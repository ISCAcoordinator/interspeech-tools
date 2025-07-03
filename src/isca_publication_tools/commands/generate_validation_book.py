import logging
import argparse
import pathlib

# Templating / rendering
import jinja2
import shutil
import importlib.resources

# ISCA Lib
from isca.io.cmt import CMTSerialiser
from isca.model.event import Conference
from isca.model.item import Paper, Presentation
from isca.model.session import PresentationSession
from isca.model.person import Person

# Helpers
from ..books.utils import (
    latexify,
    get_sorted_authors,
    get_latexified_authors,
    get_latexified_presenters,
    compile,
    is_presentation,
    has_paper,
)


def list_elts(conf: Conference, ignore_sessions:bool) -> dict[str, Paper] | dict[str, Presentation]:
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
    parser.add_argument(
        "-b", "--bootstrap", action="store_true", help="Add all elements to generate the validation book"
    )
    parser.add_argument("-c", "--classname", default="interspeech", type=str, help="The LaTeX class name")
    parser.add_argument(
        "-C",
        "--compile",
        action="store_true",
        help="Compile the book (use latexmk if available, else use lualatex. pdflatex and xelatex are not supported)",
    )
    parser.add_argument("-n", "--no-sessions", action="store_true", help="Do not use the sessions, use only the papers")
    parser.add_argument(
        "-p", "--pdf-path", type=str, default=None, help="The alternative directory containing the PDF files (flatten!)"
    )
    parser.add_argument("-P", "--pdf-metadata", action="store_true", help="Extract the metadata from the PDF")
    parser.add_argument("-f", "--format", type=str, default="cmt", help="The format of the input formation")

    # Add arguments
    parser.add_argument("conf_input", help="The input metadata file")
    parser.add_argument(
        "val_book_file", help="The validation book latex file"
    )  # TODO: fornow it is latex, it would be nice to have the full blown PDF file directly

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    logger = logging.getLogger(__name__)
    conf_path = pathlib.Path(args.conf_input)
    val_book_file = pathlib.Path(args.val_book_file)
    val_book_file.parent.mkdir(exist_ok=True, parents=True)

    templateLoader = jinja2.PackageLoader("isca_publication_tools", "resources/validation_book")
    jenv_latex = jinja2.Environment(
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        comment_start_string="\\#{",
        comment_end_string="}",
        line_statement_prefix="%%",
        line_comment_prefix="%#",
        trim_blocks=True,
        autoescape=False,
        loader=templateLoader,
    )

    # Set filters
    jenv_latex.filters["latexify"] = latexify
    jenv_latex.filters["has_paper"] = has_paper
    jenv_latex.filters["is_presentation"] = is_presentation
    jenv_latex.filters["sort_authors"] = get_sorted_authors
    jenv_latex.filters["latexified_authors"] = get_latexified_authors
    jenv_latex.filters["presenters"] = get_latexified_presenters

    if args.bootstrap:
        cls_file = val_book_file.parent / "interspeech.cls"
        if cls_file.exists():
            raise Exception(f"The class file {cls_file} already exists, delete it if you want to bootstrap/reset")

        template_res = importlib.resources.files("isca_publication_tools").joinpath(
            "resources/validation_book/interspeech.cls"
        )
        with importlib.resources.as_file(template_res) as template_file:
            print(template_file)
            shutil.copy(template_file, cls_file)

    # Load conference
    conf = None
    serialiser = None
    if args.format == "cmt":
        serialiser = CMTSerialiser(args.pdf_metadata, args.no_sessions)
    else:
        raise NotImplementedError(f"The format {args.format} is not supported")
    conf = serialiser.load(conf_path)
    conf.resolve_author_paper_association()

    # Prepare content template
    def list_papers(author: Person) -> list[Paper]:
        return conf.list_papers(author)

    jenv_latex.filters["list_papers"] = list_papers
    validation_main_template = jenv_latex.get_template("main_template.tex")

    with open(val_book_file, "w") as f:
        f.write(validation_main_template.render(classname=args.classname, papers=list_elts(conf, args.no_sessions), authors=conf.authors))

    if args.compile:
        compile(val_book_file)
