import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import json
import requests
from streamlit_lottie import st_lottie

# Import backend
from data_fetching import predict_weather
from weather_predictor import classify_weather, generate_description
from card_generator import WeatherCardGenerator

# Page config
st.set_page_config(
    page_title="Weather or Not",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'persona' not in st.session_state:
    st.session_state.persona = 'balanced'
if 'location' not in st.session_state:
    st.session_state.location = None
if 'predictions' not in st.session_state:
    st.session_state.predictions = None
if 'raw_backend_data' not in st.session_state:
    st.session_state.raw_backend_data = None
if 'years_back' not in st.session_state:
    st.session_state.years_back = 15
if 'n_ensemble' not in st.session_state:
    st.session_state.n_ensemble = 1000
if 'easter_egg_found' not in st.session_state:
    st.session_state.easter_egg_found = False
if 'character_clicks' not in st.session_state:
    st.session_state.character_clicks = 0
if 'card_generated' not in st.session_state:
    st.session_state.card_generated = False
if 'card_image' not in st.session_state:
    st.session_state.card_image = None

# Persona configurations
PERSONAS = {
    'sun_lover': {
        'icon': '☀️',
        'name': 'Sun Lover',
        'theme': {'primary': '#FFB74D', 'secondary': '#FFF3E0', 'accent': '#F57C00'},
        'character': '🌻',
        'greeting': 'Chasing sunshine!'
    },
    'rain_enjoyer': {
        'icon': '🌧️',
        'name': 'Rain Enjoyer',
        'theme': {'primary': '#64B5F6', 'secondary': '#E3F2FD', 'accent': '#1976D2'},
        'character': '🐸',
        'greeting': 'Loving those raindrops!'
    },
    'snow_enthusiast': {
        'icon': '❄️',
        'name': 'Snow Enthusiast',
        'theme': {'primary': '#90CAF9', 'secondary': '#E1F5FE', 'accent': '#0277BD'},
        'character': '⛷️',
        'greeting': 'Winter wonderland vibes!'
    },
    'balanced': {
        'icon': '🌤️',
        'name': 'Weather Neutral',
        'theme': {'primary': '#81C784', 'secondary': '#F1F8E9', 'accent': '#388E3C'},
        'character': '🦋',
        'greeting': 'Every weather is beautiful!'
    }
}

# Dynamic character states based on weather
WEATHER_CHARACTERS = {
    'sunny': {'char': '🦋', 'state': 'flying joyfully'},
    'clear': {'char': '🦋', 'state': 'basking in sunshine'},
    'partly_cloudy': {'char': '🐝', 'state': 'buzzing around'},
    'cloudy': {'char': '🐌', 'state': 'slowly moving'},
    'rainy': {'char': '🐸', 'state': 'dancing in puddles'},
    'light_rain': {'char': '🦆', 'state': 'enjoying the drizzle'},
    'heavy_rain': {'char': '🦆', 'state': 'splashing around'},
    'stormy': {'char': '🦉', 'state': 'seeking shelter'},
    'snowy': {'char': '🐧', 'state': 'sliding on ice'},
    'foggy': {'char': '👻', 'state': 'mysteriously floating'},
    'windy': {'char': '🍃', 'state': 'being blown around'},
    'hot': {'char': '🦎', 'state': 'sunbathing'},
    'cold': {'char': '🐻', 'state': 'hibernating mode'}
}

# Custom CSS based on persona
def get_custom_css(persona):
    theme = PERSONAS[persona]['theme']
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    * {{
        font-family: 'Outfit', sans-serif;
    }}
    
    .stApp {{
        background: linear-gradient(135deg, {theme['secondary']} 0%, #ffffff 100%);
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .main-header {{
        text-align: center;
        padding: 2rem 0;
        animation: fadeIn 1s ease-in;
    }}
    
    .main-title {{
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['accent']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }}
    
    .subtitle {{
        font-size: 1.2rem;
        color: #666;
        font-weight: 300;
    }}
    
    .input-card {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        margin: 2rem 0;
        animation: slideUp 0.6s ease-out;
    }}
    
    .weather-display {{
        background: linear-gradient(135deg, {theme['primary']}20 0%, white 100%);
        border-radius: 24px;
        padding: 2.5rem;
        margin: 2rem 0;
        box-shadow: 0 12px 32px rgba(0,0,0,0.1);
        border: 1px solid {theme['primary']}40;
        animation: fadeIn 0.8s ease-in;
    }}
    
    .temp-display {{
        font-size: 5rem;
        font-weight: 700;
        color: {theme['accent']};
    }}
    
    .weather-icon {{
        font-size: 6rem;
    }}
    
    .weather-description {{
        font-size: 1.3rem;
        color: #555;
        line-height: 1.8;
        margin: 1.5rem 0;
    }}
    
    .weather-params {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }}
    
    .param-card {{
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }}
    
    .param-card:hover {{
        transform: translateY(-5px);
    }}
    
    .param-icon {{
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }}
    
    .param-value {{
        font-size: 2rem;
        font-weight: 600;
        color: {theme['accent']};
    }}
    
    .param-label {{
        font-size: 0.9rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .floating-character {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        font-size: 4rem;
        animation: float 3s ease-in-out infinite;
        cursor: pointer;
        z-index: 999;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
        transition: transform 0.3s ease;
        user-select: none;
    }}
    
    .floating-character:hover {{
        transform: scale(1.2) rotate(10deg);
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-20px); }}
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    
    @keyframes slideUp {{
        from {{ 
            opacity: 0;
            transform: translateY(30px);
        }}
        to {{ 
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['accent']} 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.8rem 2.5rem !important;
        border-radius: 25px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px {theme['primary']}40 !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px {theme['primary']}60 !important;
    }}
    
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['accent']} 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.8rem 2.5rem !important;
        border-radius: 25px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px {theme['primary']}40 !important;
    }}
    
    .stDownloadButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px {theme['primary']}60 !important;
    }}
    
    .stMarkdown, .stText, p, span, div {{
        color: #333 !important;
    }}
    
    label {{
        color: #444 !important;
        font-weight: 500 !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 5px;
        gap: 5px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: #555 !important;
        font-weight: 500;
        border-radius: 8px;
        padding: 8px 16px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {theme['primary']} !important;
        color: white !important;
    }}
    
    /* Fix all input fields */
    input, select, textarea, 
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {{
        color: #333 !important;
        background-color: white !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
    }}

    .stSelectbox > div > div > div[role="listbox"] {{
        background-color: white !important;
        color: #333 !important;
    }}
    
    /* Selectbox styling */
    .stSelectbox > div > div {{
        background-color: white !important;
    }}
    
    .stSelectbox [data-baseweb="select"] {{
        background-color: white !important;
    }}
    
    /* Make leaflet attribution transparent */
    .leaflet-control-attribution {{
        opacity: 0.3 !important;
        font-size: 9px !important;
        background-color: rgba(255, 255, 255, 0.4) !important;
    }}
    
    .leaflet-control-attribution:hover {{
        opacity: 0.7 !important;
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {theme['secondary']} 0%, #ffffff 100%);
    }}
    
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        margin: 5px 0;
    }}
    
    /* Easter egg hint */
    .easter-egg-hint {{
        position: fixed;
        top: 10px;
        right: 10px;
        font-size: 0.7rem;
        color: rgba(150, 150, 150, 0.3);
        z-index: 1000;
        cursor: help;
        padding: 5px 10px;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 10px;
    }}
    
    @media (max-width: 768px) {{
        .main-title {{
            font-size: 2.5rem;
        }}
        .temp-display {{
            font-size: 3.5rem;
        }}
        .weather-icon {{
            font-size: 4rem;
        }}
        .weather-params {{
            grid-template-columns: 1fr;
        }}
        .floating-character {{
            font-size: 3rem;
            bottom: 20px;
            right: 20px;
        }}
    }}
    </style>
    """

# Helper functions
def get_weather_icon(classification):
    """Map weather classification to emoji icon"""
    icon_map = {
        'sunny': '☀️', 'clear': '☀️', 'partly_cloudy': '⛅',
        'cloudy': '☁️', 'overcast': '☁️', 'rainy': '🌧️',
        'light_rain': '🌦️', 'heavy_rain': '🌧️', 'stormy': '⛈️',
        'thunderstorm': '⛈️', 'snowy': '❄️', 'light_snow': '🌨️',
        'heavy_snow': '❄️', 'foggy': '🌫️', 'windy': '💨',
        'hot': '🔥', 'cold': '🥶'
    }
    return icon_map.get(classification.lower(), '🌤️')

def get_dynamic_character(condition):
    """Get weather-appropriate character"""
    for key in WEATHER_CHARACTERS:
        if key in condition.lower():
            return WEATHER_CHARACTERS[key]
    return WEATHER_CHARACTERS.get('clear', {'char': '🦋', 'state': 'floating peacefully'})

def transform_backend_data(backend_results, target_date, target_time, location):
    """Transform backend prediction results to frontend format"""
    pred = backend_results['predictions']
    
    # Call weather_rules to get classification and description
    weather_class, weather_desc = classify_weather(pred)
    weather_desc_full = generate_description(pred, weather_class, PERSONAS[st.session_state.persona]['name'])
    
    # Transform to frontend format
    transformed = {
        'temperature': pred['temperature']['mean'],
        'temp_min': pred['temperature']['p5'],
        'temp_max': pred['temperature']['p95'],
        'feels_like': pred['dew_point']['mean'],
        'humidity': pred['humidity']['mean'],
        'wind_speed': pred['wind_speed']['mean'],
        'pressure': 1013,
        'precipitation': pred['precipitation']['mean'],
        'precipitation_prob': pred['precipitation']['probability'] * 100,
        'cloud_cover': pred['cloud_cover']['mean'],
        'solar_radiation': pred['solar_radiation']['mean'],
        'dew_point': pred['dew_point']['mean'],
        'visibility': 10,
        'uv_index': min(11, max(0, int(pred['solar_radiation']['mean'] / 80))),
        'condition': weather_class,
        'condition_text': weather_class.replace('_', ' ').title(),
        'description': weather_desc_full,
        'location': location,
        'date': target_date,
        'time': target_time,
        'metadata': backend_results['metadata']
    }
    
    return transformed

def format_time_12hr(time_24):
    """Convert 24hr time input to 12hr format with AM/PM"""
    return time_24.strftime('%I:%M %p')


def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_spinner = load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_usmfx6bp.json")  # spinner



# Easter egg hint (subtle)
# Easter egg hint (subtle)
st.markdown("""
<div id="easter_hint" class="easter-egg-hint" title="Try clicking me 5 times!">✨</div>
<script>
const hint = document.getElementById("easter_hint");
let count = 0;
hint.addEventListener("click", () => {
    count++;
    if (count >= 5) {
        window.parent.postMessage({isEasterEgg:true}, "*");
    }
});
</script>
""", unsafe_allow_html=True)


# if st.button("✨"):
#     st.session_state.character_clicks += 5
#     st.session_state.easter_egg_found = True
#     st.snow()



# Floating character with weather awareness
if st.session_state.predictions:
    weather_char = get_dynamic_character(st.session_state.predictions['condition'])
    character = weather_char['char']
    char_state = weather_char['state']
else:
    character = PERSONAS[st.session_state.persona]['character']
    char_state = PERSONAS[st.session_state.persona]['greeting']

st.markdown(f'<div class="floating-character" title="{char_state}">{character}</div>', unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="main-header">
    <div class="main-title">Weather or Not</div>
    <div class="subtitle">Predict the future, plan your present</div>
</div>
""", unsafe_allow_html=True)

