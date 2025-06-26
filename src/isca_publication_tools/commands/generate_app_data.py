import argparse
import pathlib

# ISCA Lib
from isca.io.cmt import CMTSerialiser
from ..app.compass import CompassDataGenerator


def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_app_data",
        help="generate the data for the application",
    )

    # Add options
    parser.add_argument("-f", "--format", type=str, default="cmt", help="The format of the input formation")

    # Add arguments
    parser.add_argument("conf_input", help="The input metadata file")
    parser.add_argument("app_data_dir", help="The output directory containing the application data")

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    conf_path = pathlib.Path(args.conf_input)
    app_data_dir = pathlib.Path(args.app_data_dir)

    # Load conference
    conf = None
    serialiser = None
    if args.format == "cmt":
        serialiser = CMTSerialiser(True, False)
    else:
        raise NotImplementedError(f"The format {args.format} is not supported")
    conf = serialiser.load(conf_path)

    app_data_generator = CompassDataGenerator(conf)
    app_data_generator.generate_data(app_data_dir)
