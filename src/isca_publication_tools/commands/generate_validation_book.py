import logging
import argparse
import pathlib

# Templating / rendering
import jinja2
from pylatexenc.latexencode import UnicodeToLatexEncoder

# ISCA Lib
from isca.io.cmt import CMTSerialiser
from isca.model.paper import Paper
from isca.model.person import Person


#################################################################################################
## Helper functions
#################################################################################################


# TODO: this case by case management is idiotic...it should be made more general
def _process_unknown_char(input_char: str) -> str:
    if input_char == "ɑ":
        return "{\\textipa{A}}"
    if input_char == "ɹ":
        return "{\\textipa{\\*r}}"
    if input_char == "ɐ":
        return "{\\textipa{\\textturna}}"
    if input_char == "ɔ":
        return "{\\textipa{\\textopeno}}"
    if input_char == "ə":
        return "{\\textipa{@}}"
    if input_char == "ɛ":
        return "{\\textipa{E}}"
    if input_char == "ɤ":
        return "{\\textipa{\\textramshorns}}"
    if input_char == "ʂ":
        return "{\\textipa{\\:s}}"
    if input_char == "ʃ":
        return "{\\textipa{S}}"
    if input_char == "ˈ":
        return '{\\textipa{"}}'
    if input_char == "ț":  # TODO: what the heck is that?
        return "t"

    raise Exception(f"The following character is not known ==> {input_char} <==")


u_to_l = UnicodeToLatexEncoder(unknown_char_policy=_process_unknown_char)


def latexify(input: str | None) -> str:

    input = "" if input is None else input
    try:
        # input = pylatex.utils.escape_latex(input)

        # Get rid of superficial newlines
        input_elts = [l.strip() for l in input.split("\n")]
        input = "\n".join(list(filter(None, input_elts)))

        # Convert to latex now
        input = str(u_to_l.unicode_to_latex(input))
        input = input.replace("\n", "\n\\par ")
        return input
    except Exception:
        print(f'The following input can\'t be converted: "{input}"')
        return "XXXX"  # TODO: that it is ugly


def get_latexified_authors(input_paper: Paper) -> str:
    list_authors = []
    for cur_author in input_paper.authors:
        list_authors.append(cur_author.str_with_flatten_affiliations())

    return latexify(", ".join(list_authors))


def get_latexified_presenters(input_paper: Paper) -> str:
    list_presenters = []
    for cur_presenter in input_paper.presenters:
        list_presenters.append(cur_presenter.str_with_flatten_affiliations())

    return latexify(", ".join(list_presenters))


def get_sorted_authors(authors: set[Person]) -> list[Person]:
    list_authors = sorted(authors, key=lambda x: x.lastname + " " + str(x.middle_initial) + " " + str(x.firstname))
    return list_authors


#################################################################################################
## Entry points
#################################################################################################


def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_validation_book",
        help="generate (latex code and compile it) the validation book to be sent to the authors",
    )

    # Add options
    parser.add_argument("-c", "--class-name", default="interspeech_validation", type=str, help="The LaTeX class name")
    parser.add_argument(
        "-p", "--pdf-path", type=str, default=None, help="The alternative directory containing the PDF files (flatten!)"
    )
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

    # Load conference
    conf = None
    serialiser = None
    if args.format == "cmt":
        serialiser = CMTSerialiser(True, True)
    else:
        raise NotImplementedError(f"The format {args.format} is not supported")
    conf = serialiser.load(conf_path)
    conf.resolve_author_paper_association()

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

    # Define inner filters
    def list_papers(author: Person) -> list[Paper]:
        return conf.list_papers(author)

    # Set filters and instanciate template
    jenv_latex.filters["latexify"] = latexify
    jenv_latex.filters["sort_authors"] = get_sorted_authors
    jenv_latex.filters["latexified_authors"] = get_latexified_authors
    jenv_latex.filters["presenters"] = get_latexified_presenters
    jenv_latex.filters["list_papers"] = list_papers
    validation_main_template = jenv_latex.get_template("main_template.tex")

    with open(val_book_file, "w") as f:
        f.write(validation_main_template.render(classname=args.class_name, papers=conf.papers, authors=conf.authors))
