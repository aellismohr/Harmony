import math
import numpy as np
import random
from datetime import datetime

def get_variare_temperature(lat, lon, day_of_year, hour=12, minute=0, elevation=0):
    """
    Calculate temperature for a planet with 90-degree axial tilt at Earth's distance from Sun.
    
    Parameters:
    -----------
    lat : float
        Latitude in degrees (-90 to 90)
    lon : float
        Longitude in degrees (-180 to 180)
    day_of_year : int
        Day of year (1-365)
    hour : int
        Hour of day (0-23)
    minute : int
        Minute of hour (0-59)
    elevation : float
        Elevation in meters
    
    Returns:
    --------
    dict
        Temperature and weather information
    """
    # Constants
    DAYS_IN_YEAR = 360
    
    # Season reference points
    SPRING_EQUINOX = 0
    SUMMER_SOLSTICE = 90
    FALL_EQUINOX = 180
    WINTER_SOLSTICE = 270
    
    # Temperature extremes (in Celsius)
    MAX_DIRECT_SUNLIGHT_TEMP = 75  # Max temperature with direct constant sunlight
    MIN_DARKNESS_TEMP = -85        # Min temperature with no sunlight
    
    # Calculate season based on day of year
    normalized_day = day_of_year / DAYS_IN_YEAR
    year_angle = normalized_day * 2 * math.pi
    
    # Solar declination on 90° tilted planet (-90 to 90 degrees)
    solar_declination = 90 * math.sin(year_angle)
    
    # Determine base temperatures using the hard-coded model
    # Define location category
    if abs(lat) > 75:
        if lat > 0:
            location = "northPole"
        else:
            location = "southPole"
    elif abs(lat) > 30:
        if lat > 0:
            location = "northMid"
        else:
            location = "southMid"
    else:
        location = "equator"
    
    # Determine season category and interpolation factor
    if day_of_year < SPRING_EQUINOX:
        # Between winter solstice and spring equinox
        season1 = "winter"
        season2 = "springEquinox"
        factor = (day_of_year - WINTER_SOLSTICE) / (SPRING_EQUINOX - WINTER_SOLSTICE)
        if factor < 0:  # Handle wraparound from previous year
            factor = (day_of_year + (DAYS_IN_YEAR - WINTER_SOLSTICE)) / (SPRING_EQUINOX - WINTER_SOLSTICE + DAYS_IN_YEAR)
        season_name = "Late Winter/Early Spring"
    elif day_of_year < SUMMER_SOLSTICE:
        # Between spring equinox and summer solstice
        season1 = "springEquinox"
        season2 = "summer"
        factor = (day_of_year - SPRING_EQUINOX) / (SUMMER_SOLSTICE - SPRING_EQUINOX)
        season_name = "Late Spring/Early Summer"
    elif day_of_year < FALL_EQUINOX:
        # Between summer solstice and fall equinox
        season1 = "summer"
        season2 = "fallEquinox"
        factor = (day_of_year - SUMMER_SOLSTICE) / (FALL_EQUINOX - SUMMER_SOLSTICE)
        season_name = "Late Summer/Early Fall"
    elif day_of_year < WINTER_SOLSTICE:
        # Between fall equinox and winter solstice
        season1 = "fallEquinox"
        season2 = "winter"
        factor = (day_of_year - FALL_EQUINOX) / (WINTER_SOLSTICE - FALL_EQUINOX)
        season_name = "Late Fall/Early Winter"
    else:
        # Between winter solstice and end of year (wrapping to spring equinox)
        season1 = "winter"
        season2 = "springEquinox"
        factor = (day_of_year - WINTER_SOLSTICE) / ((DAYS_IN_YEAR - WINTER_SOLSTICE) + SPRING_EQUINOX)
        season_name = "Early/Mid Winter"
    
    # Hard-coded temperature values for key points
    temps = {
        # North Pole temperatures by season
        "northPole": {
            "summer": 75,       # Direct sunlight baking the pole
            "fallEquinox": 20,  # Transitioning to darkness
            "winter": -85,      # Complete darkness, extremely cold
            "springEquinox": -20 # Beginning to warm up
        },
        
        # South Pole temperatures (opposite of North Pole)
        "southPole": {
            "summer": -85,      # South pole summer is during Earth's winter
            "fallEquinox": -20, 
            "winter": 75,
            "springEquinox": 20
        },
        
        # Equator temperatures by season
        "equator": {
            "summer": -40,      # Sun is over North Pole, equator gets less light
            "fallEquinox": 15,  # Transitional period
            "winter": 40,       # More direct sunlight when sun is over South Pole
            "springEquinox": 15 # Transitional period
        },
        
        # Mid-latitudes (45° North)
        "northMid": {
            "summer": 45,       # Good sunlight but not direct
            "fallEquinox": 10,  # Transitioning to less light
            "winter": -60,      # Very little sunlight
            "springEquinox": -15 # Beginning to warm
        },
        
        # Mid-latitudes (45° South)
        "southMid": {
            "summer": -60,      # Southern summer during Earth's winter
            "fallEquinox": -15,
            "winter": 45,
            "springEquinox": 10
        }
    }
    
    # Interpolate between seasons
    temp1 = temps[location][season1]
    temp2 = temps[location][season2]
    base_temp = temp1 + (temp2 - temp1) * factor
    
    # Apply day/night variation (minimal effect compared to seasonal variation)
    time_of_day = (hour + minute/60) / 24.0
    
    # Day/night variation is much less significant than on Earth
    # Due to extreme seasonal effects
    if location in ["northPole", "southPole"]:
        # Poles have no day/night variation during their respective summers and winters
        day_night_factor = 0
    else:
        # Other latitudes have some variation, but much less than seasonal
        day_night_factor = math.sin(2 * math.pi * time_of_day) * 5  # Max +/- 5°C
    
    # Apply elevation effect (standard lapse rate)
    elevation_effect = elevation * 0.0065  # Standard lapse rate: 6.5°C per km
    
    # Calculate final temperature
    final_temp = base_temp + day_night_factor - elevation_effect
    
    # Round to one decimal place
    final_temp = round(final_temp * 10) / 10
    
    # Determine weather conditions based on temperature and location
    if final_temp > 30:
        if final_temp > 60:
            conditions = "Extremely hot, scorching sunlight"
        else:
            conditions = "Hot and sunny"
    elif final_temp > 10:
        conditions = "Warm"
    elif final_temp > -10:
        conditions = "Mild"
    elif final_temp > -30:
        conditions = "Cold"
    elif final_temp > -60:
        conditions = "Very cold"
    else:
        conditions = "Extremely cold, frozen wasteland"
    
    # Add precipitation and wind based on temperature gradients and season
    if 5 < final_temp < 30 and abs(solar_declination) < 45:
        conditions += ", with potential for rain"
    elif -10 < final_temp < 5:
        conditions += ", possibility of snow or cold rain"
    elif final_temp < -10:
        conditions += ", potential for snow"
    
    # Return comprehensive weather data
    return {
        "temperature": final_temp,
        "temperature_fahrenheit": final_temp * 9/5 + 32,
        "conditions": conditions,
        "location_type": location,
        "season": season_name,
        "solar_declination": solar_declination,
        "day_night_factor": day_night_factor,
        "elevation_effect": elevation_effect
    }

