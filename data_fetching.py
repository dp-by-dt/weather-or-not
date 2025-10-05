import requests
import xarray as xr
import numpy as np
from io import BytesIO
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')


class WeatherPredictor:
    """Main class for weather prediction using NASA POWER data and PCA"""
    
    def __init__(self):
        self.parameters = ["PRECTOTCORR", "T2M", "RH2M", "CLOUD_AMT", 
                          "WS10M", "ALLSKY_SFC_SW_DWN", "T2MDEW"]
        self.base_url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
        
    def fetch_power_point(self, lat, lon, start, end):
        """Fetch POWER hourly data for a given lat/lon and time range"""
        params = {
            "start": start,
            "end": end,
            "parameters": ",".join(self.parameters),
            "community": "AG",
            "latitude": lat,
            "longitude": lon,
            "format": "NetCDF"
        }
        
        try:
            resp = requests.get(self.base_url, params=params, timeout=30)
            resp.raise_for_status()
            ds = xr.open_dataset(BytesIO(resp.content))
            return ds
        except Exception as e:
            print(f"⚠️ Error fetching data: {e}")
            return None

    def fetch_multi_year_data(self, lat, lon, month, day, end_year, 
                             years_back, days_window=2, max_workers=8):
        """Fetch multi-year historical data around target date"""
        results = {}
        tasks = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for year in range(end_year - years_back + 1, end_year + 1):
                base_date = datetime(year, month, day)
                start_dt = base_date - timedelta(days=days_window)
                end_dt = base_date + timedelta(days=days_window)
                
                start_date = start_dt.strftime("%Y%m%d")
                end_date = end_dt.strftime("%Y%m%d")
                
                tasks.append((year, executor.submit(
                    self.fetch_power_point, lat, lon, start_date, end_date)))
            
            all_years_ds = []
            for year, future in tasks:
                ds = future.result()
                if ds is not None:
                    ds = ds.expand_dims(year=[year])
                    results[year] = ds
                    all_years_ds.append(ds)
        
        if all_years_ds:
            combined = xr.concat(all_years_ds, dim="year")
        else:
            combined = None
        
        return results, combined

    def prepare_daily_data(self, combined_ds, days_window):
        """Aggregate hourly data to daily averages"""
        combined_ds = combined_ds.squeeze(drop=True)
        combined_ds = combined_ds.assign_coords(
            dayofyear=("time", combined_ds.time.dt.dayofyear.data),
            hour=("time", combined_ds.time.dt.hour.data)
        )
        
        years = combined_ds['year'].values
        
        # Find common days across all years
        doys_per_year = []
        for y in years:
            ds_y = combined_ds.sel(year=int(y))
            doys_in_year = np.unique(ds_y['time.dayofyear'].values)
            doys_per_year.append(set(doys_in_year))
        
        common_doys = set.intersection(*doys_per_year)
        common_doys = np.array(sorted(common_doys))
        
        # Aggregate to daily
        daily_per_year = []
        for y in years:
            ds_y = combined_ds.sel(year=int(y))
            daily = ds_y[self.parameters].groupby('time.dayofyear').mean(dim='time')
            daily = daily.sel(dayofyear=common_doys)
            daily_exp = daily.expand_dims({'year': [int(y)]})
            daily_per_year.append(daily_exp)
        
        daily_ds = xr.concat(daily_per_year, dim='year')
        daily_ds = daily_ds.assign_coords(year=('year', years))
        
        # Convert to numpy array
        n_years = len(years)
        n_days = len(common_doys)
        n_vars = len(self.parameters)
        X_raw = np.full((n_years, n_days, n_vars), np.nan, dtype=float)
        
        for vi, v in enumerate(self.parameters):
            X_raw[:, :, vi] = daily_ds[v].values
        
        # Impute NaNs
        for vi in range(n_vars):
            var_data = X_raw[:, :, vi]
            var_mean = np.nanmean(var_data)
            X_raw[:, :, vi] = np.nan_to_num(var_data, nan=var_mean)
        
        return X_raw, common_doys, years

    def build_state_vectors(self, X_raw, days_window):
        """Build state vectors from daily data"""
        n_years, n_days, n_vars = X_raw.shape
        n_valid_days = n_days - 2 * days_window
        state_dim = (2 * days_window + 1) * n_vars
        X_state = np.zeros((n_years, n_valid_days, state_dim))
        
        for y_idx in range(n_years):
            for d_idx in range(days_window, n_days - days_window):
                window_slice = X_raw[y_idx, d_idx - days_window : d_idx + days_window + 1, :]
                X_state[y_idx, d_idx - days_window, :] = window_slice.flatten()
        
        return X_state

    def compute_weights(self, years, target_year, doys, target_doy, 
                       alpha_year=0.5, alpha_day=0.2):
        """Compute temporal and seasonal weights"""
        dist_year = np.abs(np.array(years) - target_year)
        W_year = np.exp(-alpha_year * dist_year)
        W_year = W_year / W_year.sum()
        
        dist_day = np.abs(np.array(doys) - target_doy)
        W_day = np.exp(-alpha_day * dist_day)
        W_day = W_day / W_day.sum()
        
        W_combined = np.outer(W_year, W_day)
        return W_year, W_day, W_combined

    def weighted_pca(self, X, weights, var_threshold=0.95):
        """Perform weighted PCA"""
        n_samples, n_features = X.shape
        w = weights / weights.sum()
        mu = np.average(X, axis=0, weights=w)
        Xc = X - mu
        Xc_w = Xc * w[:, None]
        Sigma = Xc.T @ Xc_w
        Sigma = 0.5 * (Sigma + Sigma.T)
        
        eigvals, eigvecs = np.linalg.eigh(Sigma)
        idx = np.argsort(eigvals)[::-1]
        eigvals = eigvals[idx]
        eigvecs = eigvecs[:, idx]
        
        total_var = np.sum(eigvals)
        explained_ratio = eigvals / (total_var + 1e-16)
        cumvar = np.cumsum(explained_ratio)
        k = int(np.searchsorted(cumvar, var_threshold) + 1)
        k = max(1, min(k, n_features))
        
        eigvals_k = eigvals[:k]
        eigvecs_k = eigvecs[:, :k]
        eps_reg = 1e-8 * total_var if total_var > 0 else 1e-8
        eigvals_k = np.maximum(eigvals_k, eps_reg)
        
        return eigvals_k, eigvecs_k, mu, k

    def generate_ensemble(self, eigvals_k, eigvecs_k, mu, n_vars, 
                         days_window, N_mc=1000):
        """Generate Monte Carlo ensemble"""
        n_components = len(eigvals_k)
        pc_std = np.sqrt(eigvals_k)
        pc_samples = np.random.normal(
            loc=0.0, scale=pc_std[None, :], size=(N_mc, n_components))
        
        X_centered_samples = pc_samples @ eigvecs_k.T
        X_samples = X_centered_samples + mu[None, :]
        
        # Extract center day
        center_slot = days_window
        start_idx = center_slot * n_vars
        end_idx = start_idx + n_vars
        center_samples = X_samples[:, start_idx:end_idx]
        
        # Apply physical constraints
        self.apply_constraints(center_samples)
        
        return center_samples

    def apply_constraints(self, samples):
        """Apply physical bounds to predictions"""
        clip_dict = {
            0: (0.0, None),      # PRECTOTCORR
            1: (-80.0, 60.0),    # T2M
            2: (0.0, 100.0),     # RH2M
            3: (0.0, 100.0),     # CLOUD_AMT
            4: (0.0, None),      # WS10M
            5: (0.0, None),      # ALLSKY_SFC_SW_DWN
            6: (-80.0, 60.0)     # T2MDEW
        }
        
        for vi, (lo, hi) in clip_dict.items():
            if lo is not None:
                samples[:, vi] = np.maximum(samples[:, vi], lo)
            if hi is not None:
                samples[:, vi] = np.minimum(samples[:, vi], hi)

    def predict(self, lat, lon, target_date, years_back=15, days_window=2, 
                N_mc=1000, random_seed=42,include_current_year=False):
        """
        Main prediction function
        
        Args:
            lat, lon: Location coordinates
            target_date: datetime object for prediction
            years_back: Years of historical data
            days_window: Days around target for state vector
            N_mc: Number of Monte Carlo samples
            random_seed: Random seed for reproducibility
            include_current_year: If True, includes target year in historical data (only use if target date has already passed)
            
        Returns:
            dict: Prediction results with statistics
        """
        np.random.seed(random_seed)
        
        target_month = target_date.month
        target_day = target_date.day
        target_year = target_date.year
        target_doy = target_date.timetuple().tm_yday
        # Determine last historical year
        if include_current_year:
            end_year = target_year
        else:
            end_year = target_year - 1  # Don't include incomplete current year
        
        print(f"Fetching historical data for {lat:.4f}°N, {lon:.4f}°E")
        print(f"Target: {target_date.strftime('%Y-%m-%d')}")
        
        # Fetch data
        _, combined_ds = self.fetch_multi_year_data(
            lat, lon, target_month, target_day, end_year, 
            years_back, days_window)
        
        if combined_ds is None:
            raise RuntimeError("Failed to fetch data")
        
        # Prepare daily data
        X_raw, common_doys, years = self.prepare_daily_data(combined_ds, days_window)
        
        # Build state vectors
        X_state = self.build_state_vectors(X_raw, days_window)
        valid_doys = common_doys[days_window : -days_window]
        
        # Compute weights
        _, _, W_combined = self.compute_weights(
            years, target_year, valid_doys, target_doy)
        
        # Weighted PCA
        X_all = X_state.reshape(-1, X_state.shape[2])
        w_all = W_combined.ravel()
        eigvals_k, eigvecs_k, mu, n_components = self.weighted_pca(X_all, w_all)
        
        print(f"Using {n_components} PCA components")
        
        # Generate ensemble
        center_samples = self.generate_ensemble(
            eigvals_k, eigvecs_k, mu, len(self.parameters), 
            days_window, N_mc)
        
        # Compute statistics
        results = {
            'metadata': {
                'location': {'lat': lat, 'lon': lon},
                'target_date': target_date.strftime('%Y-%m-%d'),
                'n_ensemble': N_mc,
                'n_components': n_components,
            },
            'predictions': {}
        }
        
        # Map to meaningful names
        var_mapping = {
            'PRECTOTCORR': 'precipitation',
            'T2M': 'temperature',
            'RH2M': 'humidity',
            'CLOUD_AMT': 'cloud_cover',
            'WS10M': 'wind_speed',
            'ALLSKY_SFC_SW_DWN': 'solar_radiation',
            'T2MDEW': 'dew_point'
        }
        
        for vi, var_name in enumerate(self.parameters):
            readable_name = var_mapping.get(var_name, var_name)
            results['predictions'][readable_name] = {
                'mean': float(np.mean(center_samples[:, vi])),
                'median': float(np.median(center_samples[:, vi])),
                'std': float(np.std(center_samples[:, vi])),
                'p5': float(np.percentile(center_samples[:, vi], 5)),
                'p95': float(np.percentile(center_samples[:, vi], 95)),
                'unit': self.get_unit(var_name)
            }
        
        # Add precipitation probability
        precip_idx = self.parameters.index('PRECTOTCORR')
        p_rain = np.mean(center_samples[:, precip_idx] > 0.1)
        results['predictions']['precipitation']['probability'] = float(p_rain)
        
        return results
    
    def get_unit(self, var_name):
        """Get unit for variable"""
        units = {
            'PRECTOTCORR': 'mm',
            'T2M': '°C',
            'RH2M': '%',
            'CLOUD_AMT': '%',
            'WS10M': 'm/s',
            'ALLSKY_SFC_SW_DWN': 'W/m²',
            'T2MDEW': '°C'
        }
        return units.get(var_name, '')


# Convenience function for easy integration
def predict_weather(lat, lon, target_date, years_back=15, N_mc=1000):
    """
    Simple wrapper function for weather prediction
    
    Args:
        lat: Latitude
        lon: Longitude
        target_date: datetime object or string 'YYYY-MM-DD'
        years_back: Years of historical data to use
        N_mc: Number of ensemble members
        
    Returns:
        dict: Prediction results
    """
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d')
    
    predictor = WeatherPredictor()
    return predictor.predict(lat, lon, target_date, years_back, N_mc=N_mc)


if __name__ == "__main__":
    # Test the predictor
    results = predict_weather(
        lat=50.0,
        lon=2.0,
        target_date=datetime(2025, 10, 5),
        years_back=15,
        N_mc=1000
    )
    
    print("\n=== Prediction Results ===")
    for var, stats in results['predictions'].items():
        print(f"\n{var.upper()}:")
        print(f"  Mean: {stats['mean']:.2f} {stats['unit']}")
        print(f"  Range: [{stats['p5']:.2f}, {stats['p95']:.2f}] {stats['unit']}")
        if 'probability' in stats:
            print(f"  Probability: {stats['probability']:.1%}")