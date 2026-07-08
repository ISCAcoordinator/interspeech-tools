# Core python
from typing import Any
from subprocess import call, DEVNULL
import pathlib

# Templating / rendering
import jinja2

# From the ISCA lib
from isca.model.item import Paper

# From the utils
from .string_helpers import latexify, AUTHOR_SEP

__all__ = ["generate_pdf_report", "generate_full_pdf_report"]

###############################################################################
# constants
###############################################################################


JENV_LATEX = jinja2.Environment(
    loader=jinja2.PackageLoader("interspeech_tools.publication", "resources/validation_packages"),
    trim_blocks=True,
    lstrip_blocks=True,
    line_statement_prefix="#",
    variable_start_string="\\VAR{",
    variable_end_string="}",
)
PAPER_TEMPLATE = JENV_LATEX.get_template("doublepage.tex")
REPORT_TEMPLATE = JENV_LATEX.get_template("fullreport_doublepage.tex")


###############################################################################
# helpers
###############################################################################

# TODO: function hacked to fit IS2026
def generate_pdf_report(paper: Paper, pid: str, detailed_report: dict[str, Any], pdf_report_file: pathlib.Path):

    pdf_report_file.parent.mkdir(exist_ok=True, parents=True)
    abstract = detailed_report["abstract"]

    with open(pdf_report_file.parent / f"{pdf_report_file.stem}.tex", "w") as f:
        f.write(
            PAPER_TEMPLATE.render(
                pdf_file=paper.pdf_file,
                pid=pid,
                title=latexify(paper.title),
                authors=[
                    latexify(author.str_with_flatten_affiliations(pid, True, True)) for author in paper.authors
                ],  # FIXME: deal with authors
                abstract=abstract,
                # abstract_file=(abstracts_dir / f"{pid}.txt").resolve(),
                detailed_report=detailed_report["issues"],
            )
        )
    call(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={pdf_report_file.parent}",
            str(pdf_report_file.resolve().parent / pdf_report_file.stem),
        ],
        stdout=DEVNULL,
    )


def generate_full_pdf_report(papers: dict[str, Paper], report_dir: pathlib.Path, full_report_file: pathlib.Path):

    full_report_file.parent.mkdir(exist_ok=True, parents=True)
    full_report_tex_file = full_report_file.parent / f"{full_report_file.stem}.tex"

    # Prepare counters and helpers
    pids = sorted([int(pid) for pid in papers.keys()])
    plist = []
    for p in pids:
        if (report_dir / f"{p}.pdf").exists():
            plist.append((report_dir / f"{p}.pdf").resolve())

    # Generate and compile latex
    with open(full_report_tex_file, "w") as f:
        f.write(REPORT_TEMPLATE.render(pids=plist))

    call(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={full_report_tex_file.parent.resolve()}",
            str(full_report_tex_file.resolve()).replace(".tex", ""),
        ],
        stdout=DEVNULL,
    )
