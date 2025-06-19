import logging
import argparse
import shutil
import pathlib
import tempfile
import zipfile
import os

def add_subparsers(subparsers):
    parser = subparsers.add_parser("flatten", help="flatten a directory or an ARCHIVE with PDFs taken from CMT")

    parser.add_argument(
        "-z",
        "--input-zip",
        action="store_true",
        help="The input from CMT is a zip file not a directory",
    )

    # Add arguments
    parser.add_argument("cmt_input", help="The input directory or  zip file to flatten")
    parser.add_argument("output_dir", help="The output directory containing the PDF in the flatten form")

    parser.set_defaults(func=main)


def main(args: argparse.Namespace):
    logger = logging.getLogger(__name__)
    input = pathlib.Path(args.cmt_input)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # Turns out the input directory is
    temp_dir = None
    if args.input_zip:
        logger.debug(f"Extracting zip file: {input.resolve()}")
        temp_dir = tempfile.TemporaryDirectory()
        input_dir = pathlib.Path(temp_dir.name)
        os.path.altsep = '\\' # NOTE: CMT zip files are storing data using the Windows file separator
        with zipfile.ZipFile(input.resolve(), 'r') as zip_ref:
            zip_ref.extractall(input_dir.resolve())
    else:
        input_dir = input

    for paper_id in input_dir.iterdir():
        try:
            int(paper_id.stem)
        except ValueError:
            logger.error(f"[{paper_id.stem}] This paper name is invalid, so it is ignored")
            continue

        pdf_files = list(paper_id.glob("**/*.pdf"))
        if len(pdf_files) > 1:
            logger.warning(
                f"[{paper_id.stem}] The number of files is above 1 ({len(pdf_files)}), select the first one"
            )

        logger.debug(f"Copy {pdf_files[0].resolve()} {output_dir.resolve()}/{paper_id.stem}.pdf")
        shutil.copy(pdf_files[0].resolve(), output_dir / f"{paper_id.stem}.pdf")


    if temp_dir is not None:
        temp_dir.cleanup()
