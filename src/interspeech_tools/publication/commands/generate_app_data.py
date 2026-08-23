import argparse
import pathlib

# ISCA Lib
from ...conf import Config
from ...io import instanciate_serialiser
from ..app.compass import CompassDataGenerator


def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_app_data",
        help="generate the data for the application",
    )

    # Add arguments
    parser.add_argument("conf_input", help="The input configuraton file required for the conference")
    parser.add_argument("app_data_dir", help="The output directory containing the application data")

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    config = Config(pathlib.Path(args.conf_input))
    app_data_dir = pathlib.Path(args.app_data_dir)

    # Load conference
    serialiser = instanciate_serialiser(config, args.debug)
    conference = serialiser.load()

    app_data_generator = CompassDataGenerator(conference)
    app_data_generator.generate_data(app_data_dir)
