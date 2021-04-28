"""
https://github.com/richardpenman/reverse_geocode/

This module will use SciPy and data from geonames.org
 to identify the closest city to the geolocation
 coordinates provided.

The module has been adjusted to make use of Python's
 built-ins more effectivel, updated to work with
 newer versions of Python and altered "code-wise" to
 match PEP8 code standards.
"""

## python imports

import csv
import os
import sys
from zipfile import ZipFile

# Handle Win32 Excel setups.
if sys.platform == 'win32':
    csv.field_size_limit(2**31-1)
else:
    csv.field_size_limit(sys.maxsize)

# Handle urllib from older Python versions.
try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

## third-party packages

# Raise error upon loading with missing SciPy.
try:
    from scipy.spatial import cKDTree as KDTree
except ImportError:
    raise ImportError(
        "reverse_geocode requires the scipy library to perform coordinate " \
        "lookups."
    )

## __all__ declaration

__all__ = (
    "GeocodeData",
    "reverse_coordinates",
    "search"
)

## globals

# Location of Geocode CSVs.
GEOCODE_URL = 'http://download.geonames.org/export/dump/cities1000.zip'
GEOCODE_FILENAME = 'cities1000.txt'

## Singleton declaration

class Singleton(type):
    """Forces a parent class to become a singleton in behaviour.
    The parent class must contain a class attribute named `_instance` for
     the single instance to be stored within. See :class:`GeocodeData` for
     an example.
    """

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

## GeocodeData declaration

class GeocodeData(metaclass=Singleton):
    """GeocodeData loads country-city geolocations into memory in preparation
    to classify a coordinates nearest city.

    """
    _instance = None

    def __init__(
        self,
        geocode_filename='geocode.csv',
        country_filename='countries.csv'
    ):
        coordinates, self.locations = self.extract(rel_path(geocode_filename))
        self.tree = KDTree(coordinates)
        self.countries = {}
        self.load_countries(rel_path(country_filename))


    def load_countries(self, country_filename):
        """Load a map of country code to name
        """
        for code, name in csv.reader(open(country_filename)):
            self.countries[code] = name

    def query(self, coordinates):
        """Find closest match to this list of coordinates
        """
        try:
            distances, indices = self.tree.query(coordinates, k=1)
        except:
            raise ValueError(
                "Could not identify from coordinates {}".format(
                    coordinates
                )
            )
        else:
            if type(indices) == int:
                return [{}]

            results = [self.locations[index] for index in indices]
            for result in results:
                result['country'] = self.countries.get(
                    result['country_code'],
                    ''
                )
            return results


    def download(self):
        """Download geocode file
        """
        local_filename = os.path.abspath(os.path.basename(GEOCODE_URL))
        if not os.path.exists(local_filename):
            urlretrieve(GEOCODE_URL, local_filename)
        return local_filename


    def extract(self, local_filename):
        """Extract geocode data from zip
        """
        if os.path.exists(local_filename):
            # open compact CSV
            rows = csv.reader(open(local_filename, encoding='utf8'))
        else:
            if not os.path.exists(GEOCODE_FILENAME):
                # remove GEOCODE_FILENAME to get updated data
                local_filename = self.download()
                z = ZipFile(local_filename)
                open(GEOCODE_FILENAME, 'wb').write(z.read(GEOCODE_FILENAME))

            # extract coordinates into more compact CSV for faster loading
            writer = csv.writer(open(local_filename, 'w', encoding='utf8'))
            rows = []
            for row in csv.reader(open(GEOCODE_FILENAME), delimiter='\t'):
                latitude, longitude = row[4:6]
                country_code = row[8]
                if latitude and longitude and country_code:
                    city = row[1]
                    row = latitude, longitude, country_code, city
                    writer.writerow(row)
                    rows.append(row)

        # load a list of known coordinates and corresponding locations
        coordinates, locations = [], []
        for latitude, longitude, country_code, city in rows:
            coordinates.append((latitude, longitude))
            locations.append(dict(country_code=country_code, city=city))
        return coordinates, locations

## Helper function declaration

def rel_path(filename):
    """Return the path of this filename relative to the current script
    """
    return os.path.join(os.getcwd(), os.path.dirname(__file__), filename)

## Reversing functions declarations

def reverse_coordinates(coordinate):
    """Search for closest known location to this coordinate.

    :param coordinate: A tuple of (latitude, longitude) coordinates.
    :type coordinate: tuple
    """
    gd = GeocodeData()
    return gd.query([coordinate])[0]


def search(coordinates):
    """Search for closest known locations to these coordinates.

    :param coordinates: A list of tuples of (latitude, longitude) coordinates.
    :type coordinates: list[tuple]
    """
    gd = GeocodeData()
    return gd.query(coordinates)