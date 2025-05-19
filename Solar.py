"""
Time Reference System
Time is based on a full orbital year (360 Nexus days for simplicity)
Each planet has its own day length, but shares the same orbital period
Year/day/hour/minute should be our primary time reference
"""

"""
Planet Class
Properties:
- name: Planet name
- axial_tilt: Current tilt in degrees
- rotation_period: Hours per day
- axial_precession_period: Years to complete one precession cycle
- radius: Size in km
- climate_type: Base temperature profile

Methods:
- get_day_length(): Get day length in hours
- get_days_per_year(): Number of local days in a year
- get_current_tilt(year): Calculate tilt accounting for precession
- get_subsolar_point(year, day, hour): Get lat/long where sun is directly overhead
- is_daylight(lat, long, year, day, hour): Is this location in daylight?
- get_daylight_hours(lat, year, day): Calculate hours of daylight
- get_local_time(year, day, hour, longitude): Convert global time to local time
- get_season(lat, year, day): Current season at location
"""
import math
import numpy as np
from datetime import datetime, timedelta
import random
import textwrap

class Planet:
    """
    Planet class representing a planet in our solar system.
    
    Each planet has the same orbital period (360 days) but different rotation periods.
    Time is measured in a standard format with year, day, hour, and minute, where
    day refers to a Nexus day (24 hours).
    """
    
    def __init__(self, name, axial_tilt, rotation_period, axial_precession_period=None, 
                 radius=6371, climate_type="temperate"):
        """
        Initialize a planet with basic properties.
        
        Parameters:
        -----------
        name : str
            Name of the planet
        axial_tilt : float
            Initial axial tilt in degrees
        rotation_period : float
            Length of one day in hours
        axial_precession_period : float or None
            Period for complete axial precession in years, None if no precession
        radius : float
            Planet radius in kilometers (default: Earth radius)
        climate_type : str
            Base climate type ("temperate", "hot", "cold")
        """
        self.name = name
        self.initial_axial_tilt = axial_tilt
        self.rotation_period = rotation_period
        self.axial_precession_period = axial_precession_period
        self.radius = radius
        self.climate_type = climate_type
        
        # Constants
        self.orbital_period = 360  # Days per year (fixed for all planets)
    
    def get_day_length(self):
        """
        Get the length of one day on this planet.
        
        Returns:
        --------
        float
            Day length in hours
        """
        return self.rotation_period
    
    def get_days_per_year(self):
        """
        Calculate how many local days occur in one year.
        
        Returns:
        --------
        float
            Number of local days per year
        """
        return self.orbital_period * 24 / self.rotation_period
    
    def get_current_tilt(self, year, day=0):
        """
        Calculate the current axial tilt accounting for precession.
        
        Parameters:
        -----------
        year : int
            Current year
        day : int
            Current day of year (0-359)
            
        Returns:
        --------
        float
            Current axial tilt in degrees
        """
        # If no precession, return the initial tilt
        if self.axial_precession_period is None:
            return self.initial_axial_tilt
        
        # Calculate the total time in years
        total_years = year + day / self.orbital_period
        
        # Calculate the phase in the precession cycle (0 to 2π)
        phase = 2 * np.pi * total_years / self.axial_precession_period
        
        # For simplicity, model a small sinusoidal variation around the initial tilt
        # Real precession is more complex, but this captures the basic behavior
        variation = 2.0  # degrees of variation
        return self.initial_axial_tilt + variation * np.sin(phase)
    
    def get_subsolar_point(self, year, day, hour=12, minute=0):
        """
        Calculate the latitude and longitude where the sun is directly overhead.
        
        Parameters:
        -----------
        year : int
            Current year
        day : int
            Current day of year (0-359)
        hour : int
            Current hour (0-23)
        minute : int
            Current minute (0-59)
            
        Returns:
        --------
        tuple
            (latitude, longitude) of subsolar point in degrees
        """
        # Get current axial tilt
        current_tilt = self.get_current_tilt(year, day)
        
        # Calculate orbital position (0 to 2π)
        # Day 0 = spring equinox (sun directly over equator, moving north)
        orbital_position = 2 * np.pi * day / self.orbital_period
        
        # Calculate solar declination (latitude where sun is directly overhead)
        # This varies throughout the year due to axial tilt
        solar_declination = current_tilt * np.sin(orbital_position)
        
        # Calculate fraction of day that has passed
        day_fraction = (hour + minute / 60) / 24
        
        # Calculate longitude based on time of day
        # At noon (day_fraction = 0.5) on the reference meridian, the sun is directly overhead
        # Longitude ranges from -180 to 180, with negative being west
        longitude = (0.5 - day_fraction) * 360
        if longitude > 180:
            longitude -= 360
        
        return (solar_declination, longitude)
    
    def is_daylight(self, lat, lon, year, day, hour=12, minute=0):
        """
        Determine if a location is in daylight at the specified time.
        
        Parameters:
        -----------
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
            
        Returns:
        --------
        bool
            True if the location is in daylight, False if in darkness
        """
        # Get subsolar point
        subsolar_lat, subsolar_lon = self.get_subsolar_point(year, day, hour, minute)
        
        # Convert to radians for calculations
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        subsolar_lat_rad = math.radians(subsolar_lat)
        subsolar_lon_rad = math.radians(subsolar_lon)
        
        # Calculate the angular distance between the point and the subsolar point
        # using the great circle distance formula
        angular_distance = math.acos(
            math.sin(lat_rad) * math.sin(subsolar_lat_rad) +
            math.cos(lat_rad) * math.cos(subsolar_lat_rad) * 
            math.cos(lon_rad - subsolar_lon_rad)
        )
        
        # The location is in daylight if the angular distance is less than π/2 radians (90 degrees)
        return angular_distance < math.pi / 2
    
    def get_daylight_hours(self, lat, year, day):
        """
        Calculate the number of hours of daylight at a specific latitude and day.
        
        Parameters:
        -----------
        lat : float
            Latitude in degrees
        year : int
            Current year
        day : int
            Current day of year (0-359)
            
        Returns:
        --------
        float
            Hours of daylight at the specified latitude and day
        """
        # Convert to radians
        lat_rad = math.radians(lat)
        
        # Get current axial tilt
        current_tilt = self.get_current_tilt(year, day)
        
        # Calculate orbital position
        orbital_position = 2 * np.pi * day / self.orbital_period
        
        # Calculate solar declination
        solar_declination = current_tilt * np.sin(orbital_position)
        solar_declination_rad = math.radians(solar_declination)
        
        # Calculate day length using standard formula
        # If tan(lat) * tan(declination) >= 1, it's polar day (24 hours daylight)
        # If tan(lat) * tan(declination) <= -1, it's polar night (0 hours daylight)
        arg = math.tan(lat_rad) * math.tan(solar_declination_rad)
        
        if arg >= 1:
            return self.rotation_period  # Polar day - sun never sets
        elif arg <= -1:
            return 0  # Polar night - sun never rises
        else:
            # Calculate the hour angle
            hour_angle = math.acos(-arg)
            
            # Convert to hours (2 * hour_angle = total daylight angle in radians)
            return self.rotation_period * hour_angle / math.pi
    
    def get_local_time(self, year, day, hour, minute, longitude):
        """
        Convert a standard time to local time based on longitude.
        
        Parameters:
        -----------
        year : int
            Current year
        day : int
            Current day of year (0-359)
        hour : int
            Current hour (0-23)
        minute : int
            Current minute (0-59)
        longitude : float
            Longitude in degrees (-180 to 180)
            
        Returns:
        --------
        tuple
            (hour, minute) of local time
        """
        # Calculate the time difference based on longitude
        # Each 15 degrees of longitude = 1 hour time difference
        hour_offset = longitude / 15
        
        # Calculate total minutes
        total_minutes = hour * 60 + minute + hour_offset * 60
        
        # Adjust for day boundaries
        day_minutes = 24 * 60
        while total_minutes < 0:
            total_minutes += day_minutes
            day -= 1
        while total_minutes >= day_minutes:
            total_minutes -= day_minutes
            day += 1
            
        # Adjust for year boundaries
        while day < 0:
            day += self.orbital_period
            year -= 1
        while day >= self.orbital_period:
            day -= self.orbital_period
            year += 1
            
        # Convert back to hours and minutes
        adjusted_hour = int(total_minutes // 60) % 24
        adjusted_minute = int(total_minutes % 60)
        
        return (year, day, adjusted_hour, adjusted_minute)
    
    def get_season(self, lat, year, day):
        """
        Determine the current season at a given latitude.
        
        Parameters:
        -----------
        lat : float
            Latitude in degrees
        year : int
            Current year
        day : int
            Current day of year (0-359)
            
        Returns:
        --------
        str
            Season name ("Spring", "Summer", "Fall", "Winter" or "No distinct seasons")
        """
        # For minimal axial tilt, there aren't really seasons
        current_tilt = self.get_current_tilt(year, day)
        if abs(current_tilt) < 5:
            return "No distinct seasons"
        
        # Calculate orbital position in the year
        # We consider day 0 to be the spring equinox in the northern hemisphere
        day_fraction = day / self.orbital_period
        
        # Northern Hemisphere seasons
        if lat >= 0:
            if day_fraction < 0.25:  # First quarter of the year (spring)
                return "Spring"
            elif day_fraction < 0.5:  # Second quarter (summer)
                return "Summer"
            elif day_fraction < 0.75:  # Third quarter (fall)
                return "Fall"
            else:  # Last quarter (winter)
                return "Winter"
        # Southern Hemisphere (reversed seasons)
        else:
            if day_fraction < 0.25:  # First quarter (fall in the south)
                return "Fall"
            elif day_fraction < 0.5:  # Second quarter (winter in the south)
                return "Winter"
            elif day_fraction < 0.75:  # Third quarter (spring in the south)
                return "Spring"
            else:  # Last quarter (summer in the south)
                return "Summer"


"""
SolarSystem Class
Properties:
- planets: Array of Planet objects

Methods:
- create_standard_system(): Create our 6-planet system
- get_planet_by_name(name): Find planet by name
- get_subsolar_points(year, day, hour): Get sun positions on all planets
"""
class SolarSystem:
    """
    Class representing our solar system with multiple planets.
    """
    
    def __init__(self):
        """Initialize the solar system with an empty list of planets."""
        self.planets = []
    
    def add_planet(self, planet):
        """
        Add a planet to the solar system.
        
        Parameters:
        -----------
        planet : Planet
            Planet object to add
        """
        self.planets.append(planet)
    
    def get_planet_by_name(self, name):
        """
        Find a planet by its name.
        
        Parameters:
        -----------
        name : str
            Name of the planet to find
            
        Returns:
        --------
        Planet or None
            The planet object if found, None otherwise
        """
        for planet in self.planets:
            if planet.name.lower() == name.lower():
                return planet
        return None
    
    def get_subsolar_points(self, year, day, hour=12, minute=0):
        """
        Get subsolar points for all planets at a specific time.
        
        Parameters:
        -----------
        year : int
            Current year
        day : int
            Current day of year (0-359)
        hour : int
            Current hour (0-23)
        minute : int
            Current minute (0-59)
            
        Returns:
        --------
        dict
            Dictionary mapping planet names to their subsolar points (lat, lon)
        """
        results = {}
        for planet in self.planets:
            results[planet.name] = planet.get_subsolar_point(year, day, hour, minute)
        return results
    
    def add_moon_system(self, planet_name, moon_system):
        """
        Add a moon system to a planet in the solar system.
        
        Parameters:
        -----------
        planet_name : str
            Name of the planet to add the moon system to
        moon_system : MoonSystem
            MoonSystem object to add
        """
        planet = self.get_planet_by_name(planet_name)
        if planet:
            planet.moons = moon_system
        else:
            raise ValueError(f"Planet {planet_name} not found in the solar system.")

def create_standard_system():
    """
    Create the standard solar system with our six planets.
    
    Returns:
    --------
    SolarSystem
        Solar system object with the standard six planets
    """
    solar_system = SolarSystem()
    
    # Nexus - Earth-like planet
    nexus = Planet(
        name="Nexus",
        axial_tilt=23.5,
        rotation_period=24.0,
        axial_precession_period=26000,   # Earth's precession period with one moon
        radius=6371,
        climate_type="temperate"
    )
    solar_system.add_planet(nexus)

    # Add Nexus moon
    nexus_moons = MoonSystem("Nexus")
    nexus_moons.add_moon("Luna", radius_km=1737, orbit_radius_km=384400, orbital_period_days=30)
    solar_system.add_moon_system("Nexus", nexus_moons)
    
    # Celeste - Ringed planet
    celeste = Planet(
        name="Celeste",
        axial_tilt=29.0,
        rotation_period=18.0,
        axial_precession_period=50000,  # Slower precession due to ring and small moon system
        radius=7300,
        climate_type="cold"
    )
    solar_system.add_planet(celeste)

    # Add Celeste tiny moon and rings
    celeste_moons = MoonSystem("Celeste")
    celeste_moons.add_moon("Lira", 500, 10000, 5)
    celeste_moons.add_rings(8000, 12000)
    solar_system.add_moon_system("Celeste", celeste_moons)
    
    # Fortis Crags - Rocky planet
    fortis = Planet(
        name="Fortis Crags",
        axial_tilt=10,
        rotation_period=48,
        axial_precession_period=15000,  # Faster precession due to dual moons
        radius=5800,
        climate_type="dry"
    )
    solar_system.add_planet(fortis)

    # Add Fortis Crags moons
    fortis_moons = MoonSystem("Fortis Crags")
    fortis_moons.add_moon("Rinaya", 800, 10000, 30)
    fortis_moons.add_moon("Renshiro", 1000, 20000, 30)
    solar_system.add_moon_system("Fortis Crags", fortis_moons)
    
    # Percepio - Fast-rotating stormy planet
    percepio = Planet(
        name="Percepio",
        axial_tilt=25,
        rotation_period=6.0,  # Very fast rotation
        axial_precession_period=8000,  # Rapid precession from multiple small moons
        radius=6000,
        climate_type="stormy"
    )
    solar_system.add_planet(percepio)

    # Add Percepio moons
    percepio_moons = MoonSystem("Percepio")
    percepio_moons.add_moon("Taryesh", 300, 8000, 10)
    percepio_moons.add_moon("Valmira", 300, 8000, 10)
    percepio_moons.add_moon("Zoravin", 300, 8000, 10)
    percepio_moons.add_moon("Navirith", 300, 8000, 10)
    percepio_moons.add_moon("Koryath", 300, 8000, 10)
    percepio_moons.add_moon("Suvareth", 300, 8000, 10)
    solar_system.add_moon_system("Percepio", percepio_moons)
    
    # Variare - Extreme tilt planet
    variare = Planet(
        name="Variare",
        axial_tilt=90,  # Sideways
        rotation_period=12.0,
        axial_precession_period=np.inf,  # No precession and no moons
        radius=6500,
        climate_type="variare"
    )
    solar_system.add_planet(variare)

    # Add Variare moon
    variare_moons = MoonSystem("Variare")
    variare_moons.add_moon("Veyla", 1000, 10000, 30)
    solar_system.add_moon_system("Variare", variare_moons)
    
    # Synvios - Lush symbiotic planet
    synvios = Planet(
        name="Synvios",
        axial_tilt=20,
        rotation_period=20,
        axial_precession_period=12000,  # Precession from binary moons
        radius=6800,
        climate_type="wet"
    )
    solar_system.add_planet(synvios)

    # Add Synvios binary moons
    synvios_moons = MoonSystem("Synvios")
    synvios_moons.add_moon("Morani", 1200, 10000, 30)
    # Add a minimoon to Sylvan
    sylvan = synvios_moons.get_moon_by_name("Morani")
    sylvan.add_minimoon("Mariko", 200, 1000, 5)
    solar_system.add_moon_system("Synvios", synvios_moons)
    
    return solar_system

class MiniMoon:
    def __init__(self, name, radius_km, orbit_radius_km, orbital_period_days, parent_moon):
        """
        Initialize a minimoon (moon of a moon) with given parameters
        
        Parameters:
        name (str): Name of the minimoon
        radius_km (float): Radius of the minimoon in kilometers
        orbit_radius_km (float): Distance from parent moon center in kilometers
        orbital_period_days (float): Orbital period around parent moon in Earth days
        parent_moon (Moon): The moon object this minimoon orbits
        """
        self.name = name
        self.radius = radius_km
        self.orbit_radius = orbit_radius_km
        self.orbital_period = orbital_period_days
        self.parent_moon = parent_moon
        
        # Calculate angular size as seen from parent moon surface
        self.angular_size_degrees = 2 * math.degrees(math.atan(self.radius / (self.orbit_radius - parent_moon.radius)))
        
        # Initialize with random orbital position
        self.initial_phase = random.random() * 2 * np.pi
    
    def get_position(self, absolute_time):
        """
        Calculate orbital position around parent moon at a given absolute time
        
        Parameters:
        absolute_time (float): Time in Earth days since reference point
        
        Returns:
        float: Orbital position in radians (0 to 2π)
        """
        # Calculate orbital position
        orbit_fraction = absolute_time / self.orbital_period
        position = (orbit_fraction * 2 * np.pi + self.initial_phase) % (2 * np.pi)
        return position
    
    def get_absolute_position(self, absolute_time):
        """
        Calculate absolute position relative to the planet, combining parent moon's orbit and minimoon's orbit
        
        Parameters:
        absolute_time (float): Time in Earth days since reference point
        
        Returns:
        tuple: (x, y, z) coordinates relative to planet center
        """
        # Get parent moon's position
        moon_pos = self.parent_moon.get_position(absolute_time)
        moon_x = self.parent_moon.orbit_radius * math.cos(moon_pos)
        moon_y = self.parent_moon.orbit_radius * math.sin(moon_pos)
        moon_z = 0  # Assuming circular orbit in xy-plane
        
        # Get minimoon's position relative to parent moon
        mini_pos = self.get_position(absolute_time)
        mini_rel_x = self.orbit_radius * math.cos(mini_pos)
        mini_rel_y = self.orbit_radius * math.sin(mini_pos)
        mini_rel_z = 0  # Assuming circular orbit in xy-plane
        
        # Combine positions
        # This is a simplification - in reality we would need to consider the 3D orientation
        x = moon_x + mini_rel_x
        y = moon_y + mini_rel_y
        z = moon_z + mini_rel_z
        
        return (x, y, z)
    
    def __str__(self):
        return (f"MiniMoon: {self.name}\n"
                f"Radius: {self.radius:.1f} km\n"
                f"Orbit Radius: {self.orbit_radius:.1f} km\n"
                f"Orbital Period: {self.orbital_period:.2f} Earth days\n"
                f"Angular Size: {self.angular_size_degrees:.4f}°\n"
                f"Parent Moon: {self.parent_moon.name}")

class Moon:
    def __init__(self, name, radius_km, orbit_radius_km, orbital_period_days, planet_radius_km=6371):
        """
        Initialize a moon with given parameters
        
        Parameters:
        name (str): Name of the moon
        radius_km (float): Radius of the moon in kilometers
        orbit_radius_km (float): Distance from planet center in kilometers
        orbital_period_days (float): Orbital period around planet in Earth days
        planet_radius_km (float): Radius of the parent planet in kilometers (default Earth radius)
        """
        self.name = name
        self.radius = radius_km
        self.orbit_radius = orbit_radius_km
        self.orbital_period = orbital_period_days
        self.planet_radius = planet_radius_km
        
        # Calculate angular size as seen from planet surface
        self.angular_size_degrees = 2 * math.degrees(math.atan(self.radius / (self.orbit_radius - self.planet_radius)))
        
        # Initialize with random orbital position
        self.initial_phase = random.random() * 2 * np.pi
        
        # Initialize empty list for minimoons
        self.minimoons = []
    
    def get_position(self, absolute_time):
        """
        Calculate orbital position at a given absolute time
        
        Parameters:
        absolute_time (float): Time in Earth days since reference point
        
        Returns:
        float: Orbital position in radians (0 to 2π)
        """
        # Calculate orbital position
        orbit_fraction = absolute_time / self.orbital_period
        position = (orbit_fraction * 2 * np.pi + self.initial_phase) % (2 * np.pi)
        return position
    
    def add_minimoon(self, name, radius_km, orbit_radius_km, orbital_period_days):
        """
        Add a minimoon orbiting this moon
        
        Parameters:
        name (str): Name of the minimoon
        radius_km (float): Radius of the minimoon in kilometers
        orbit_radius_km (float): Distance from moon center in kilometers
        orbital_period_days (float): Orbital period around moon in Earth days
        
        Returns:
        MiniMoon: The newly created minimoon object
        """
        minimoon = MiniMoon(name, radius_km, orbit_radius_km, orbital_period_days, self)
        self.minimoons.append(minimoon)
        return minimoon
    
    def is_binary_system(self):
        """
        Check if this moon forms a binary system with its minimoons
        
        Returns:
        bool: True if this moon has minimoons, False otherwise
        """
        return len(self.minimoons) > 0
    
    def __str__(self):
        output = (f"Moon: {self.name}\n"
                f"Radius: {self.radius:.1f} km\n"
                f"Orbit Radius: {self.orbit_radius:.1f} km\n"
                f"Orbital Period: {self.orbital_period:.2f} Earth days\n"
                f"Angular Size: {self.angular_size_degrees:.4f}°")
        
        if self.minimoons:
            output += f"\nNumber of minimoons: {len(self.minimoons)}"
            for i, minimoon in enumerate(self.minimoons):
                output += f"\n  Minimoon {i+1}: {minimoon.name} (r={minimoon.radius:.1f} km)"
        
        return output

class MoonSystem:
    def __init__(self, planet_name, planet_radius_km=6371):
        """
        Initialize a moon system for a planet
        
        Parameters:
        planet_name (str): Name of the parent planet
        planet_radius_km (float): Radius of the parent planet in kilometers
        """
        self.planet_name = planet_name
        self.planet_radius = planet_radius_km
        self.moons = []
        self.has_rings = False
        self.ring_inner_radius = 0
        self.ring_outer_radius = 0

    def get_moon_by_name(self, name):
        """
        Find a moon in the system by its name
        
        Parameters:
        name (str): Name of the moon to find
        
        Returns:
        Moon or None: The moon object if found, None otherwise
        """
        for moon in self.moons:
            if moon.name.lower() == name.lower():
                return moon
        return None
    
    def add_moon(self, name, radius_km, orbit_radius_km, orbital_period_days):
        """
        Add a moon to the system
        
        Parameters:
        name (str): Name of the moon
        radius_km (float): Radius of the moon in kilometers
        orbit_radius_km (float): Distance from planet center in kilometers
        orbital_period_days (float): Orbital period around planet in Earth days
        
        Returns:
        Moon: The newly created moon object
        """
        moon = Moon(name, radius_km, orbit_radius_km, orbital_period_days, self.planet_radius)
        self.moons.append(moon)
        return moon
    
    def add_rings(self, inner_radius_km, outer_radius_km):
        """
        Add rings to the planet
        
        Parameters:
        inner_radius_km (float): Inner radius of the ring system in kilometers
        outer_radius_km (float): Outer radius of the ring system in kilometers
        """
        self.has_rings = True
        self.ring_inner_radius = inner_radius_km
        self.ring_outer_radius = outer_radius_km
    
    def find_eclipses(self, planet, start_time, duration_days):
        """
        Find solar and lunar eclipses within a time period
        
        Parameters:
        planet (Planet): Parent planet object
        start_time (float): Start time in Earth days
        duration_days (float): Duration to search in Earth days
        
        Returns:
        list: List of eclipse events with details
        """
        eclipse_events = []
        
        # Number of time steps to check
        num_steps = int(duration_days * 24)  # Check every hour
        
        # Check for potential eclipses at each time step
        for step in range(num_steps):
            time = start_time + step / 24
            
            # For each moon, check if it's in position for an eclipse
            for moon in self.moons:
                # Get positions of sun, moon, and planet
                subsolar_lat, subsolar_lon = planet.get_subsolar_point(time)
                moon_position = moon.get_position(time)
                
                # Solar eclipse: Moon between planet and sun
                # This is a very simplified check - in reality, need to check alignment in 3D
                solar_eclipse_alignment = self._check_solar_eclipse(moon_position, subsolar_lon, time)
                
                if solar_eclipse_alignment < 5:  # Degrees of alignment tolerance
                    # Find location on planet where eclipse is visible
                    eclipse_lat, eclipse_lon = self._calculate_eclipse_location(subsolar_lat, subsolar_lon, moon_position)
                    
                    eclipse_events.append({
                        "type": "Solar Eclipse",
                        "time": time,
                        "moon": moon.name,
                        "location": (eclipse_lat, eclipse_lon),
                        "duration": self._estimate_eclipse_duration(moon, "solar")
                    })
                
                # Lunar eclipse: Planet between moon and sun
                lunar_eclipse_alignment = self._check_lunar_eclipse(moon_position, subsolar_lon, time)
                
                if lunar_eclipse_alignment < 5:  # Degrees of alignment tolerance
                    eclipse_events.append({
                        "type": "Lunar Eclipse",
                        "time": time,
                        "moon": moon.name,
                        "visibility": "Night side of planet",
                        "duration": self._estimate_eclipse_duration(moon, "lunar")
                    })
                
                # Check for minimoon eclipses (either minimoon eclipsing parent moon or vice versa)
                for minimoon in moon.minimoons:
                    minimoon_position = minimoon.get_position(time)
                    
                    # Check if minimoon is between planet and parent moon
                    # This would cause an eclipse on the moon's surface
                    if self._check_minimoon_eclipse(moon_position, minimoon_position, time):
                        eclipse_events.append({
                            "type": "Minimoon Eclipse on Moon Surface",
                            "time": time,
                            "moon": moon.name,
                            "minimoon": minimoon.name,
                            "duration": self._estimate_minimoon_eclipse_duration(minimoon, moon)
                        })
        
        return eclipse_events
    
    def _check_minimoon_eclipse(self, moon_position, minimoon_position, time):
        """
        Check if minimoon is in position to cause an eclipse on parent moon
        
        Parameters:
        moon_position (float): Moon orbital position in radians
        minimoon_position (float): Minimoon orbital position in radians
        time (float): Current time
        
        Returns:
        bool: True if an eclipse is occurring, False otherwise
        """
        # Very simplified check - in reality we'd need full 3D geometry
        # We're just checking if minimoon is in a certain phase of its orbit
        # relative to the parent moon's position
        
        # Convert positions to relative angle
        relative_angle = (minimoon_position - moon_position) % (2 * np.pi)
        
        # Eclipse occurs if minimoon is roughly in conjunction or opposition
        # (this is a very simplified model)
        return (relative_angle < 0.1 or 
                abs(relative_angle - np.pi) < 0.1 or 
                abs(relative_angle - 2 * np.pi) < 0.1)
    
    def _estimate_minimoon_eclipse_duration(self, minimoon, moon):
        """
        Estimate duration of minimoon eclipse
        
        Parameters:
        minimoon (MiniMoon): Minimoon object
        moon (Moon): Parent moon object
        
        Returns:
        float: Estimated duration in hours
        """
        # Simplified calculation
        angular_size_ratio = minimoon.angular_size_degrees / moon.angular_size_degrees
        orbital_period_hours = minimoon.orbital_period * 24
        
        # Rough estimate: proportional to orbital period and angular size
        return orbital_period_hours * angular_size_ratio / 10
    
    def _check_solar_eclipse(self, moon_position, subsolar_lon, time):
        """
        Check if moon is aligned for a solar eclipse
        
        Parameters:
        moon_position (float): Moon orbital position in radians
        subsolar_lon (float): Longitude of subsolar point
        time (float): Current time
        
        Returns:
        float: Angle of alignment in degrees (0 = perfect alignment)
        """
        # Convert moon orbital position to longitude on planet
        moon_lon = (math.degrees(moon_position) + 180) % 360
        
        # Calculate alignment angle (how close moon is to being between planet and sun)
        alignment = abs((moon_lon - subsolar_lon + 180) % 360 - 180)
        return alignment
    
    def _check_lunar_eclipse(self, moon_position, subsolar_lon, time):
        """
        Check if moon is aligned for a lunar eclipse
        
        Parameters:
        moon_position (float): Moon orbital position in radians
        subsolar_lon (float): Longitude of subsolar point
        time (float): Current time
        
        Returns:
        float: Angle of alignment in degrees (0 = perfect alignment)
        """
        # Convert moon orbital position to longitude on planet
        moon_lon = (math.degrees(moon_position) + 180) % 360
        
        # For lunar eclipse, moon should be opposite the sun
        alignment = abs((moon_lon - (subsolar_lon + 180) % 360 + 180) % 360 - 180)
        return alignment
    
    def _calculate_eclipse_location(self, subsolar_lat, subsolar_lon, moon_position):
        """
        Calculate the location on planet where a solar eclipse would be visible
        
        Parameters:
        subsolar_lat (float): Latitude of subsolar point
        subsolar_lon (float): Longitude of subsolar point
        moon_position (float): Moon orbital position
        
        Returns:
        tuple: (latitude, longitude) where eclipse is centered
        """
        # Step 1: Find the subsolar point on the planet
        # This is where the sun is directly overhead
        # We assume the planet is a perfect sphere for simplicity
        planet_radius = self.planet_radius
        subsolar_x = planet_radius * math.cos(math.radians(subsolar_lat)) * math.cos(math.radians(subsolar_lon))
        subsolar_y = planet_radius * math.cos(math.radians(subsolar_lat)) * math.sin(math.radians(subsolar_lon))
        subsolar_z = planet_radius * math.sin(math.radians(subsolar_lat))
        # Step 2: Find the moon's position relative to the subsolar point
        # This is a simplified calculation assuming a circular orbit
        moon_angle = moon_position
        moon_x = planet_radius * math.cos(moon_angle)
        moon_y = planet_radius * math.sin(moon_angle)
        moon_z = 0
        # Step 3: Find the midpoint between the subsolar point and moon
        midpoint_x = (subsolar_x + moon_x) / 2
        midpoint_y = (subsolar_y + moon_y) / 2
        midpoint_z = (subsolar_z + moon_z) / 2
        # Step 4: Convert the midpoint back to latitude and longitude
        midpoint_lat = math.degrees(math.asin(midpoint_z / planet_radius))
        midpoint_lon = (math.degrees(math.atan2(midpoint_y, midpoint_x)) + 360) % 360
        # Return the midpoint as the eclipse location
        return (midpoint_lat, midpoint_lon)
    
    def _estimate_eclipse_duration(self, moon, eclipse_type):
        """
        Estimate the duration of an eclipse
        
        Parameters:
        moon (Moon): Moon object
        eclipse_type (str): "solar" or "lunar"
        
        Returns:
        float: Estimated duration in hours
        """
        # Simplified duration calculation
        if eclipse_type == "solar":
            # Solar eclipse duration depends on moon's angular size and orbital speed
            angular_size_factor = moon.angular_size_degrees / 0.5  # Compare to Earth's moon (~0.5°)
            orbital_speed_factor = 27.3 / moon.orbital_period  # Compare to Earth's moon
            
            # Base duration for solar eclipse (typically 2-3 hours for totality + partial phases)
            return 3 * angular_size_factor / orbital_speed_factor
        else:
            # Lunar eclipses typically last longer (~3-4 hours)
            return 4
    
    def __str__(self):
        output = f"Moon System for {self.planet_name}\n"
        output += f"Number of moons: {len(self.moons)}\n"
        
        for i, moon in enumerate(self.moons):
            output += f"\nMoon {i+1}:\n"
            moon_str = str(moon).replace('Moon: ', '')
            output += textwrap.indent(moon_str, "  ") + "\n"
            
            # Add minimoon information
            if moon.minimoons:
                output += f"  This is a binary system with {len(moon.minimoons)} minimoon(s):\n"
                for j, minimoon in enumerate(moon.minimoons):
                    output += f"    Minimoon {j+1}:\n"
                    minimoon_str = minimoon.__str__().replace('MiniMoon: ', '')
                    output += textwrap.indent(minimoon_str, "      ") + "\n"
        
        if self.has_rings:
            output += f"\nRing System:\n"
            output += f"  Inner Radius: {self.ring_inner_radius:.1f} km\n"
            output += f"  Outer Radius: {self.ring_outer_radius:.1f} km\n"
        
        return output


"""
Key Time Conversion Functions
- nexus_to_absolute(year, day, hour): Convert Nexus date to absolute time
- absolute_to_planet_time(abs_time, planet): Convert absolute time to local planet time
- planet_to_planet_time(from_planet, to_planet, year, day, hour): Convert between planets
"""
def nexus_to_absolute(year, day, hour=12):
    """
    Convert a Nexus date to absolute time in Earth years
    
    Parameters:
    year (int): Current year
    day (int): Current day of year (0-359)
    hour (int): Current hour (0-23)
    
    Returns:
    float: Absolute time in Earth days since reference point
    """
    return year + day / 360 + hour / (360 * 24)

def absolute_to_planet_time(abs_time, planet):
    """
    Convert absolute time to local time on a planet
    
    Parameters:
    abs_time (float): Absolute time in Earth days since reference point
    planet (Planet): Planet object to convert time to
    
    Returns:
    tuple: (year, day, hour, minute) on the planet
    """
    # Calculate Nexus date
    year = int(abs_time)
    day = int((abs_time - year) * 360)
    hour = int((abs_time - year - day / 360) * 360 * 24)
    minute = int((abs_time - year - day / 360 - hour / (360 * 24)) * 360 * 24 * 60)
    
    # Convert to local time
    local_time = planet.get_local_time(year, day, hour, minute, 0)
    return local_time

def planet_to_planet_time(from_planet, to_planet, year, day, hour=12):
    """
    Convert a time from one planet to another
    
    Parameters:
    from_planet (Planet): Origin planet
    to_planet (Planet): Destination planet
    year (int): Current year
    day (int): Current day of year (0-359)
    hour (int): Current hour (0-23)
    
    Returns:
    tuple: (year, day, hour, minute) on the destination planet
    """
    # Convert to absolute time
    abs_time = nexus_to_absolute(year, day, hour)
    
    # Convert to local time on the origin planet
    local_time = absolute_to_planet_time(abs_time, from_planet)
    
    # Convert to local time on the destination planet
    destination_time = to_planet.get_local_time(*local_time, 0)
    return destination_time

