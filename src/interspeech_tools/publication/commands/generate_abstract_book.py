import logging
import argparse
import pathlib
from re import A

# Templating / rendering
from ..books.theme import generate_theme_file
import shutil
import importlib.resources
import jinja2

# ISCA Lib
from isca.io.cmt import CMTSerialiser

# Helpers
from ..books.utils import compile
from ..books.abstract import AbstractBookProcessor
from ..books.jinja_helpers import configure_latex_jinja


#################################################################################################
## Entry points
#################################################################################################


def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_abstract_book",
        help="generate (latex code and compile it) the abstract book",
    )

    # Add options
    parser.add_argument("-b", "--bootstrap", action="store_true", help="Add all elements to generate the abstract book")
    parser.add_argument("-c", "--classname", default="interspeech", type=str, help="The LaTeX class name")
    parser.add_argument(
        "-C",
        "--compile",
        action="store_true",
        help="Compile the book (use latexmk if available, else use lualatex. pdflatex and xelatex are not supported)",
    )
    parser.add_argument(
        "-p", "--pdf-path", type=str, default=None, help="The alternative directory containing the PDF files (flatten!)"
    )
    parser.add_argument("-P", "--pdf-metadata", action="store_true", help="Extract the metadata from the PDF")
    parser.add_argument("-f", "--format", type=str, default="cmt", help="The format of the input formation")

    # Add arguments
    parser.add_argument("conf_input", help="The input metadata file")
    parser.add_argument("abstract_book_root_dir", help="The abstract book latex file")

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    logger = logging.getLogger(__name__)
    conf_path = pathlib.Path(args.conf_input)
    abstract_book_root_dir = pathlib.Path(args.abstract_book_root_dir)
    generated_elements_dir = abstract_book_root_dir / "auto"
    generated_elements_dir.mkdir(exist_ok=True, parents=True)

    colour_file = None
    if args.bootstrap:
        cls_file = abstract_book_root_dir / "interspeech.cls"
        if cls_file.exists():
            raise Exception(f"The class file {cls_file} already exists, delete it if you want to bootstrap/reset")

        template_res = importlib.resources.files("interspeech_tools.publication").joinpath(
            "resources/abstract_book/interspeech.cls"
        )
        with importlib.resources.as_file(template_res) as template_file:
            shutil.copy(template_file, cls_file)

        colour_file = cls_file.parent / "theme/colours.tex"
        if colour_file.exists():
            raise Exception(f"The colour file {colour_file} already exists, delete it if you want to bootstrap/reset")
        colour_file.parent.mkdir(exist_ok=True, parents=True)

    # Load conference
    conf = None
    serialiser = None
    if args.format == "cmt":
        serialiser = CMTSerialiser(args.pdf_metadata, False)
    else:
        raise NotImplementedError(f"The format {args.format} is not supported")
    conf = serialiser.load(conf_path)
    conf.resolve_author_paper_association()

    # Generate the them
    if colour_file is not None:

        template_loader = jinja2.PackageLoader("interspeech_tools.publication", "resources/abstract_book")
        template_engine = configure_latex_jinja(template_loader)
        generate_theme_file(conf, colour_file, template_engine)

    processor = AbstractBookProcessor(conf)
    processor.process(generated_elements_dir)

    if args.bootstrap:
        processor.generate_entry_point(abstract_book_root_dir / "main.tex")

    # Prepare content template
    if args.compile:
        compile(abstract_book_root_dir / "main.tex")