def estimate_temperature(planet, lat, lon, year, day, hour, minute=0, elevation=0):
    """
    Estimate temperature at a specific location and time on a planet.
    
    Parameters:
    -----------
    planet : Planet
        Planet object
    lat : float
        Latitude in degrees
    lon : float
        Longitude in degrees
    year : int
        Current year
    day : int
        Current day of year (0-359)
    hour : int
        Current hour (0-23)
    minute : int
        Current minute (0-59)
    elevation : float
        Elevation in meters above sea level
        
    Returns:
    --------
    float
        Estimated temperature in Celsius
    """
    # Determine if it's daylight at this location and time
    is_day = planet.is_daylight(lat, lon, year, day, hour, minute)
    
    # Use noon as the reference for the subsolar point (solar declination)
    subsolar_lat, subsolar_lon = planet.get_subsolar_point(year, day, 12, 0)
    
    # Calculate orbital position (normalized from 0 to 1)
    # This helps determine where in the seasonal cycle we are
    # 0 = spring equinox, 0.25 = summer solstice, 0.5 = fall equinox, 0.75 = winter solstice
    orbital_position = day / 360.0  # Assuming 360-day year for simplicity
    
    # Calculate seasonal angle (0 to 2π)
    seasonal_angle = 2 * math.pi * orbital_position
    
    tilt = planet.get_current_tilt(year, day)
    if tilt <= 60:
        # Seasonal factor increases with latitude (minimal at equator)
        # Also scales with planet's axial tilt relative to Earth standard
        tilt_ratio = planet.get_current_tilt(year, day) / 23.5  # Normalized to Earth
        
        # Calculate normalized subsolar latitude (-1 to 1)
        # This creates a continuous sinusoidal pattern through the year
        # Alternative to using the actual subsolar_lat directly
        normalized_subsolar_lat = tilt_ratio * math.sin(seasonal_angle)

        # Base parameters - optimized for Earth-like planets
        equator_base_temp = 31  # Base temperature at equator
        max_lat_effect = 45  # Maximum cooling effect from latitude
        lat_power = 2.5  # Power for latitude effect curve
        summer_boost = 7  # Maximum summer warming
        winter_drop = 30  # Maximum winter cooling
        seasonal_power = 1  # Power for seasonal effect curve
        
        # Adjust base temperature for climate type
        if planet.climate_type == "hot":
            equator_base_temp += 3  # Higher for hot climates
        elif planet.climate_type == "cold":
            equator_base_temp -= 3  # Lower for cold climates
        
        # Latitude effect is based on absolute latitude (distance from equator)
        # Non-linear effect - stronger near poles
        lat_effect = max_lat_effect * math.pow(abs(lat) / 90, lat_power)
        
        # Calculate full seasonal cycle effect that properly transitions through all seasons
        # This creates a continuous sinusoidal pattern that matches Earth's seasons
        seasonal_strength = abs(normalized_subsolar_lat)  # How strong the seasonal effect is
        seasonal_sign = 1 if (lat * normalized_subsolar_lat > 0) else -1  # Direction of seasonal effect
        
        # Scale seasonal effect based on latitude (stronger at higher latitudes)
        seasonal_factor = math.pow(abs(lat) / 90, seasonal_power) * seasonal_strength
        seasonal_effect = seasonal_sign * (summer_boost if seasonal_sign > 0 else winter_drop) * seasonal_factor
        
        # Day/night temperature variation
        day_night_range = 4 * (planet.rotation_period/24) * (1 - 0.3 * (abs(lat) / 90))
        #day_night_range = max(3, min(day_night_range, 14))
        
        if is_day:
            # Determine time offset from solar noon
            _, subsolar_lon = planet.get_subsolar_point(year, day, hour, minute)
            time_offset = abs((lon - subsolar_lon + 180) % 360 - 180) / 180
            # Use a cosine curve for day temperature variation
            day_night_factor = day_night_range * math.cos(time_offset * math.pi/2)
        else:
            # Night cooldown
            day_night_factor = -day_night_range * 0.6
        
        # Elevation effect: temperature decreases with altitude
        if hasattr(planet, 'surface_gravity'):
            gravity_factor = planet.surface_gravity / 9.8  # Normalize to Earth gravity
        else:
            gravity_factor = 1.0  # Default to Earth gravity
        lapse_rate = 6.5 * gravity_factor  # °C per 1000m
        elevation_effect = -(elevation / 1000) * lapse_rate
        
        # Calculate final temperature
        temperature = equator_base_temp - lat_effect + seasonal_effect + day_night_factor + elevation_effect
    
    else: # (VARIARE ONLY)
        # Extreme axial tilt (> 60 degrees)
        # For planets with extreme axial tilt (especially 90 degrees)
        # The temperature model is dramatically different from Earth-like planets
        
        # The subsolar point will sweep from pole to pole through the year
        # At equinoxes, the subsolar point is at the equator
        # At solstices, the subsolar point is at one of the poles
        
        # Constants for extreme tilt model
        MAX_DIRECT_SUNLIGHT_TEMP = 75  # Max temperature with direct constant sunlight
        MIN_DARKNESS_TEMP = -85        # Min temperature with no sunlight
        EQUATOR_BASE_TEMP = 15         # Base temp at equator during equinoxes
        
        # Calculate angular distance from point to subsolar point
        # This is crucial for determining light exposure
        angular_distance = math.acos(
            math.sin(math.radians(lat)) * math.sin(math.radians(subsolar_lat)) +
            math.cos(math.radians(lat)) * math.cos(math.radians(subsolar_lat)) * 
            math.cos(math.radians(lon - subsolar_lon))
        )
        angular_distance_deg = math.degrees(angular_distance)
        
        # Calculate exposure factor (0 = complete darkness, 1 = direct overhead sun)
        if is_day:
            # During daylight, exposure depends on angle to sun
            exposure_factor = max(0, math.cos(angular_distance))
        else:
            # During night, no direct sunlight
            exposure_factor = 0
        
        # Determine seasonal factor based on subsolar_lat
        # This affects temperatures even in darkness
        seasonal_factor = abs(subsolar_lat) / 90.0  # 0 at equinoxes, 1 at solstices
        
        # Determine hemisphere alignment
        # If lat and subsolar_lat have same sign, it's "summer" in that hemisphere
        # If opposite signs, it's "winter" in that hemisphere
        same_hemisphere = (lat * subsolar_lat >= 0)
        
        # Calculate base temperature depending on hemisphere season and latitude
        if abs(lat) > 80:  # Polar regions
            if same_hemisphere and seasonal_factor > 0.8:
                # Polar summer with direct sunlight (near solstice)
                base_temp = MAX_DIRECT_SUNLIGHT_TEMP * exposure_factor
                if not is_day:  # Still warm during polar day
                    base_temp = MAX_DIRECT_SUNLIGHT_TEMP * 0.9
            elif not same_hemisphere and seasonal_factor > 0.8:
                # Polar winter with complete darkness (near solstice)
                base_temp = MIN_DARKNESS_TEMP
            else:
                # Transitional seasons
                transition_factor = seasonal_factor if same_hemisphere else (1 - seasonal_factor)
                base_temp = MIN_DARKNESS_TEMP + (MAX_DIRECT_SUNLIGHT_TEMP - MIN_DARKNESS_TEMP) * transition_factor * exposure_factor
        
        elif abs(lat) < 20:  # Equatorial regions
            if seasonal_factor < 0.2:  # Near equinoxes
                # Equator gets more direct sunlight near equinoxes
                base_temp = EQUATOR_BASE_TEMP + 15 * exposure_factor
            else:
                # Equator gets less light as sun moves toward poles
                light_reduction = seasonal_factor * 0.8
                base_temp = EQUATOR_BASE_TEMP - 40 * light_reduction + 15 * exposure_factor
        
        else:  # Mid-latitudes
            if same_hemisphere:
                # "Summer" in this hemisphere
                summer_factor = seasonal_factor * (1 - abs(abs(lat) - 45) / 45)
                base_temp = EQUATOR_BASE_TEMP + 35 * summer_factor * exposure_factor
            else:
                # "Winter" in this hemisphere
                winter_factor = seasonal_factor * (1 - abs(abs(lat) - 45) / 45)
                base_temp = EQUATOR_BASE_TEMP - 65 * winter_factor + 15 * exposure_factor
        
        # Day/night variation is less significant with extreme tilt
        # But still present except at poles during solstices
        if abs(lat) < 80 or seasonal_factor < 0.8:
            if is_day:
                day_night_boost = 5 * (1 - seasonal_factor) * exposure_factor
                base_temp += day_night_boost
            else:
                night_cooling = 8 * (1 - seasonal_factor)
                base_temp -= night_cooling
        
        # Thermal lag - temperatures lag behind solar position
        # Max temperatures occur after summer solstice, min temperatures after winter solstice
        lag_days = 15  # Thermal lag in days
        lag_angle = 2 * math.pi * (lag_days / 360.0)
        lagged_seasonal_angle = seasonal_angle + lag_angle
        lag_factor = math.sin(lagged_seasonal_angle) - math.sin(seasonal_angle)
        base_temp += lag_factor * 3  # Small adjustment for thermal lag
        
        # Apply elevation effect
        if hasattr(planet, 'surface_gravity'):
            gravity_factor = planet.surface_gravity / 9.8  # Normalize to Earth gravity
        else:
            gravity_factor = 1.0  # Default to Earth gravity
        lapse_rate = 6.5 * gravity_factor  # °C per 1000m
        elevation_effect = -(elevation / 1000) * lapse_rate
        
        # Final temperature
        temperature = base_temp + elevation_effect

    # Add small random fluctuations for realism
    seed = int(year * 1000 + day * 10 + hour + abs(lat) * 100 + abs(lon) * 10)
    random.seed(seed)
    random_factor = random.uniform(-0.8, 0.8)
    
    return temperature + random_factor

