import argparse
import pathlib

# ISCA Lib
from isca.io.archive import ArchiveInputSerialiser
from ...io.cmt import CMTSerialiser


def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_archive",
        help="generate the ISCA archive material",
    )

    # Add options
    parser.add_argument("-f", "--format", type=str, default="cmt", help="The format of the input formation")

    # Add arguments
    parser.add_argument("conf_input", help="The input metadata file")
    parser.add_argument("output_root_dir", help="The output directory containing the material to be imported in the ISCA Archive")

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    conf_path = pathlib.Path(args.conf_input)
    output_root_dir = pathlib.Path(args.output_root_dir)

    # Load conference
    conf = None
    serialiser = None
    if args.format == "cmt":
        serialiser = CMTSerialiser(False, False)
    else:
        raise NotImplementedError(f"The format {args.format} is not supported")
    conf = serialiser.load(conf_path)

    archive_generator = ArchiveInputSerialiser()
    archive_generator.dump(conf, output_root_dir)
