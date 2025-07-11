import pathlib
import subprocess

import pylatex
# from pylatexenc.latexencode import UnicodeToLatexEncoder


# TODO: this case by case management is idiotic...it should be made more general
def _process_unknown_char(input_char: str) -> str:
    return input_char
# raise Exception(f"The following character is not known ==> {input_char} <==")


# u_to_l = UnicodeToLatexEncoder(unknown_char_policy=_process_unknown_char)


def latexify(input: str | None) -> str:

    input = "" if input is None else input
    input = input.replace("\n\n", "\n")
    input = pylatex.utils.escape_latex(input)
    # input = input.replace("\n", "\n\\par ")
    return input


def is_tool(name: str) -> bool:
    """Check whether `name` is on PATH and marked as executable."""

    # from whichcraft import which
    from shutil import which

    return which(name) is not None


def compile(main_file: pathlib.Path):
    workdir = main_file.parent
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