def get_weather_conditions(planet, lat, lon, year, day, hour, minute=0, elevation=0):
    """
    Determine weather conditions at a specific location and time.
    
    Parameters:
    -----------
    planet : Planet
        Planet object
    lat : float
        Latitude in degrees
    lon : float
        Longitude in degrees
    year : int
        Current year
    day : int
        Current day of year (0-359)
    hour : int
        Current hour (0-23)
    minute : int
        Current minute (0-59)
    elevation : float
        Elevation in meters above sea level
        
    Returns:
    --------
    dict
        Weather conditions including type, temperature, and description
    """
    # Get the estimated temperature and daylight status
    temperature = estimate_temperature(planet, lat, lon, year, day, hour, minute, elevation)
    is_daylight = planet.is_daylight(lat, lon, year, day, hour, minute)
    season = planet.get_season(lat, year, day)
    
    # Use noon for subsolar reference
    subsolar_lat, _ = planet.get_subsolar_point(year, day, 12, 0)
    
    # Establish a consistent seed for weather randomness
    seed = int(year * 1000 + day + hour + lat * 100 + lon * 10)
    random.seed(seed)
    
    # Base weather probabilities by climate type
    if planet.climate_type == "percepio":
        weather_probs = {
            "clear": 0.3,
            "cloudy": 0.2,
            "rain": 0.1,
            "snow": 0.1,
            "storm": 0.3
        }
    elif planet.climate_type == "celeste":
        weather_probs = {
            "clear": 0.35,
            "cloudy": 0.35,
            "rain": 0.05,
            "snow": 0.20,
            "storm": 0.05
        }
    elif planet.climate_type == "dry":
        weather_probs = {
            "clear": 0.70,
            "cloudy": 0.10,
            "rain": 0.025,
            "snow": 0.025,
            "storm": 0.15
        }
    elif planet.climate_type == "wet":
        weather_probs = {
            "clear": 0.45,
            "cloudy": 0.10,
            "rain": 0.30,
            "snow": 0.10,
            "storm": 0.05
        }
    elif planet.climate_type == "variare":
        weather_probs = {
            "clear": 0.05,
            "cloudy": 0.15,
            "rain": 0.15,
            "snow": 0.15,
            "storm": 0.50
        }
    else:  # Temperate
        weather_probs = {
            "clear": 0.60,
            "cloudy": 0.15,
            "rain": 0.15,
            "snow": 0.05,
            "storm": 0.05
        }
    
    # Adjust probabilities based on planetary and location factors
    
    # Effect of axial tilt on storm frequency
    tilt_factor = planet.get_current_tilt(year, day) / 23.5  # Normalized to Earth
    solstice_factor = abs(subsolar_lat) / max(0.1, planet.get_current_tilt(year, day))
    
    # Stronger storms near solstices with higher tilt
    if solstice_factor > 0.7:
        weather_probs["storm"] += 0.05 * (tilt_factor - 1) if tilt_factor > 1 else 0
    
    # Effect of rotation period
    rotation_factor = 24 / max(0.1, planet.rotation_period)  # Avoid division by zero
    if rotation_factor > 2:  # Faster rotation
        weather_probs["storm"] += 0.08
        weather_probs["cloudy"] += 0.08
        weather_probs["clear"] = max(0.15, weather_probs["clear"] - 0.16)
    elif rotation_factor < 0.5:  # Slower rotation
        weather_probs["clear"] += 0.08
        weather_probs["storm"] = max(0.02, weather_probs["storm"] - 0.03)
    
    # Elevation effects on weather patterns
    if elevation > 1000:
        # Higher elevations tend to be clearer but with more extreme conditions
        weather_probs["clear"] += min(0.15, elevation / 10000)
        weather_probs["cloudy"] -= min(0.1, elevation / 15000)
        
        # Snow more likely at high elevations when cold
        if temperature < 5:
            snow_boost = min(0.2, elevation / 5000)
            weather_probs["snow"] += snow_boost
            weather_probs["rain"] = max(0, weather_probs.get("rain", 0) - snow_boost/2)
    
    # Temperature effects
    if temperature < 2:
        # Convert rain to snow at freezing temperatures
        snow_prob = weather_probs.get("rain", 0) + weather_probs.get("snow", 0)
        weather_probs["rain"] = 0
        weather_probs["snow"] = snow_prob
    elif temperature > 35:
        # Increased storms in hot conditions
        storm_boost = min(0.15, (temperature - 35) / 10)
        weather_probs["storm"] += storm_boost
        weather_probs["clear"] = max(0.1, weather_probs.get("clear", 0) - storm_boost/2)
    
    # Seasonal adjustments
    if season == "Winter":
        weather_probs["clear"] = max(0.15, weather_probs.get("clear", 0) - 0.1)
        weather_probs["cloudy"] = min(0.45, weather_probs.get("cloudy", 0) + 0.1)
        if temperature < 3:
            weather_probs["snow"] = min(0.5, weather_probs.get("snow", 0) + 0.1)
    elif season == "Summer":
        if temperature > 28:
            storm_boost = min(0.15, (temperature - 28) / 20)
            weather_probs["storm"] = min(0.35, weather_probs.get("storm", 0) + storm_boost)
    
    # Normalize probabilities
    weather_types = list(weather_probs.keys())
    weather_values = list(weather_probs.values())
    total = sum(weather_values)
    if total > 0:
        weather_values = [v/total for v in weather_values]
    
    # Select weather type
    rand = random.random()
    cumulative = 0
    weather_type = "clear"  # Default
    for i, prob in enumerate(weather_values):
        cumulative += prob
        if rand <= cumulative:
            weather_type = weather_types[i]
            break
    
    # Generate descriptive text
    description = _generate_weather_description(
        weather_type, temperature, is_daylight, season, planet.rotation_period, 
        planet.initial_axial_tilt, elevation
    )
    
    return {
        "type": weather_type,
        "temperature": temperature,
        "is_daylight": is_daylight,
        "season": season,
        "elevation": elevation,
        "description": description
    }

