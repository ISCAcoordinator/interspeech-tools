#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Martin Cooke <m.cooke@ikerbasque.org>
    Sébastien Le Maguer <sebastien.lemaguer@helsinki.fi>

DESCRIPTION

    Helper used by the ISCA archivists to check the validity of a conference package to be published

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created:  5 June 2025
"""

# Core python
import pathlib
import argparse
import shutil

# Logger & progress bars
import logging
from interspeech_tools.publication.validation.pdf_report import generate_pdf_report
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

# Data
from ruamel.yaml import YAML

# ISCA Lib
from isca.io.utils.pdf import PDFLoader
from isca.helper.pdf import CameraReadyPDFChecker

# Helpers
from ...conf import Config
from ...io import instanciate_serialiser
from ...model import LongPaper
from ..validation.pdf_report import generate_pdf_report, generate_full_pdf_report

###############################################################################
# global constants
###############################################################################
PDF_LOADER = PDFLoader()
STANDARD_CHECKER = CameraReadyPDFChecker(6, 2, True)
LONG_CHECKER = CameraReadyPDFChecker(10, 2, True)


###############################################################################
# global constants
###############################################################################
def add_subparsers(subparsers):
    parser = subparsers.add_parser(
        "generate_validation_packages",
        help="generate the validation packages to be communicated to the helpers",
    )

    # Add performative options
    parser.add_argument("-n", "--nb-helpers", default=1, type=int, help="The number of Helpers")
    parser.add_argument(
        "-f",
        "--disable-font-checker",
        action="store_true",
        help="Deactivate the checking of the font",
    )
    parser.add_argument(
        "-p",
        "--with-pdf-reports",
        action="store_true",
        help="Generate the PDF report for each helper in addition to the YAML ones",
    )

    # Add arguments
    parser.add_argument("conf_input", help="The input configuraton file required for the conference")
    parser.add_argument("output_root_dir", help="The output directory containing the material to be imported in the ISCA Archive")

    parser.set_defaults(func=main)


###############################################################################
# Entry point
###############################################################################
def main(args: argparse.Namespace):
    logger = logging.getLogger(__name__)
    config = Config(pathlib.Path(args.conf_input))

    # Load conferenceerence
    serialiser = instanciate_serialiser(config, args.debug)
    conference = serialiser.load()
    conference.resolve_author_paper_association()

    with logging_redirect_tqdm():
        papers = dict()
        for paper_id, paper in tqdm(conference.papers.items(), desc="validation"):
            logger.info(f"[{paper_id}] Validation started")
            paper_report = {"title": paper.title, "pdf_file": paper.pdf_file, "abstract": paper.abstract}
            authors = []
            for paper_author in paper.authors:
                author = {
                    "first_name": paper_author.firstname,
                    "last_name": paper_author.lastname,
                    "email": paper_author.email,
                    "affiliation": paper_author.str_affiliations(paper_id=paper_id, short=True, markers=False),
                }
                authors.append(author)
            paper_report["authors"] = authors
            paper_report["checked"] = False
            try:
                the_pdf = PDF_LOADER.load_pdf(paper.pdf_file, False)
                logger.debug(f"[{paper_id}] The paper is a regular paper", extra={"paper_id": paper_id})
                if isinstance(paper, LongPaper):
                    _, _, report = LONG_CHECKER.validates(str(paper_id), the_pdf, paper)
                else:
                    _, _, report = STANDARD_CHECKER.validates(str(paper_id), the_pdf, paper)

            except Exception as ex:
                report = {"fundamental": str(ex)}

            # Add paper report
            paper_report["issues"] = report
            papers[paper_id] = paper_report
            logger.debug(paper_report)

            logger.info(f"[{paper_id}] Validation done")

        ##
        # Generate packages
        ###################################
        yaml = YAML(typ="rt", pure=True)
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        output_root_dir = pathlib.Path(args.output_root_dir)
        nb_papers_per_package = (len(papers.keys()) // args.nb_helpers) + 1
        i_helper = 0
        subset_papers = {}
        for paper_idx, (paper_id, paper_info) in enumerate(tqdm(papers.items(), desc="serialize")):
            if (paper_idx % nb_papers_per_package) == 0:
                if i_helper != 0:
                    with open(output_dir / "report.yaml", "w") as f_output:
                        yaml.dump({"papers": subset_papers}, f_output)

                    if args.with_pdf_reports:
                        generate_full_pdf_report(subset_papers, output_dir / "check_pdfs", output_dir / "validation_report.pdf")
                    logger.info(f"Package for helper {i_helper} is now ready")

                i_helper += 1
                subset_papers = {}
                output_dir = output_root_dir / f"helper_{i_helper}"
                pdfs_dir = output_dir / "pdfs"
                pdfs_dir.mkdir(exist_ok=True, parents=True)

            pdf_file = conference.papers[paper_id].pdf_file
            assert pdf_file is not None, f"{paper_id} doesn't have a PDF"
            shutil.copy(pdf_file, pdfs_dir / pdf_file.name)
            paper_info["pdf_file"] = str((pdfs_dir / pdf_file.name).relative_to(output_dir))

            if (paper_info["issues"] is not None) and ("abstract" in paper_info["issues"]):
                paper_info["abstract"] = paper_info["issues"]["abstract"]
                paper_info["issues"]["abstract"] = "Check abstract"

            subset_papers[paper_id] = paper_info

            if args.with_pdf_reports:
                (output_dir / "check_pdfs").mkdir(exist_ok=True, parents=True)
                generate_pdf_report(
                    conference.papers[paper_id], str(paper_id), paper_info, output_dir / f"check_pdfs/{paper_id}.pdf"
                )

        with open(output_dir / "report.yaml", "w") as f_output:
            yaml.dump({"papers": subset_papers}, f_output)

        if args.with_pdf_reports:
            generate_full_pdf_report(subset_papers, output_dir / "check_pdfs", output_dir / "validation_report.pdf")

        logger.info(f"Package for helper {i_helper} is now ready")
