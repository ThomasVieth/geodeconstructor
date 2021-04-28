"""

"""

## python imports

from dataclasses import dataclass
from datetime import datetime
from locale import getdefaultlocale
from typing import Any

## external imports

from .tools import classproperty

# Check if the geopy library is available before trying relative imports.
use_geopy = True

from .reverse_geocode import reverse_coordinates

try:
    from geopy.geocoders import Nominatim
except ImportError:
    use_geopy = False

## __all__ declaration

__all__ = ("Coordinate", )

## globals

# Used by openstreetmaps for correctly handling language.
locale = getdefaultlocale()[:2]

## Coordinate declaration

@dataclass
class Coordinate:
    """Stores geolocation coordinates to be reversed to address later.

    :param latitude: The latitude coordinate to initialize with.
    :type latitude: float

    :param longitude: The longitude coordinate to initialize with.
    :type longitude: float
    """
    latitude: float
    longitude: float
    city: str = ''
    country: str = ''

    _geolocator: Any = None

    @classmethod
    def init_with_georeverse(cls, latitude: float, longitude: float):
        """Initializes the Coordinates instance and then calls the `reverse`
        function.
        """
        instance = cls(latitude, longitude)
        instance.reverse()
        return instance

    def as_tuple(self):
        """Returns the longitude and latitude as a coordinate tuple for KML."""
        return (self.longitude, self.latitude)

    def reverse(self):
        """Reverses the geolocation coordinates and renders them in
        city/country attributes."""
        # On reverse_geocode library available, use scipy to map best to 
        #  dataset. Prioritise this as is much quicker, lacking the use of HTTP
        #  protocol.
        if not use_geopy:
            # Reverse the coordinates to address using dataset.
            location = reverse_coordinates((self.latitude, self.longitude))
            self.country, self.city = location["country"], location["city"]

        # On geopy library available, use openstreetmaps api. Much slower as
        #  sends HTTP requests to their REST API.
        else:
            # Reverse the coordinates to address using local language.
            location = self.geolocator.reverse(
                f"{self.latitude:0.6f}, {self.longitude:0.6f}", language=locale
            )
            location_split = list(
                map(
                    lambda x: x.strip(' '),
                    location.address.split(',')
                )
            )
            self.country, self.city = location_split[-1], location_split[1:-2]

    @classproperty
    def geolocator(cls):
        # Implementation of a singleton for geopy's openstreetmaps interface.
        if not cls._geolocator:
            cls._geolocator = Nominatim(user_agent="geo-deconstructor")
        return cls._geolocator