# Persona selector in sidebar
with st.sidebar:
    st.markdown("<div style='overflow-y:auto; height:90vh;'>", unsafe_allow_html=True)
    st.title("Settings & Persona")
    st.markdown("### 🎭 Choose Your Weather Persona")
    st.markdown("---")
    
    for key, persona in PERSONAS.items():
        is_active = st.session_state.persona == key
        button_type = "primary" if is_active else "secondary"
        
        if st.button(
            f"{persona['icon']} {persona['name']}", 
            key=f"persona_{key}",
            use_container_width=True
        ):
            st.session_state.persona = key
            st.rerun()
    
    st.markdown("---")
    st.success(f"**Active:** {PERSONAS[st.session_state.persona]['icon']} {PERSONAS[st.session_state.persona]['name']}")
    
    st.markdown("---")
    st.markdown("### ⚙️ Advanced Settings")
    st.session_state.years_back = st.slider("Years of historical data", 5, 20, st.session_state.years_back)
    st.session_state.n_ensemble = st.slider("Ensemble members", 100, 2000, st.session_state.n_ensemble, step=100)
    
    # Easter egg tracker
    st.markdown("---")
    if st.button("🎯 Click the hint 5 times!", use_container_width=True, key="easter_trigger"):
        st.session_state.character_clicks += 1
        if st.session_state.character_clicks >= 5 and not st.session_state.easter_egg_found:
            st.session_state.easter_egg_found = True
            st.balloons()
            st.success("🎉 You found the secret! You're a weather explorer!")
    
    if st.session_state.easter_egg_found:
        st.markdown("### 🌟 Achievement Unlocked!")
        st.markdown("**Weather Explorer Badge**")
        st.markdown("*You discovered the hidden feature!*")
    st.markdown("</div>", unsafe_allow_html=True)


