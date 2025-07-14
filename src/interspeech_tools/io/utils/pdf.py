import re
import pathlib
import pymupdf


from isca.model.person import Affiliation
from isca.model.person import Person

PDF_WORD_KEYWORD = "INTERSPEECH2025_WORD_TEMPLATE"
PDF_AFFILIATION_KEY = "Affiliation"
PDF_AUTHOR_KEY = "Author"
PDF_TITLE_KEY = "Title"
PDF_AFFILIATION_RE = r"(?:\{(\d+)\})?\{([^}]*)\}\{([^}]+)\}\{([^}]+)\}"
PDF_AUTHOR_RE = r"([^{]*) \{([^}]+)\}(?: \{([0-9, ]+)\})?"


class WordException(Exception):
    pass


class PDFMetadataException(Exception):
    pass


def _load_extended_metadata(doc: pymupdf.Document) -> dict[str, str]:

    metadata = {}  # make my own metadata dict
    what, value = doc.xref_get_key(-1, "Info")  # /Info key in the trailer
    if what != "xref":
        pass  # PDF has no metadata
    else:
        xref = int(value.replace("0 R", ""))  # extract the metadata xref
        for key in doc.xref_get_keys(xref):
            metadata[key] = doc.xref_get_key(xref, key)[1]

    return metadata


def _get_affiliations(metadata: dict[str, str]) -> dict[str, Affiliation]:
    affiliations = dict()
    affiliations_meta = metadata[PDF_AFFILIATION_KEY].split(";")
    for cur_affiliation in affiliations_meta:
        cur_affiliation = cur_affiliation.strip()
        if not cur_affiliation:
            continue

        m = re.match(PDF_AFFILIATION_RE, cur_affiliation)
        if m:
            affiliation_key = m.group(1)
            department = m.group(2).strip()
            department = department if department != "" else None
            affiliations[affiliation_key] = Affiliation(institute=m.group(3), country=m.group(4), department=department)
        else:
            raise PDFMetadataException(f'[Affiliation] This should not have happened: "{cur_affiliation}"')

    return affiliations


def _get_authors(metadata: dict[str, str], affiliations: dict[str, Affiliation] | None = None) -> list[Person]:
    list_authors = []
    authors_meta = metadata[PDF_AUTHOR_KEY].split(";")
    for cur_author in authors_meta:
        cur_author = cur_author.strip()
        if not cur_author:
            continue

        m = re.match(PDF_AUTHOR_RE, cur_author)
        if m:
            first_name = m.group(1)
            last_name = m.group(2)

            email = f'{".".join([first_name, last_name])}@none.org'

            list_affiliations = []
            if affiliations is not None:
                if m.group(3) is None:
                    aff_keys = list(affiliations.keys())
                    if len(aff_keys) > 1:
                        raise PDFMetadataException(
                            "No affiliations were given to the author, but multiple affiliations are available"
                        )
                    list_affiliations.append(affiliations[aff_keys[0]])
                else:
                    affiliation_indices = m.group(3).split(",")
                    for affiliation_indice in affiliation_indices:
                        affiliation_indice = affiliation_indice.replace("*", "").strip()
                        if affiliation_indice == "":
                            continue
                        cur_affiliation = affiliations[affiliation_indice.strip()]
                        list_affiliations.append(cur_affiliation)

            main_affiliation = list_affiliations[0]
            alternative_affiliations = {}  # TODO: this needs to be fixed!
            cur_author = Person(
                first_name,
                last_name,
                default_affiliation=main_affiliation,
                email=email,
                paper_affiliations=alternative_affiliations,
            )
            list_authors.append(cur_author)
        else:
            raise PDFMetadataException(f'[Author] This should not have happened: "{cur_author}"')

    return list_authors


def load_pdf_information(pdf_file: pathlib.Path) -> tuple[str, list[Person]]:
    # Load the information
    doc = pymupdf.open(pdf_file)
    metadata = _load_extended_metadata(doc)
    if "Keywords" not in metadata:
        raise WordException("The document is a word and can't be analysed")
    elif metadata["Keywords"] == PDF_WORD_KEYWORD:
        raise WordException("The document is a word and can't be analysed")

    affiliations = _get_affiliations(metadata)
    authors = _get_authors(metadata, affiliations)
    title = metadata[PDF_TITLE_KEY].replace("\n", " ")

    return title, authors
