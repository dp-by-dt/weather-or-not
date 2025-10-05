"""
Weather classification and description generation based on predicted parameters
"""

def classify_weather(predictions):
    """
    Classify weather based on predicted parameters
    
    Args:
        predictions: Dictionary of weather predictions with keys:
            - temperature: dict with 'mean', 'p5', 'p95', etc.
            - precipitation: dict with 'mean', 'probability', etc.
            - cloud_cover: dict with 'mean'
            - wind_speed: dict with 'mean'
            - humidity: dict with 'mean'
    
    Returns:
        tuple: (classification_string, short_description)
    """
    
    # Extract mean values
    temp = predictions['temperature']['mean']
    precip = predictions['precipitation']['mean']
    precip_prob = predictions['precipitation'].get('probability', 0)
    clouds = predictions['cloud_cover']['mean']
    wind = predictions['wind_speed']['mean']
    humidity = predictions['humidity']['mean']
    
    # Classification logic
    classification = ""
    short_desc = ""
    
    # Temperature categories
    temp_category = ""
    if temp < 0:
        temp_category = "freezing"
    elif temp < 10:
        temp_category = "cold"
    elif temp < 20:
        temp_category = "cool"
    elif temp < 28:
        temp_category = "comfortable"
    elif temp < 35:
        temp_category = "warm"
    else:
        temp_category = "hot"
    
    # Primary weather determination
    if precip > 5 and precip_prob > 0.5:
        if temp < 0:
            classification = "snowy"
            short_desc = "Expect snowfall"
        elif precip > 20:
            classification = "heavy_rain"
            short_desc = "Heavy rainfall expected"
        else:
            classification = "rainy"
            short_desc = "Rainy conditions"
    
    elif precip > 0.5 and precip_prob > 0.3:
        classification = "light_rain"
        short_desc = "Light rain possible"
    
    elif clouds > 80:
        classification = "overcast"
        short_desc = "Overcast skies"
    
    elif clouds > 50:
        classification = "cloudy"
        short_desc = "Mostly cloudy"
    
    elif clouds > 20:
        classification = "partly_cloudy"
        short_desc = "Partly cloudy"
    
    else:
        if temp > 30:
            classification = "hot"
            short_desc = "Hot and sunny"
        else:
            classification = "clear"
            short_desc = "Clear skies"
    
    # Wind modifier
    if wind > 15:
        classification = f"windy_{classification}"
        short_desc = f"Windy with {short_desc.lower()}"
    
    # Special conditions
    if humidity > 85 and temp > 25:
        short_desc += " and humid"
    elif humidity < 30:
        short_desc += " and dry"
    
    return classification, short_desc