# Inject custom CSS
st.markdown(get_custom_css(st.session_state.persona), unsafe_allow_html=True)

# Main content
st.markdown('<div class="input-card">', unsafe_allow_html=True)
st.markdown("### 📍 Where and When?")

# Location input tabs
location_tab1, location_tab2 = st.tabs(["🗺️ Map Selection", "📌 Coordinates"])

with location_tab1:
    st.markdown("**Click on the map to select a location**")
    
    # Create folium map
    m = folium.Map(
        location=[20.5937, 78.9629],
        zoom_start=5,
        tiles='OpenStreetMap'
    )
    m.add_child(folium.LatLngPopup())
    
    # Display map with proper sizing
    map_data = st_folium(m, width=None, height=400, returned_objects=["last_clicked"])
    
    if map_data and map_data.get('last_clicked'):
        lat = map_data['last_clicked']['lat']
        lon = map_data['last_clicked']['lng']
        st.session_state.location = {'lat': lat, 'lon': lon, 'method': 'map'}
        st.success(f"📍 Selected: {lat:.4f}°N, {lon:.4f}°E")

with location_tab2:
    st.markdown("**Enter coordinates manually**")
    col1, col2 = st.columns(2)
    with col1:
        lat_input = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=20.5937, step=0.1, format="%.4f")
    with col2:
        lon_input = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=78.9629, step=0.1, format="%.4f")
    
    if st.button("📍 Use These Coordinates", use_container_width=True):
        st.session_state.location = {'lat': lat_input, 'lon': lon_input, 'method': 'coords'}
        st.success(f"📍 Location set: {lat_input:.4f}°N, {lon_input:.4f}°E")