def _generate_weather_description(weather_type, temperature, is_daylight, season, 
                                  rotation_period, axial_tilt, elevation=0):
    """
    Generate a descriptive text for the weather conditions.
    
    Parameters:
    -----------
    weather_type : str
        Type of weather (clear, cloudy, rain, snow, storm)
    temperature : float
        Temperature in Celsius
    is_daylight : bool
        Whether it's daylight or night
    season : str
        Current season
    rotation_period : float
        Planet's rotation period in hours
    axial_tilt : float
        Planet's axial tilt in degrees
    elevation : float
        Elevation in meters
        
    Returns:
    --------
    str
        Weather description
    """
    time_of_day = "day" if is_daylight else "night"
    planet_desc = ""
    elevation_desc = ""
    
    # Planetary characteristic descriptions
    if rotation_period < 10:
        planet_desc = "The short day/night cycle creates rapidly changing conditions. "
    elif rotation_period > 36:
        planet_desc = "The long day/night cycle leads to sustained weather patterns. "
        
    if axial_tilt > 40:
        planet_desc += "The extreme axial tilt causes dramatic seasonal effects. "
    elif axial_tilt < 10:
        planet_desc += "The minimal axial tilt results in stable year-round conditions. "
    
    # Elevation descriptions
    if elevation > 2000:
        elevation_desc = f"At this high elevation of {elevation}m, air is thin and conditions can change rapidly. "
    elif elevation > 1000:
        elevation_desc = f"The moderate elevation of {elevation}m affects local weather patterns. "
    
    # Weather type descriptions with elevation considerations
    if weather_type == "clear":
        if temperature > 30:
            desc = f"A hot, clear {time_of_day} with excellent visibility. {elevation_desc}{planet_desc}The sun is intense."
        elif temperature < 5:
            desc = f"A cold, clear {time_of_day} with crisp air and excellent visibility. {elevation_desc}{planet_desc}"
        else:
            desc = f"A pleasant, clear {time_of_day} with excellent visibility. {elevation_desc}{planet_desc}"
    
    elif weather_type == "cloudy":
        if temperature > 25:
            desc = f"A warm, overcast {time_of_day}. {elevation_desc}{planet_desc}The cloud cover is thick but no precipitation is occurring."
        elif temperature < 5:
            desc = f"A cold, gray {time_of_day}. {elevation_desc}{planet_desc}The sky is completely overcast."
        else:
            desc = f"A mild {time_of_day} with significant cloud cover. {elevation_desc}{planet_desc}"
    
    elif weather_type == "rain":
        intensity = random.choice(["light", "moderate", "heavy"])
        if elevation > 1500 and temperature < 10:
            desc = f"A cool {time_of_day} with {intensity} sleet and rain. {elevation_desc}{planet_desc}The higher elevation makes precipitation unstable."
        elif temperature > 25:
            desc = f"A warm, rainy {time_of_day} with {intensity} precipitation. {elevation_desc}{planet_desc}The air is humid."
        else:
            desc = f"A cool, rainy {time_of_day} with {intensity} precipitation. {elevation_desc}{planet_desc}"
    
    elif weather_type == "snow":
        intensity = random.choice(["light", "moderate", "heavy"])
        if elevation > 2000:
            desc = f"A cold {time_of_day} with {intensity} snowfall. {elevation_desc}{planet_desc}The high altitude intensifies the snow conditions."
        else:
            desc = f"A cold {time_of_day} with {intensity} snowfall. {elevation_desc}{planet_desc}Visibility is reduced."
    
    elif weather_type == "storm":
        if temperature > 25 and temperature < 35:
            if elevation > 1500:
                storm_type = random.choice(["thunderstorm", "electrical storm", "high-elevation lightning storm"])
                desc = f"A hot, stormy {time_of_day} with an active {storm_type}. {elevation_desc}{planet_desc}The high elevation makes the storm particularly intense."
            else:
                storm_type = random.choice(["thunderstorm", "electrical storm", "torrential downpour"])
                desc = f"A hot, stormy {time_of_day} with an active {storm_type}. {elevation_desc}{planet_desc}"
        elif temperature < 5:
            desc = f"A cold, wintery storm with a mix of snow and freezing rain. {elevation_desc}{planet_desc}Conditions could be dangerous."
        else:
            desc = f"A stormy {time_of_day} with strong winds. {elevation_desc}{planet_desc}"
    
    else:
        desc = f"Unusual weather conditions with temperature around {temperature:.1f}°C. {elevation_desc}{planet_desc}"
    
    return desc