def generate_description(predictions, classification, persona="Weather Neutral"):
    """
    Generate a detailed, personalized weather description
    
    Args:
        predictions: Dictionary of weather predictions
        classification: Weather classification string
        persona: User's weather persona
    
    Returns:
        str: Detailed weather description
    """
    
    # Extract values
    temp = predictions['temperature']['mean']
    temp_min = predictions['temperature']['p5']
    temp_max = predictions['temperature']['p95']
    precip = predictions['precipitation']['mean']
    precip_prob = predictions['precipitation'].get('probability', 0)
    clouds = predictions['cloud_cover']['mean']
    wind = predictions['wind_speed']['mean']
    humidity = predictions['humidity']['mean']
    
    # Build description components
    description_parts = []
    
    # Opening statement based on classification
    if "rain" in classification:
        if persona == "Rain Enjoyer":
            description_parts.append("Perfect! Rain is on the way.")
        else:
            description_parts.append("Rain is expected today.")
    elif "snow" in classification:
        if persona == "Snow Enthusiast":
            description_parts.append("Exciting news - snowfall ahead!")
        else:
            description_parts.append("Snowy conditions expected.")
    elif "clear" in classification or "sunny" in classification:
        if persona == "Sun Lover":
            description_parts.append("Great news! Sunny skies ahead!")
        else:
            description_parts.append("Clear skies are expected.")
    else:
        description_parts.append("Mixed weather conditions today.")
    
    # Temperature details
    temp_desc = f"Temperatures will be around {temp:.1f}°C"
    if temp_max - temp_min > 5:
        temp_desc += f", with variations between {temp_min:.1f}°C and {temp_max:.1f}°C"
    temp_desc += "."
    description_parts.append(temp_desc)
    
    # Comfort level
    if temp < 10:
        description_parts.append("Dress warmly - it'll be quite chilly.")
    elif temp > 30:
        description_parts.append("Stay hydrated and seek shade - it'll be quite hot.")
    elif 20 <= temp <= 25:
        description_parts.append("Very comfortable temperatures - perfect for any outdoor activities.")
    
    # Precipitation details
    if precip > 0.5:
        rain_desc = f"Expect about {precip:.1f}mm of precipitation"
        if precip_prob > 0.7:
            rain_desc += f" (probability: {precip_prob*100:.0f}%)"
        rain_desc += ". "
        
        if precip < 2:
            rain_desc += "Just a light drizzle, really."
        elif precip < 10:
            rain_desc += "Moderate rainfall - an umbrella would be wise."
        else:
            rain_desc += "Heavy rain expected - plan accordingly."
        
        description_parts.append(rain_desc)
    elif precip_prob > 0.3:
        description_parts.append(f"There's a {precip_prob*100:.0f}% chance of some rain.")
    
    # Cloud coverage
    if clouds < 20:
        description_parts.append("Mostly clear skies throughout the day.")
    elif clouds < 50:
        description_parts.append("Some clouds, but plenty of sunshine too.")
    elif clouds < 80:
        description_parts.append("Mostly cloudy conditions expected.")
    else:
        description_parts.append("Overcast skies with little sunshine.")
    
    # Wind conditions
    if wind > 20:
        description_parts.append(f"Strong winds at {wind:.1f} m/s - secure loose objects.")
    elif wind > 10:
        description_parts.append(f"Moderate winds at {wind:.1f} m/s - a bit breezy.")
    elif wind < 3:
        description_parts.append("Very calm conditions with minimal wind.")
    
    # Humidity
    if humidity > 80:
        description_parts.append("High humidity will make it feel muggy.")
    elif humidity < 30:
        description_parts.append("Low humidity - quite dry conditions.")
    
    # Activity recommendations based on persona
    if persona == "Sun Lover":
        if "clear" in classification or "sunny" in classification:
            description_parts.append("Perfect day for soaking up some sunshine! ☀️")
        elif "rain" in classification:
            description_parts.append("Not your favorite weather, but indoor activities can be fun too.")
    
    elif persona == "Rain Enjoyer":
        if "rain" in classification:
            description_parts.append("Ideal weather for a cozy day with the sound of rain! 🌧️")
        elif "clear" in classification:
            description_parts.append("Bright and dry - maybe find some indoor activities.")
    
    elif persona == "Snow Enthusiast":
        if "snow" in classification:
            description_parts.append("Perfect for winter activities! ⛷️")
        elif temp > 25:
            description_parts.append("Quite warm - not your preferred weather, but still enjoyable.")
    
    else:  # Balanced
        if precip < 1 and 18 <= temp <= 28:
            description_parts.append("Great weather for any outdoor plans you might have.")
        elif "rain" in classification:
            description_parts.append("Indoor activities recommended, or embrace the rain with proper gear.")
    
    # Closing advice
    if wind > 15 or precip > 10:
        description_parts.append("Stay safe and plan your activities accordingly.")
    
    return " ".join(description_parts)


def get_weather_emoji(classification):
    """
    Get appropriate emoji for weather classification
    
    Args:
        classification: Weather classification string
    
    Returns:
        str: Emoji representation
    """
    emoji_map = {
        'clear': '☀️',
        'sunny': '☀️',
        'partly_cloudy': '⛅',
        'cloudy': '☁️',
        'overcast': '☁️',
        'light_rain': '🌦️',
        'rainy': '🌧️',
        'heavy_rain': '🌧️',
        'thunderstorm': '⛈️',
        'snowy': '❄️',
        'light_snow': '🌨️',
        'heavy_snow': '❄️',
        'foggy': '🌫️',
        'windy': '💨',
        'hot': '🔥',
        'cold': '🥶'
    }
    
    # Check for compound classifications (e.g., 'windy_rainy')
    for key in emoji_map:
        if key in classification:
            return emoji_map[key]
    
    return '🌤️'  # Default