# Date and time selection
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    target_date = st.date_input(
        "📅 Select Date",
        min_value=datetime.now().date(),
        max_value=datetime.now().date() + timedelta(days=365),
        value=datetime.now().date() + timedelta(days=1)
    )

with col2:
    #st.markdown("🕐 Select time")
    
    # Simple hour and AM/PM selector
    hour_col, ampm_col = st.columns([3, 1])
    with hour_col:
        hour_12 = st.selectbox("🕐 Select Time", list(range(1, 13)), index=11, key="hour_select")
    with ampm_col:
        ampm = st.selectbox("", ["AM", "PM"], index=0 if datetime.now().hour < 12 else 1, key="ampm_select")
    
    # Convert to 24hr format
    if ampm == "PM" and hour_12 != 12:
        hour_24 = hour_12 + 12
    elif ampm == "AM" and hour_12 == 12:
        hour_24 = 0
    else:
        hour_24 = hour_12
    
    target_time = datetime.strptime(f"{hour_24}:00", "%H:%M").time()
    st.caption(f"Selected: {format_time_12hr(target_time)}")

st.markdown('</div>', unsafe_allow_html=True)

# Predict button
if st.session_state.location:
    if st.button("🔮 Predict Weather", use_container_width=True):
        with st.empty():
            try:
                st_lottie(lottie_spinner, height=150, key="loading_spinner")
                # Create datetime object
                target_datetime = datetime.combine(target_date, target_time)
                
                # Call the backend
                backend_results = predict_weather(
                    lat=st.session_state.location['lat'],
                    lon=st.session_state.location['lon'],
                    target_date=target_datetime,
                    years_back=st.session_state.years_back,
                    N_mc=st.session_state.n_ensemble
                )
                
                # Store raw backend data
                st.session_state.raw_backend_data = backend_results
                
                # Transform to frontend format
                st.session_state.predictions = transform_backend_data(
                    backend_results, 
                    target_date, 
                    target_time, 
                    st.session_state.location
                )
                
                # Reset card generation state
                st.session_state.card_generated = False
                st.session_state.card_image = None
                
                st.success("✅ Prediction complete!")
                
            except Exception as e:
                st.error(f"❌ Prediction failed: {str(e)}")
                st.info("Please check your location and date, then try again.")
                import traceback
                with st.expander("🔍 Error Details"):
                    st.code(traceback.format_exc())
else:
    st.info("👆 Please select a location first!")