def analyze_habitability(planet, year=0, day=0):
    """
    Analyze the habitability of different regions of the planet.
    
    Parameters:
    -----------
    planet : Planet
        Planet object
    year : int
        Current year for axial tilt calculation
    day : int
        Current day for seasonal reference
        
    Returns:
    --------
    dict
        Habitability analysis including optimal zones and challenges
    """
    latitudes = list(range(-90, 91, 10))
    elevations = [0, 500, 1000, 2000, 3000]  # Different elevations to analyze
    habitable_zones = []
    
    # Temperature thresholds for habitability
    livable_min = -15
    optimal_min = 5
    optimal_max = 32
    livable_max = 48
    
    for lat in latitudes:
        for elevation in elevations:
            # Check summer and winter temperatures at noon and midnight
            summer_day_temp = estimate_temperature(planet, lat, 0, year, 90, 12, 0, elevation)
            summer_night_temp = estimate_temperature(planet, lat, 0, year, 90, 0, 0, elevation)
            winter_day_temp = estimate_temperature(planet, lat, 0, year, 270, 12, 0, elevation)
            winter_night_temp = estimate_temperature(planet, lat, 0, year, 270, 0, 0, elevation)
            
            # Calculate averages and ranges
            summer_avg = (summer_day_temp + summer_night_temp) / 2
            winter_avg = (winter_day_temp + winter_night_temp) / 2
            avg_temp = (summer_avg + winter_avg) / 2
            seasonal_range = abs(summer_avg - winter_avg)
            daily_range = max(abs(summer_day_temp - summer_night_temp), 
                              abs(winter_day_temp - winter_night_temp))
            
            # Determine habitability status with more nuanced criteria
            if optimal_min <= avg_temp <= optimal_max and seasonal_range < 35 and daily_range < 20:
                status = "optimal"
            elif livable_min <= avg_temp <= livable_max and seasonal_range < 55 and daily_range < 30:
                status = "livable"
            else:
                status = "hostile"
            
            habitable_zones.append({
                "latitude": lat,
                "elevation": elevation,
                "avg_temperature": avg_temp,
                "seasonal_range": seasonal_range,
                "daily_range": daily_range,
                "status": status,
                "summer_day": summer_day_temp,
                "summer_night": summer_night_temp,
                "winter_day": winter_day_temp,
                "winter_night": winter_night_temp
            })
    
    current_tilt = planet.get_current_tilt(year, day)
    challenges = []
    
    # Identify challenges based on planetary parameters
    if current_tilt > 35:
        challenges.append({
            "type": "extreme_seasons",
            "description": f"Axial tilt of {current_tilt:.1f}° causes extreme seasonal variations",
            "impact": "Seasonal migration necessary for survival in mid to high latitudes"
        })
    
    if planet.rotation_period > 30:
        challenges.append({
            "type": "long_days",
            "description": f"Long day/night cycle of {planet.rotation_period:.1f} hours",
            "impact": "Significant temperature extremes between day and night"
        })
    elif planet.rotation_period < 12:
        challenges.append({
            "type": "short_days",
            "description": f"Short day/night cycle of {planet.rotation_period:.1f} hours",
            "impact": "Rapid weather changes and biological rhythm challenges"
        })
    
    if current_tilt > 40:
        polar_band = 90 - current_tilt
        challenges.append({
            "type": "permanent_day_night",
            "description": f"Regions above {polar_band:.1f}° latitude experience extended day or night during solstices",
            "impact": "Polar regions difficult to inhabit without significant technological assistance"
        })
    
    # Count different habitability zones
    optimal_count = sum(1 for zone in habitable_zones if zone["status"] == "optimal")
    livable_count = sum(1 for zone in habitable_zones if zone["status"] == "livable")
    total_zones = len(habitable_zones)
    
    # Determine overall assessment
    if optimal_count >= total_zones * 0.35:
        overall = "Highly habitable"
    elif livable_count >= total_zones * 0.25:
        overall = "Moderately habitable"
    else:
        overall = "Marginally habitable"
    
    # Generate settlement recommendations
    recommendations = _generate_settlement_recommendations(habitable_zones, challenges, planet)
    
    return {
        "overall_assessment": overall,
        "habitable_zones": habitable_zones,
        "challenges": challenges,
        "settlement_recommendations": recommendations,
        "optimal_percentage": (optimal_count / total_zones) * 100,
        "livable_percentage": (livable_count / total_zones) * 100
    }

