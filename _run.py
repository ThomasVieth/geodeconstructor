"""

"""

## python imports

from argparse import ArgumentParser
from datetime import datetime, timedelta
from enum import IntEnum
from os.path import abspath, dirname, join

## internal imports

from geodeconstructor.history.json import generate_location_history_json
from geodeconstructor.history.locations import iter_unique_country_path

## Argument parsing

argument_parser = ArgumentParser()
argument_parser.add_argument(
    "filepath",
    help="The path to the `Location History.json` exported by Google Takeout.",
    type=str
)

argument_parser.add_argument(
    "-a",
    "--attr",
    help="The attribute to diff upon when determining changes in position.",
    type=str,
    default="country"
)
argument_parser.add_argument(
    "-e",
    "--export",
    help="The file type that should be exported (stdout/xml/csv/kml).",
    type=str,
    default="stdout"
)

argument_parser.add_argument(
    "--startdate",
    help="The date of which to start parsing from; in ISO format.",
    type=str
)
argument_parser.add_argument(
    "--enddate",
    help="The date of which to stop parsing at; in ISO format.",
    type=str
)

## Output handling

class Action(IntEnum):
    ENTERING = 0
    EXITING = 1

def print_node(action, node, timedelta):
    """Prints the state of the action and the location city/country."""
    if action == Action.ENTERING:
        print(f"Entering {node.city}, {node.country} at {timedelta}.")
    elif action == Action.EXITING:
        print(f"Exiting {node.city}, {node.country} after {timedelta}.")

def write_node_csv(action, node, timedelta, filepointer):
    """Writes the state of the action and the location city/country to CSV."""
    if action == Action.ENTERING:
        # Using '' instead of "" due to use of them within CSV output.
        filepointer.write(
            f'"Entering","{node.city}","{node.country}","{timedelta}",,\n'
        )
    elif action == Action.EXITING:
        # Using '' instead of "" due to use of them within CSV output.
        filepointer.write(
            f'"Exiting","{node.city}","{node.country}","","{timedelta}",\n'
        )

def write_node_kml(action, node, timedelta, kml_doc, kml_styles):
    """Writes the state of the action and the location city/country to KML."""
    if action == Action.ENTERING:
        # Ugly way of achieving this, however KML library doesn't support style
        #  as kwargs...
        point = kml_doc.newpoint(
            name=f"Entering {node.city}, {node.country}",
            description=str(timedelta),
            coords=[node.as_tuple()]
        )
        point.iconstyle = kml_styles[0]

    elif action == Action.EXITING:
        # Ugly way of achieving this, however KML library doesn't support style
        #  as kwargs...
        point = kml_doc.newpoint(
            name=f"Exiting {node.city}, {node.country}",
            description=str(timedelta),
            coords=[node.as_tuple()]
        )
        point.iconstyle = kml_styles[1]

# Actually handling script usage.
# Only run if directly run by user.
if __name__ == "__main__":
    # Handle argument parsing.
    args = argument_parser.parse_args()

    # Validate the JSON provided is a Location History export.
    json = generate_location_history_json(args.filepath)

    if args.startdate and args.enddate:
        date1Ms = datetime.fromisoformat(args.startdate).timestamp() * 1000
        date2Ms = datetime.fromisoformat(args.enddate).timestamp() * 1000

        # Generate dynamic function to handle filtering upon timestamps by
        #  milliseconds.
        def _new_filter(item):
            value = int(item.get("timestampMs", 0))
            if value == 0 or value > date2Ms or value < date1Ms:
                return False
            return True

    # Start the iteration... and return in generator form.
        generator = iter_unique_country_path(json["locations"], _new_filter)
    else:
        generator = iter_unique_country_path(json["locations"])

    # Upon requesting CSV, open the CSV file for writing.
    if args.export == "csv":
        csv = open(
            join(dirname(args.filepath), "Location History.csv"),
            "w+"
        )
        # Using '' instead of "" due to use of them within CSV output.
        csv.write('"Action","City","Country","DateTime","TimeDelta",\n')
    elif args.export == "kml":
        try:
            from simplekml import Kml, Style, IconStyle, ItemIcon
        except ImportError:
            raise ImportError(f"To export as KML, use `pip install simplekml`.")
        kml = Kml(name=f"Location History {args.attr.capitalize()} Changes")
        kml_styles = [
            IconStyle(
                color="#00FF00", # GREEN
                icon=ItemIcon(
                    href="http://maps.google.com/mapfiles" \
                    "/kml/shapes/placemark_circle.png"
                )
            ),
            IconStyle(
                color="#FF0000", # RED
                icon=ItemIcon(
                    href="http://maps.google.com/mapfiles" \
                    "/kml/shapes/placemark_circle.png"
                )
            )
        ]

    # Start iterating over the generator.
    # The generator will output the previous and next node when detecting a change in
    #  attribute, whether this be on city or country change.
    for prev_node, prev_timestampMs, next_node, next_timestampMs in generator:
        # Case when printing out first node.
        if prev_node is None:
            next_datetime = datetime.fromtimestamp(next_timestampMs / 1000)
            if args.export == "stdout":
                print_node(Action.ENTERING, next_node, next_datetime)
            elif args.export == "csv":
                write_node_csv(Action.ENTERING, next_node, next_datetime, csv)
            elif args.export == "kml":
                write_node_kml(Action.ENTERING, next_node, next_datetime, kml,
                    kml_styles)
        else:
            time_spent = timedelta(milliseconds=next_timestampMs - prev_timestampMs)
            if args.export == "stdout":
                print_node(Action.EXITING, prev_node, time_spent)
            elif args.export == "csv":
                write_node_csv(Action.EXITING, prev_node, time_spent, csv)
            elif args.export == "kml":
                write_node_kml(Action.EXITING, prev_node, time_spent, kml,
                    kml_styles)

            next_datetime = datetime.fromtimestamp(next_timestampMs / 1000)
            if args.export == "stdout":
                print_node(Action.ENTERING, next_node, next_datetime)
            elif args.export == "csv":
                write_node_csv(Action.ENTERING, next_node, next_datetime, csv)
            elif args.export == "kml":
                write_node_kml(Action.ENTERING, next_node, next_datetime, kml,
                    kml_styles)

    # Close up any opened files.
    if args.export == "csv":
        csv.close()
    elif args.export == "kml":
        kml.save(join(dirname(args.filepath), "Location History.kml"))