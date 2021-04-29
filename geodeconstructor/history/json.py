"""

"""

## python imports

from functools import partial
from json import load, loads
from os import walk
from os.path import isdir, isfile, join

## __all__ declaration

__all__ = (
    "generate_location_history_json",
    "generate_semantic_history_json",
)

## open and validate json files

def _generate_json_and_validate(key_name: str, filepath: str):
    if not isfile(filepath):
        raise FileNotFoundError(f"{filepath} could not be identified.")

    with open(filepath) as fp:
        json = load(fp)

    if key_name not in json.keys():
        raise ValueError(f"Cannot find {key_name} key within JSON provided.")

    return json

generate_location_history_json = partial(
    _generate_json_and_validate,
    "locations"
)
generate_semantic_history_json = partial(
    _generate_json_and_validate,
    "timelineObject"
)

## find all semantic json files

def generate_semantic_history_json(directory: str):
    if not isdir(directory):
        raise FileNotFoundError(
            f"{directory} could not be identified as a directory."
        )

    for subdir, _, filenames in walk(directory):
        for filename in filenames:
            filepath = join(directory, subdir, filename)
            yield generate_semantic_history_json(filepath)