def _generate_settlement_recommendations(habitable_zones, challenges, planet):
    """
    Generate recommendations for settlement locations.
    
    Parameters:
    -----------
    habitable_zones : list
        List of zones with habitability data
    challenges : list
        List of habitability challenges
    planet : Planet
        Planet object
        
    Returns:
    --------
    list
        Settlement recommendations
    """
    recommendations = []
    
    # Group zones by status and elevation
    optimal_zones = {}
    for zone in habitable_zones:
        if zone["status"] == "optimal":
            key = f"{zone['elevation']}"
            if key not in optimal_zones:
                optimal_zones[key] = []
            optimal_zones[key].append(zone)
    
    # Find best elevation band for settlements
    best_elevation = None
    most_optimal_zones = 0
    for elevation, zones in optimal_zones.items():
        if len(zones) > most_optimal_zones:
            most_optimal_zones = len(zones)
            best_elevation = int(elevation)
    
    if best_elevation is not None:
        best_lats = [zone["latitude"] for zone in optimal_zones[str(best_elevation)]]
        
        # Find contiguous latitude bands
        lat_bands = []
        current_band = [best_lats[0]] if best_lats else []
        
        for i in range(1, len(best_lats)):
            if best_lats[i] == best_lats[i-1] + 10:
                current_band.append(best_lats[i])
            else:
                lat_bands.append(current_band)
                current_band = [best_lats[i]]
        
        if current_band:
            lat_bands.append(current_band)
        
        # Identify largest band
        if lat_bands:
            largest_band = max(lat_bands, key=len)
            band_start = min(largest_band)
            band_end = max(largest_band)
            
            if band_start == band_end:
                lat_range = f"{band_start}°"
            else:
                lat_range = f"{band_start}° to {band_end}°"
            
            recommendations.append({
                "type": "primary_settlement",
                "location": f"Latitudes {lat_range} at elevation {best_elevation}m",
                "reason": "Most consistently optimal temperatures year-round"
            })
    
    # Elevation-specific recommendations
    elevation_zones = {}
    for zone in habitable_zones:
        key = zone["elevation"]
        if key not in elevation_zones:
            elevation_zones[key] = []
        elevation_zones[key].append(zone)
    
    for elevation, zones in elevation_zones.items():
        optimal_count = sum(1 for z in zones if z["status"] == "optimal")
        if optimal_count > 0:
            optimal_percent = (optimal_count / len(zones)) * 100
            if optimal_percent >= 30 and int(elevation) > 0:
                recommendations.append({
                    "type": "elevation_advantage",
                    "location": f"Elevations around {int(elevation)}m",
                    "advantage": f"{optimal_percent:.1f}% of zones at this elevation are optimal",
                    "reason": "Elevation helps mitigate temperature extremes"
                })
    
    # Recommendations based on planetary characteristics
    tilt = planet.initial_axial_tilt
    if tilt > 25:
        recommendations.append({
            "type": "nomadic",
            "description": "Seasonal migration recommended due to strong seasonal variations",
            "pattern": f"Move {int(tilt/3)}° toward equator during local winter"
        })
    
    if planet.rotation_period < 12:
        recommendations.append({
            "type": "storm_adaptation",
            "description": "Requires robust storm-resistant architecture and weather prediction",
            "reason": f"Short {planet.rotation_period}-hour day creates rapidly changing weather patterns"
        })
    elif planet.rotation_period > 30:
        recommendations.append({
            "type": "day_night_adaptation",
            "description": "Settlements need robust temperature regulation systems",
            "reason": f"Long {planet.rotation_period}-hour day/night cycle causes extreme temperature variations"
        })
    
    # Climate type adaptations
    if planet.climate_type == "hot":
        recommendations.append({
            "type": "heat_adaptation",
            "description": "Settlements require cooling systems and water conservation",
            "reason": "Higher baseline temperatures across the planet"
        })
    elif planet.climate_type == "cold":
        recommendations.append({
            "type": "cold_adaptation",
            "description": "Settlements require robust heating and insulation",
            "reason": "Lower baseline temperatures across the planet"
        })
    
    # Recommendations for extreme conditions
    has_extreme_seasons = any(c["type"] == "extreme_seasons" for c in challenges)
    if has_extreme_seasons:
        recommendations.append({
            "type": "seasonal_migration",
            "description": "Establish seasonal settlements at different elevations",
            "pattern": "Consider higher elevations during summer and lower elevations during winter"
        })
    
    has_permanent_day_night = any(c["type"] == "permanent_day_night" for c in challenges)
    if has_permanent_day_night:
        recommendations.append({
            "type": "polar_adaptation",
            "description": "Polar settlements require special adaptations",
            "reason": "Must handle extended periods of darkness or continuous daylight"
        })
    
    return recommendations