# Display predictions
if st.session_state.predictions:
    pred = st.session_state.predictions
    
    st.markdown('<div class="weather-display">', unsafe_allow_html=True)
    
    # Main weather display
    col1, col2 = st.columns([1, 2])
    
    with col1:
        icon = get_weather_icon(pred['condition'])
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="weather-icon">{icon}</div>
            <div class="temp-display">{pred['temperature']:.1f}°C</div>
            <div style="font-size: 1.2rem; color: #888;">Feels like {pred['feels_like']:.1f}°C</div>
            <div style="font-size: 0.9rem; color: #aaa; margin-top: 0.5rem;">
                Range: {pred['temp_min']:.1f}°C - {pred['temp_max']:.1f}°C
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"### {pred['condition_text']}")
        st.markdown(f"**📅 {pred['date'].strftime('%A, %B %d, %Y')}** at **🕐 {format_time_12hr(pred['time'])}**")
        st.markdown(f"**📍 Location:** {pred['location']['lat']:.4f}°N, {pred['location']['lon']:.4f}°E")
        
        # Personalized description
        st.markdown(f'<div class="weather-description">{pred["description"]}</div>', unsafe_allow_html=True)
    
    # Weather parameters grid
    st.markdown('<div class="weather-params">', unsafe_allow_html=True)
    
    params = [
        {'icon': '💧', 'label': 'Humidity', 'value': f"{pred['humidity']:.1f}%"},
        {'icon': '💨', 'label': 'Wind Speed', 'value': f"{pred['wind_speed']:.1f} m/s"},
        {'icon': '🌧️', 'label': 'Precipitation', 'value': f"{pred['precipitation']:.1f} mm"},
        {'icon': '☔', 'label': 'Rain Probability', 'value': f"{pred['precipitation_prob']:.0f}%"},
        {'icon': '☁️', 'label': 'Cloud Cover', 'value': f"{pred['cloud_cover']:.1f}%"},
        {'icon': '☀️', 'label': 'Solar Radiation', 'value': f"{pred['solar_radiation']:.0f} W/m²"},
    ]
    
    cols = st.columns(3)
    for idx, param in enumerate(params):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="param-card">
                <div class="param-icon">{param['icon']}</div>
                <div class="param-value">{param['value']}</div>
                <div class="param-label">{param['label']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show detailed statistics in expander
    with st.expander("📊 View Detailed Statistics"):
        if st.session_state.raw_backend_data:
            raw_pred = st.session_state.raw_backend_data['predictions']
            
            for var, stats in raw_pred.items():
                st.markdown(f"**{var.replace('_', ' ').title()}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Mean", f"{stats['mean']:.2f} {stats['unit']}")
                with col2:
                    st.metric("Median", f"{stats['median']:.2f} {stats['unit']}")
                with col3:
                    st.metric("5th %ile", f"{stats['p5']:.2f} {stats['unit']}")
                with col4:
                    st.metric("95th %ile", f"{stats['p95']:.2f} {stats['unit']}")
                st.markdown("---")
    
    # Download options
    st.markdown("---")
    st.markdown("### 💾 Save Your Forecast")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # CSV download
        df = pd.DataFrame([pred])
        csv = df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name=f"weather_forecast_{target_date}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # JSON download
        json_str = json.dumps(pred, default=str, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name=f"weather_forecast_{target_date}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        # Raw backend data download
        if st.session_state.raw_backend_data:
            raw_json = json.dumps(st.session_state.raw_backend_data, default=str, indent=2)
            st.download_button(
                label="🔬 Download Raw Data",
                data=raw_json,
                file_name=f"weather_raw_{target_date}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col4:
        # Weather card download
        if st.button("🎨 Generate Weather Card", use_container_width=True):
            with st.spinner("Creating your beautiful weather card..."):
                try:
                    # Generate the card
                    generator = WeatherCardGenerator()
                    card_image = generator.generate_card(
                        weather_data=pred,
                        persona=st.session_state.persona,
                        include_quote=True
                    )
                    
                    # Convert to bytes
                    card_bytes = generator.card_to_bytes(card_image)
                    
                    # Create download button
                    st.download_button(
                        label="💾 Download Card",
                        data=card_bytes,
                        file_name=f"weather_card_{target_date}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                    
                    # Show preview
                    st.image(card_image, caption="Your Weather Card Preview", use_container_width=True)
                    st.success("✅ Weather card generated!")
                    
                except Exception as e:
                    st.error(f"Failed to generate card: {str(e)}")

                    st.info("The card generator requires PIL/Pillow library.")




