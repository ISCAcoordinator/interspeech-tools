import pathlib
import subprocess

from pylatexenc.latexencode import UnicodeToLatexEncoder

from isca.model.item import Paper, Presentation
from isca.model.person import Person


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

def is_presentation(input: object) -> bool:
    return isinstance(input, Presentation)

def has_paper(input: Presentation) -> bool:
    if not is_presentation(input):
        return False
    if input.presented_paper is None:
        return False
    return True

def get_latexified_authors(input_paper: Paper | Presentation) -> str:
    list_authors = []
    if is_presentation(input_paper):
        input_paper = input_paper.presented_paper

    for cur_author in input_paper.authors:
        list_authors.append(cur_author.str_with_flatten_affiliations(input_paper.id, short=True))

    return latexify(", ".join(list_authors))


def get_latexified_presenters(input_presentation: Presentation) -> str:
    list_presenters = []
    if input_presentation.presenters is not None:
        for cur_presenter in input_presentation.presenters:
            list_presenters.append(cur_presenter.str_with_flatten_affiliations(input_presentation.id))

    return latexify(", ".join(list_presenters))


def get_sorted_authors(authors: set[Person]) -> list[Person]:
    list_authors = sorted(authors, key=lambda x: x.lastname + " " + str(x.middle_initial) + " " + str(x.firstname))
    return list_authors


def is_tool(name: str) -> bool:
    """Check whether `name` is on PATH and marked as executable."""

    # from whichcraft import which
    from shutil import which

    return which(name) is not None


def compile(main_file: pathlib.Path):
    workdir = main_file.parent
    cmd = []
    if is_tool("latexmk"):
        p = subprocess.Popen(["latexmk", "-pdflatex=lualatex", "-pdf", main_file.name], cwd=workdir)
        p.wait()
    elif is_tool("lualatex"):
        for _ in range(2):
            p = subprocess.Popen(["lualatex", main_file.name], cwd=workdir)
            p.wait()
    else:
        raise Exception(
            "There is no compatible latex tools (lualatex needs to be available at a minimum; "
            + "pdflatex and xelatex are not supported)"
        )
