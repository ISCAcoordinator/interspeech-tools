import logging
import argparse
import pathlib
import shutil

# Templating / rendering
import importlib.resources
import jinja2

# ISCA Lib
from isca.model.event import Conference
from isca.model.item import Paper
from isca.model.person import Person
from isca.model.program import PresentationSession, Presentation

# Helpers
from ...conf import Config
from ...io import instanciate_serialiser
from ..books.utils import compile
from ..books.jinja_helpers import configure_latex_jinja
from ..books.theme import generate_theme_file


def list_elts(conf: Conference, ignore_sessions: bool) -> dict[str, Paper] | dict[str, Presentation]:
    if ignore_sessions:
        return conf.papers
    else:
        presentations = dict()
        for cur_session in conf.sessions:
            if not isinstance(cur_session, PresentationSession):
                continue
            if cur_session.presentations is not None:
                for cur_presentation in cur_session.presentations:
                    if cur_presentation.presented_paper is not None:
                        presentations[cur_presentation.presented_paper.id] = cur_presentation
        return presentations


#################################################################################################
## Entry points
#################################################################################################


def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_validation_book",
        help="generate (latex code and compile it) the validation book to be sent to the authors",
    )

    # Add options
    parser.add_argument("-b", "--bootstrap", action="store_true", help="Add all elements to generate the validation book")
    parser.add_argument("-c", "--classname", default="interspeech", type=str, help="The LaTeX class name")
    parser.add_argument(
        "--compile-tool",
        default="none",
        help="tools to compile the book (none: no compilation, auto: use what is available, latexmk, lualtex) [none]",
    )
    parser.add_argument("-n", "--no-sessions", action="store_true", help="Do not use the sessions, use only the papers")
    parser.add_argument(
        "-p", "--pdf-path", type=str, default=None, help="The alternative directory containing the PDF files (flatten!)"
    )
    parser.add_argument("-P", "--pdf-metadata", action="store_true", help="Extract the metadata from the PDF")
    parser.add_argument("-f", "--format", type=str, default="cmt", help="The format of the input formation")

    # Add arguments
    parser.add_argument("conf_input", help="The input metadata file")
    parser.add_argument("val_book_directory", help="The validation book output directory")

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    logger = logging.getLogger(__name__)
    config = Config(pathlib.Path(args.conf_input))
    val_book_directory = pathlib.Path(args.val_book_directory)
    val_book_directory.mkdir(exist_ok=True, parents=True)

    abstract_template_loader = jinja2.PackageLoader("interspeech_tools.publication", "resources/abstract_book")
    abstract_template_engine = configure_latex_jinja(abstract_template_loader)
    validation_template_loader = jinja2.PackageLoader("interspeech_tools.publication", "resources/validation_book")
    validation_template_engine = configure_latex_jinja(validation_template_loader)
    colour_file = None
    if args.bootstrap:
        # Copy class
        cls_file = val_book_directory / "interspeech.cls"
        if cls_file.exists():
            raise Exception(f"The class file {cls_file} already exists, delete it if you want to bootstrap/reset")

        template_res = importlib.resources.files("interspeech_tools.publication").joinpath(
            "resources/validation_book/interspeech.cls"
        )
        with importlib.resources.as_file(template_res) as template_file:
            shutil.copy(template_file, cls_file)

        # Copy insructions
        instruction_file = val_book_directory / "draft_booklet_instructions.tex"
        if instruction_file.exists():
            raise Exception(f"The instruction file{instruction_file} already exists, delete it if you want to bootstrap/reset")

        template_res = importlib.resources.files("interspeech_tools.publication").joinpath(
            "resources/validation_book/draft_booklet_instructions.tex"
        )
        with importlib.resources.as_file(template_res) as template_file:
            shutil.copy(template_file, instruction_file)

        # Copy instruction figures
        INSTRUCTION_FIGURES = [
            "figures/abstract_book.png",
            "figures/archive.png",
            "figures/author_annotated.png",
            "figures/author.png",
            "figures/validation.png",
        ]
        for figure_file_name in INSTRUCTION_FIGURES:
            figure_file = val_book_directory / figure_file_name
            if figure_file.exists():
                raise Exception(f"The figure {figure_file} already exists, delete it if you want to bootstrap/reset")
            figure_file.parent.mkdir(exist_ok=True, parents=True)
            template_res = importlib.resources.files("interspeech_tools.publication").joinpath(
                f"resources/validation_book/{figure_file_name}"
            )
            with importlib.resources.as_file(template_res) as template_file:
                shutil.copy(template_file, figure_file)

        colour_file = cls_file.parent / "theme/colours.tex"
        if colour_file.exists():
            raise Exception(f"The colour file {colour_file} already exists, delete it if you want to bootstrap/reset")
        colour_file.parent.mkdir(exist_ok=True, parents=True)

    # Load conferenceerence
    serialiser = instanciate_serialiser(config)
    conference = serialiser.load()
    conference.resolve_author_paper_association()

    # Generate the them
    if colour_file is not None:
        generate_theme_file(conference, colour_file, abstract_template_engine)

    # Prepare content template
    def list_papers(author: Person) -> list[Paper]:
        return conference.list_papers(author)

    validation_template_engine.filters["list_papers"] = list_papers

    # Render author index
    validation_author_index_template = validation_template_engine.get_template("author_index.tex.jinja2")
    val_book_entry_file = val_book_directory / "author_index.tex"
    with open(val_book_entry_file, "w") as f:
        f.write(validation_author_index_template.render(authors=conference.authors))

    # Render paper index
    validation_paper_index_template = validation_template_engine.get_template("paper_index.tex.jinja2")
    val_book_entry_file = val_book_directory / "paper_index.tex"
    with open(val_book_entry_file, "w") as f:
        f.write(validation_paper_index_template.render(papers=list_elts(conference, args.no_sessions)))

    # Render entry file
    validation_main_template = validation_template_engine.get_template("main.tex.jinja2")
    val_book_entry_file = val_book_directory / "validation_book.tex"
    with open(val_book_entry_file, "w") as f:
        f.write(validation_main_template.render(classname=args.classname))

    # Compile if wanted
    if args.compile_tool != "none":
        compile(val_book_entry_file, args.compile_tool)
