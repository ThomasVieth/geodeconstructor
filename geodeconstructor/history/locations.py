"""

"""

## python imports

from functools import partial
from typing import Any, Sequence

## library imports

from ..components import Coordinate

## __all__ declaration

__all__ = (
    "iter_unique_path_by_attribute",
    "iter_unique_city_path",
    "iter_unique_country_path"
)

## generator - iter through location list and identify when country changes

def _default_filter_func(item: Any):
    """Filter function that verifies timestampMs key is available."""
    return item.get("timestampMs", 0) != 0

def _default_key_func(item: Any):
    """Key function that orders based upon timestampMs value."""
    return item.get("timestampMs")

def iter_unique_path_by_attribute(attribute: str, locations: Sequence[Any],
    filter_func=_default_filter_func, key_func=_default_key_func):
    """Generates a tuple set of unique visits to the attribute specified,
    yielding the previous and next location on each iteration. The first
    iteration will return None, None for the previous node and time. After this,
    the previous node/time and next node/time will be present.

    :param attribute: The attribute inside the location object to compare. e.g.
    city, country
    :type attribute: str

    :param locations: The locations list from the Location History.json
    :type locations: list[dict]

    :param filter_func: The filter function to apply to the list before
    iteration. Default: verifies the timestamp is available.
    :type func: func(item)

    :param key_func: The key function to apply during the sorting process,
    typically used to sort the list in chronological order.
    :type key_func: func(item)
    """
    # Order chronologically and filter non-useful objects.
    locations_chronological = list(
        iter_chronologically(locations, filter_func, key_func)
    )
    # Gather initial data for first iteration.
    initial_location = locations_chronological[0]
    initial_latitude = initial_location["latitudeE7"] / 10000000
    initial_longitude = initial_location["longitudeE7"] / 10000000
    initial_timestamp = int(initial_location["timestampMs"])
    initial_coordinate = Coordinate.init_with_georeverse(initial_latitude,
        initial_longitude)
    yield None, None, initial_coordinate, initial_timestamp

    # Setup stores needed for use during iteration.
    current_coordinate = None
    last_coordinate = initial_coordinate
    last_location = initial_location

    # Ensure we never overflow the list iteration by gathering the length.
    end_index = len(locations_chronological)
    for index in range(1, end_index - 1):
        # Initialise the first to be the current location.
        if not current_coordinate:
            current_location = locations_chronological[index]
            current_latitude = current_location["latitudeE7"] / 10000000
            current_longitude = current_location["longitudeE7"] / 10000000
            current_coordinate = Coordinate.init_with_georeverse(
                current_latitude,
                current_longitude
            )

        next_location = locations_chronological[index + 1]
        next_latitude = next_location["latitudeE7"] / 10000000
        next_longitude = next_location["longitudeE7"] / 10000000
        next_coordinate = Coordinate.init_with_georeverse(
            next_latitude,
            next_longitude
        )

        # Compare the attribute provided and yield if necessary.
        if getattr(next_coordinate, attribute) != getattr(current_coordinate, attribute):
            yield (current_coordinate, int(last_location["timestampMs"]),
                next_coordinate, int(next_location["timestampMs"]))
            last_coordinate = next_coordinate
            last_location = next_location

        # Store next value into current for use in prior iteration.
        current_coordinate = next_coordinate
        current_location = next_location

iter_unique_city_path = partial(iter_unique_path_by_attribute, "city")
iter_unique_country_path = partial(iter_unique_path_by_attribute, "country")

## generator - iter location list chronologically

def iter_chronologically(list_object: Sequence[Any], filter_func, key_func):
    """Generates a list of objects from the list of objects provided,
    filtering using the provided filter function and ordering by the
    provided key function.

    :param list_object: A list of objects.
    :type list_object: list

    :param filter_func: A function return True or False on whether should
    be in output list.
    :type filter_func: func(item)

    :param key_func: A function that returns the keyvalue to sort upon.
    :type key_func: func(item)
    """
    list_object = filter(filter_func, list_object)
    yield from sorted(list_object, key=key_func)