def get_activity_suggestions(predictions, classification):
    """
    Suggest activities based on weather conditions
    
    Args:
        predictions: Dictionary of weather predictions
        classification: Weather classification string
    
    Returns:
        list: List of activity suggestions
    """
    temp = predictions['temperature']['mean']
    precip = predictions['precipitation']['mean']
    wind = predictions['wind_speed']['mean']
    
    suggestions = []
    
    if precip < 1 and 18 <= temp <= 28 and wind < 10:
        suggestions.extend([
            "🚶 Perfect for a walk or jog",
            "🚴 Great cycling weather",
            "🧺 Ideal for a picnic"
        ])
    
    elif precip < 1 and temp > 28:
        suggestions.extend([
            "🏊 Swimming or water activities",
            "🌳 Seek shade for outdoor activities",
            "🍦 Great weather for ice cream!"
        ])
    
    elif precip < 1 and temp < 15:
        suggestions.extend([
            "🥾 Hiking with warm clothing",
            "☕ Outdoor coffee with a jacket",
            "📸 Photography in crisp air"
        ])
    
    elif "rain" in classification:
        suggestions.extend([
            "📚 Perfect reading weather",
            "🎬 Movie marathon day",
            "🍲 Cook your favorite comfort food",
            "☂️ Puddle jumping for the adventurous!"
        ])
    
    elif "snow" in classification:
        suggestions.extend([
            "⛷️ Skiing or snowboarding",
            "⛸️ Ice skating",
            "☃️ Build a snowman",
            "🔥 Cozy up by the fireplace"
        ])
    
    elif "windy" in classification:
        suggestions.extend([
            "🪁 Kite flying",
            "🏠 Indoor activities recommended",
            "🌳 Avoid tall trees and structures"
        ])
    
    if not suggestions:
        suggestions.append("🏠 Indoor activities recommended")
    
    return suggestions


def get_clothing_recommendations(predictions, classification):
    """
    Recommend clothing based on weather conditions
    
    Args:
        predictions: Dictionary of weather predictions
        classification: Weather classification string
    
    Returns:
        list: List of clothing recommendations
    """
    temp = predictions['temperature']['mean']
    precip = predictions['precipitation']['mean']
    wind = predictions['wind_speed']['mean']
    
    recommendations = []
    
    # Base layer
    if temp < 10:
        recommendations.append("🧥 Heavy jacket or coat")
        recommendations.append("🧣 Scarf and gloves")
    elif temp < 18:
        recommendations.append("🧥 Light jacket or sweater")
    elif temp < 28:
        recommendations.append("👕 T-shirt or light shirt")
    else:
        recommendations.append("👕 Light, breathable clothing")
        recommendations.append("🧢 Hat for sun protection")
    
    # Rain gear
    if precip > 1:
        recommendations.append("☂️ Umbrella or raincoat")
        if precip > 10:
            recommendations.append("👢 Waterproof footwear")
    
    # Wind protection
    if wind > 10:
        recommendations.append("🧥 Windbreaker recommended")
    
    # Sun protection
    if "clear" in classification or "sunny" in classification:
        recommendations.append("🕶️ Sunglasses")
        recommendations.append("🧴 Sunscreen")
    
    return recommendations


# Example usage
if __name__ == "__main__":
    # Test with sample predictions
    sample_predictions = {
        'temperature': {'mean': 25.5, 'p5': 23.0, 'p95': 28.0},
        'precipitation': {'mean': 2.5, 'probability': 0.6},
        'cloud_cover': {'mean': 60.0},
        'wind_speed': {'mean': 8.5},
        'humidity': {'mean': 70.0}
    }
    
    classification, short_desc = classify_weather(sample_predictions)
    print(f"Classification: {classification}")
    print(f"Short Description: {short_desc}")
    print(f"\nDetailed Description:")
    print(generate_description(sample_predictions, classification, "Sun Lover"))
    print(f"\nEmoji: {get_weather_emoji(classification)}")
    print(f"\nActivity Suggestions:")
    for suggestion in get_activity_suggestions(sample_predictions, classification):
        print(f"  {suggestion}")
    print(f"\nClothing Recommendations:")
    for rec in get_clothing_recommendations(sample_predictions, classification):
        print(f"  {rec}")