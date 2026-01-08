import argparse
import pathlib

# ISCA Lib
from isca.io.archive import ArchiveInputSerialiser

# Local helpers
from ...conf import Config
from ...io import instanciate_serialiser


def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_archive",
        help="generate the ISCA archive material",
    )

    # Add options
    parser.add_argument("-b", "--booklet", type=str, default=None, help="The booklet to add to the archive")
    parser.add_argument("-f", "--format", type=str, default="cmt", help="The format of the input formation")

    # Add arguments
    parser.add_argument("conf_input", help="The input configuraton file required for the conference")
    parser.add_argument("output_root_dir", help="The output directory containing the material to be imported in the ISCA Archive")

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    config = Config(pathlib.Path(args.conf_input))
    output_root_dir = pathlib.Path(args.output_root_dir)

    # Load conference
    serialiser = instanciate_serialiser(config)
    conference = serialiser.load()

    booklet_path = None
    if args.booklet is not None:
        booklet_path = pathlib.Path(args.booklet)
        assert booklet_path.is_file(), f"The booklet ({booklet_path}) neither exists nor is a file"

    archive_generator = ArchiveInputSerialiser()
    archive_generator.dump(conference, output_root_dir, booklet_path=booklet_path)
