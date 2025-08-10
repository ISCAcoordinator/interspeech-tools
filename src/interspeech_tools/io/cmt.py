# Python
from datetime import datetime
import traceback
import re
import pathlib

# Data loading
from ruamel.yaml import YAML
from openpyxl import load_workbook
import pandas as pd

# Model helpers
from isca.model.event import Conference
from isca.model.core import ISCAObject
from isca.model.person import Person, Speaker, Affiliation, Role, Annuary
from isca.model.item import Paper, Session
from isca.model.program import (
    Program,
    OralPresentation,
    PosterPresentation,
    Keynote,
    KeynoteSession,
    OralSession,
    PosterSession,
    Room,
    SocialSession,
    Timeslot,
    TimeslotType,
)
from isca.io.utils.helpers import load_excel

from ..model import (
    Interspeech,
    InterspeechEvent,
    InterspeechEventType,
    Satellite,
    Tutorial,
    TutorialSession,
    BlueSkyPresentation,
    SurveyTalk,
    SpecialPresentation,
    ShowAndTellPresentation,
    SpecialSession,
    ShowAndTellSession,
)
from .utils.pdf import load_pdf_information, WordException, PDFMetadataException

###############################################################################
# Constants
###############################################################################
CMT_AUTHOR_NAME_AFF_SEP = "); "
CMT_AUTHOR_SEP = "; "
CMT_FIRST_LAST_STEP = ", "
CMT_CORRESPONDING_MARKER = "*"

CMT_SESSION_TIMESLOTS_SHEET_NAME = "Timeslots"
CMT_SESSION_SESSIONS_SHEET_NAME = "Sessions"
CMT_SESSION_ROOMS_SHEET_NAME = "Rooms"
CMT_SESSION_KEYNOTES_SHEET_NAME = "Keynotes"
CMT_SESSION_EVENTS_SHEET_NAME = "Events"
CMT_SESSION_TUTORIALS_SHEET_NAME = "Tutorials"
CMT_SESSION_BLUESKY_SHEET_NAME = "BlueSky Papers"
CMT_SESSION_SURVEY_TALKS_SHEET_NAME = "Survey Talks"
CMT_SESSION_STUDENT_AWARD_NOMINEES_SHEET_NAME = "StudentAwardNominees"
CMT_SESSION_THEME_AWARD_NOMINEES_SHEET_NAME = "ThemeAwardNominees"
CMT_SESSION_PAPER_SEPARATOR = ","

CMT_CHAIR_CONF_SEPARATOR = ","

CMT_ROLE_SEP = ";"
CMT_AFFILIATION_SEPARATOR = ";"

CMT_FREE_SLOT_TOKEN = "<FREE>"

CMT_AUTHOR_FULL_INFO_REGEXP = re.compile(r"^([^(]*)\s*\((.*)\)\s*")
CMT_AUTHOR_ELTS_REGEXP = re.compile(
    r"""
    ^\s*
    (?:([^{}]+)\s*)?
    (?:\[([^{}]+)\]\s*)?
    \{(.+)\}
    \s*$
""",
    re.VERBOSE,
)


CMT_NEW_PRESENTER_FULL_INFO_REGEXP = re.compile(r"^([^(]*)\s*(?:\((.*)\)\s*)?[<]([^>]+)[>]\s*$")
CMT_AFFILIATION_REGEXP = re.compile(
    r"""
    ^\s*
    (?:\{([^}]+)\},\s*)?
    ([^{]+)\s*
    (?:,\s*\{([^}]+)\})?
    \s*$
""",
    re.VERBOSE,
)
MAX_ID_NAME_LENGTH = 8


###############################################################################
# Core of the module
###############################################################################
class CMTSerialiser(ISCAObject):
    def __init__(self, metadata_from_pdf: bool = False, ignore_sessions: bool = False):
        super().__init__()
        self.metadata_from_pdf = metadata_from_pdf
        self.ignore_sessions = ignore_sessions
        self._annuary = Annuary()
        self._id_generator: dict[str, int] = dict()

    def _extract_df_information(self, paper_info: pd.Series) -> tuple[Paper, list[Person] | None]:

        paper_id = paper_info["Paper ID"]
        author_names = str(paper_info["Author Names"]).replace(CMT_CORRESPONDING_MARKER, "").split(CMT_AUTHOR_NAME_AFF_SEP)
        author_emails = [email.lower().strip() for email in str(paper_info["Author Emails"]).split(CMT_AUTHOR_SEP)]

        # The number of elements should be the same
        if len(author_emails) != len(author_names):
            names = "\n".join(author_names)
            self.logger.error(f"[{paper_id}] author names = {names}")
            self.logger.error(f"[{paper_id}] author emails = {author_emails}")
            raise Exception(
                f"[{paper_id}] The number of authors ({len(author_names)}) does not match the number of emails ({len(author_emails)})"
            )

        paper_authors = list()
        for i_author, cur_author in enumerate(author_names):
            cur_author = cur_author.replace(CMT_CORRESPONDING_MARKER, "").strip()
            if cur_author[-1] != ")":
                cur_author = cur_author + ")"

            match_author_affiliations = CMT_AUTHOR_FULL_INFO_REGEXP.match(cur_author)
            if not match_author_affiliations:
                raise Exception(f"[{paper_id}] Impossible to parse the author, please fix the spreadsheet: {cur_author}")

            # Extract author information
            middle_initial = None
            email = author_emails[i_author]
            cur_author = match_author_affiliations.group(1)
            if "{" in cur_author:
                match_author = CMT_AUTHOR_ELTS_REGEXP.match(cur_author)
                if match_author:
                    first_name = match_author.group(1)
                    middle_initial = match_author.group(2)
                    last_name = match_author.group(3)
                else:
                    raise Exception(f"[{paper_id}] Impossible to parse the author, please fix the spreadsheet: {cur_author}")
            else:
                author_elts = cur_author.split(" ")
                author_elts = list(filter(None, author_elts))  # NOTE: helpers to ignore empty elements due to multiple space
                last_name = author_elts[-1]
                first_name = " ".join(author_elts[:-1])

            first_name = first_name.strip() if first_name is not None else None
            last_name = last_name.strip()

            # FIXME: As for now, we dunno how to extract the affiliation component, just consider an institute
            list_affiliations = list()
            affiliations = [s.strip() for s in match_author_affiliations.group(2).split(CMT_AFFILIATION_SEPARATOR)]
            for f in affiliations:
                match_affiliation = CMT_AFFILIATION_REGEXP.match(f)
                if not match_affiliation:
                    raise Exception(f"[{paper_id}] The following affiliation for author {cur_author} is not valid: {f}")

                country = None
                if len(match_affiliation.groups()) > 2:
                    country = match_affiliation.group(3)

                affiliation = Affiliation(
                    department=match_affiliation.group(1), institute=match_affiliation.group(2), country=country
                )
                list_affiliations.append(affiliation)
            assert len(list_affiliations) > 0

            cur_person = self._annuary.find_person_by_email(email)

            # # TODO: this is too naive for now, no possibility
            # if cur_person is None:
            #     candidates = self._annuary.find_person_by_name(first_name, last_name, middle_initial)
            #     if len(candidates) > 0:
            #         if len(candidates) > 1:
            #             raise Exception(f"[{paper_id}] Too many candidates for {first_name} {'[' + middle_initial + ']' if middle_initial is not None else ''} {last_name}")
            #         cur_person = list(candidates)[0]

            if cur_person is None:
                id = self._generate_id(last_name)
                cur_person = Person(
                    id,
                    first_name,
                    last_name,
                    email=email,
                    default_affiliation=list_affiliations[0],
                    roles=set([Role.AUTHOR]),
                )
                self._annuary.add(cur_person)
            else:
                cur_person.add_role(Role.AUTHOR)
                if cur_person.firstname != first_name:
                    self.logger.debug(
                        f"[{paper_id}] Change the name of {email} from {cur_person.name} to {first_name} {{{last_name}}}"
                    )

                # NOTE: The information from the PDF are likely more reliable
                cur_person.firstname = first_name
                cur_person.lastname = last_name

            for affiliation in list_affiliations:
                cur_person.add_paper_affiliation(str(paper_info["Paper ID"]), affiliation)
            paper_authors.append(cur_person)

        # Extract presenters (TODO: This is a bit too specific, will have to check with Antoine about this)
        presenters = None
        if ("Q7 (New presenter)" in paper_info) and (not pd.isna(paper_info["Q7 (New presenter)"])):
            m_full = CMT_NEW_PRESENTER_FULL_INFO_REGEXP.match(paper_info["Q7 (New presenter)"])
            if m_full:
                self.logger.info(f"Adding alternative presenter \"{paper_info['Q7 (New presenter)']}\" to paper {paper_id}")

                pres_email = m_full.group(3).lower().strip()

                cur_presenter = self._annuary.find_person_by_email(pres_email)
                if cur_presenter is None:

                    m_identity = CMT_AUTHOR_ELTS_REGEXP.match(m_full.group(1))
                    assert m_identity is not None, f"The format of the author is not valid for: {m_full.group(1)}"
                    pres_firstname = m_identity.group(1)
                    middle_initial = m_identity.group(2)
                    pres_lastname = m_identity.group(3)

                    if m_full.group(2) is None:
                        raise Exception(f"The presenter \"{paper_info['Q7 (New presenter)']}\" does nor respect the format")

                    affiliations = []
                    for aff_str in m_full.group(2).split(CMT_AFFILIATION_SEPARATOR):
                        aff_str = aff_str.strip()
                        m_affiliation = CMT_AFFILIATION_REGEXP.match(aff_str)
                        assert m_affiliation is not None, f"The format of the affiliation is not valid for: {aff_str}"
                        affiliation = Affiliation(m_affiliation.group(2), m_affiliation.group(3), m_affiliation.group(1))
                        affiliations.append(affiliation)

                    id = self._generate_id(pres_lastname)
                    cur_presenter = Person(
                        id,
                        pres_firstname,
                        pres_lastname,
                        affiliations[0],
                        pres_email,
                        middle_initial=middle_initial,
                        paper_affiliations={str(paper_id): affiliations},
                    )  # FIXME: force unknwon affiliation
                    self._annuary.add(cur_presenter)

                cur_presenter.add_role(Role.PRESENTER)
                presenters = [cur_presenter]
            else:
                raise Exception(f"The presenter \"{paper_info['Q7 (New presenter)']}\" does nor respect the format")

        elif "Q7 (Presenter - Value)" in paper_info:
            presenter_idx = int(paper_info["Q7 (Presenter - Value)"]) - 1

            if presenter_idx >= len(paper_authors):
                raise IndexError(
                    f"[{paper_id}] Author {presenter_idx} can't be a presenter as there are only {len(paper_authors)} authors"
                )
            cur_presenter = paper_authors[presenter_idx]
            cur_presenter.add_role(Role.PRESENTER)
            presenters = [cur_presenter]
        else:
            self.logger.warning(
                f"[{paper_id}] doesn't have a presenter",
                extra={"paper_id": str(paper_info["Paper ID"]), "paper_serie": paper_info},
            )

        abstract = None
        if "Abstract" in paper_info:
            abstract = str(paper_info["Abstract"])
        elif "Paper Abstract" in paper_info:
            abstract = str(paper_info["Paper Abstract"])
        abstract = re.sub(r"(?<!\n)\n(?=\S)", " ", abstract)  # NOTE: merge consecutive lines

        # Fix title
        title = str(paper_info["Paper Title"])
        if ("\n" in title) or ("\r" in title):
            title = title.replace("\r", "")
            title = " ".join([t.strip() for t in title.split("\n")])

        resource = None
        if "Q3 (Link to resource (optional))" in paper_info:
            resource = str(paper_info["Q3 (Link to resource (optional))"])
            if not resource.startswith("https://doi.org/"):
                if resource.startswith("10."):  # FIXME: hardcoded number prefix
                    resource = "https://doi.org/" + resource
                else:
                    resource = None

        return (
            Paper(str(paper_info["Paper ID"]), title, paper_authors, abstract=abstract, resource=resource),
            presenters,
        )

    def load(self, conf_metadata_file: pathlib.Path) -> Conference:
        yaml = YAML(typ="rt", pure=True)
        with open(conf_metadata_file) as f_in:
            conf_info = yaml.load(f_in.read())

        if "alternative_emails" in conf_info:
            for reference_email, alternative_emails in conf_info["alternative_emails"].items():
                for alternative_email in alternative_emails:
                    self._annuary.add_alternative_email(reference_email, alternative_email)

        # Load data
        if conf_info["input_data"]["root_dir"].startswith("/"):
            input_root_dir = conf_info["input_data"]["root_dir"]
        else:
            input_root_dir = conf_metadata_file.parent / conf_info["input_data"]["root_dir"]

        if conf_info["input_data"]["pdfs_dir"].startswith("/"):
            pdfs_path = pathlib.Path(conf_info["input_data"]["pdfs_dir"])
        else:
            pdfs_path = input_root_dir / conf_info["input_data"]["pdfs_dir"]

        if conf_info["input_data"]["updated_pdfs_dir"].startswith("/"):
            updated_pdfs_path = pathlib.Path(conf_info["input_data"]["updated_pdfs_dir"])
        else:
            updated_pdfs_path = input_root_dir / conf_info["input_data"]["updated_pdfs_dir"]

        if conf_info["input_data"]["metadata_spreadsheet"].startswith("/"):
            metadata_file = pathlib.Path(conf_info["input_data"]["metadata_spreadsheet"])
        else:
            metadata_file = input_root_dir / conf_info["input_data"]["metadata_spreadsheet"]

        if conf_info["input_data"]["users_spreadsheet"].startswith("/"):
            users_file = pathlib.Path(conf_info["input_data"]["users_spreadsheet"])
        else:
            users_file = input_root_dir / conf_info["input_data"]["users_spreadsheet"]

        if conf_info["input_data"]["speakers_spreadsheet"].startswith("/"):
            speakers_file = pathlib.Path(conf_info["input_data"]["speakers_spreadsheet"])
        else:
            speakers_file = input_root_dir / conf_info["input_data"]["speakers_spreadsheet"]

        if conf_info["input_data"]["reviewers_spreadsheet"].startswith("/"):
            reviewers_file = pathlib.Path(conf_info["input_data"]["reviewers_spreadsheet"])
        else:
            reviewers_file = input_root_dir / conf_info["input_data"]["reviewers_spreadsheet"]

        if "sessions_spreadsheet" not in conf_info["input_data"]:
            self.ignore_sessions = True
            self.logger.warning("There is no session spreadsheet indicated, we just ignore any session information")
        elif conf_info["input_data"]["sessions_spreadsheet"].startswith("/"):
            session_file = pathlib.Path(conf_info["input_data"]["sessions_spreadsheet"])
        else:
            session_file = input_root_dir / conf_info["input_data"]["sessions_spreadsheet"]

        if conf_info["input_data"]["satellites_spreadsheet"].startswith("/"):
            satellites_file = pathlib.Path(conf_info["input_data"]["satellites_spreadsheet"])
        else:
            satellites_file = input_root_dir / conf_info["input_data"]["satellites_spreadsheet"]

        self.load_users(users_file)
        self.load_reviewers(reviewers_file)
        self.load_speakers(speakers_file)
        papers, _, presenters = self.load_papers(metadata_file, pdfs_path, updated_pdfs_path)

        if self.ignore_sessions:
            conf = self.load_conference(conf_metadata_file, papers=papers, sessions=None)
        else:
            _, program, student_award_nominees, theme_award_nominees = self.load_sessions(session_file, papers, presenters)
            conf = self.load_conference(
                conf_metadata_file,
                program=program,
                papers=papers,
                student_award_nominees=student_award_nominees,
                theme_award_nominees=theme_award_nominees,
            )

        satellites = self.load_satellite_events(satellites_file)
        conf.update_satellite_events(satellites)
        return conf

    def load_users(self, user_spreadsheet_file: pathlib.Path, ignore_role: bool = True) -> Annuary:

        users = Annuary(alternative_emails=self._annuary.alternative_emails)
        wb = load_workbook(filename=user_spreadsheet_file)
        for worksheet in wb.sheetnames:
            df = load_excel(user_spreadsheet_file, sheet_name=worksheet)

            df["Email"] = [e.lower().strip() for e in df["Email"]]
            for _, user_row in df.iterrows():
                email = str(user_row["Email"]).strip().lower()
                if users.is_an_alternative_email(email):
                    reference_email = users.get_reference_email(email)
                    if reference_email in df["Email"]:
                        self.logger.info(
                            f"We do not load user <{email}> as it will be loaded later using the reference email <{reference_email}>"
                        )
                        continue
                    else:
                        email = reference_email

                first_name = str(user_row["# First Name"]).strip()
                first_name = first_name.title() if first_name.isupper() else first_name

                middle_initial = ""
                if not pd.isna(user_row["Middle Initial (optional)"]):
                    middle_initial = str(user_row["Middle Initial (optional)"]).strip()

                if pd.isna(user_row["Last Name"]) or (str(user_row["Last Name"]) == ""):
                    last_name = first_name.strip()
                    first_name = None
                else:
                    last_name = str(user_row["Last Name"])

                last_name = last_name.title() if last_name.isupper() else last_name
                country = None
                if not pd.isna(user_row["Country"]):
                    country = str(user_row["Country"]).strip()

                affiliation = Affiliation(
                    institute=str(user_row["Organization"]).strip(),
                    country=country,
                )

                roles = set()
                if not ignore_role:
                    for r in str(user_row["Roles"]).split(CMT_ROLE_SEP):
                        if r == "Reviewer":
                            roles.add(Role.REVIEWER)
                        elif r == "Author":
                            roles.add(Role.AUTHOR)
                        elif r == "Meta-Reviewer":
                            roles.add(Role.META_REVIEWER)
                        elif r == "Senior Meta-Reviewer":
                            roles.add(Role.SENIOR_META_REVIEWER)
                        elif r == "Proceeding-Editor":
                            roles.add(Role.PROCEEDING_EDITOR)
                        elif r == "Chair":
                            roles.add(Role.CHAIR)
                        elif r == "Track Chair":
                            roles.add(Role.TRACK_CHAIR)
                        elif r == "Setting-Reader":
                            roles.add(Role.SETTING_READER)
                        elif r == "Not in CMT":
                            self.logger.debug(
                                f'User "{str(user_row["Email"]).strip()}" is not part of CMT users, inferred to be an author'
                            )
                            roles.add(Role.AUTHOR)
                        else:
                            raise Exception(f'The role ("{r}") is unknown')

                id = self._generate_id(last_name)
                cur_user = Person(
                    id,
                    first_name.strip() if first_name is not None else None,
                    last_name.strip(),
                    email=email,
                    roles=roles,
                    default_affiliation=affiliation,
                    middle_initial=middle_initial,
                )

                users.add(cur_user)

        self._annuary.update(users, ignore_alternative=True)

        return users

    def load_speakers(self, speaker_spreadsheet_file: pathlib.Path) -> Annuary:

        speakers = Annuary(alternative_emails=self._annuary.alternative_emails)
        wb = load_workbook(filename=speaker_spreadsheet_file)
        for worksheet in wb.sheetnames:
            df = load_excel(speaker_spreadsheet_file, sheet_name=worksheet)

            for _, speaker_row in df.iterrows():
                email = str(speaker_row["Email"]).lower().strip()
                cur_person = self._annuary.find_person_by_email(email)
                if cur_person is not None:
                    if email == "":
                        raise Exception(cur_person)
                    speaker = Speaker.from_person(cur_person)
                else:

                    first_name = str(speaker_row["First Name"]).strip()
                    first_name = first_name.title() if first_name.isupper() else first_name

                    middle_initial = ""
                    if not pd.isna(speaker_row["Middle Initial (optional)"]):
                        middle_initial = str(speaker_row["Middle Initial (optional)"]).strip()

                    if pd.isna(speaker_row["Last Name"]) or (str(speaker_row["Last Name"]) == ""):
                        last_name = first_name.strip()
                        first_name = None
                    else:
                        last_name = str(speaker_row["Last Name"])

                    last_name = last_name.title() if last_name.isupper() else last_name
                    country = None
                    if not pd.isna(speaker_row["Country"]):
                        country = str(speaker_row["Country"]).strip()

                    affiliation = Affiliation(
                        institute=str(speaker_row["Organization"]).strip(),
                        country=country,
                    )

                    # Create speaker
                    id = self._generate_id(last_name)
                    speaker = Speaker(
                        id,
                        first_name.strip() if first_name is not None else None,
                        last_name.strip(),
                        email=str(speaker_row["Email"]).strip(),
                        roles=set([]),
                        default_affiliation=affiliation,
                        middle_initial=middle_initial,
                    )

                speaker.add_role(Role.PRESENTER)
                speaker.biography = speaker_row["Biography"] if "Biography" in speaker_row else None
                speaker.url = speaker_row["Website"] if "Website" in speaker_row else None
                speaker.photo = (
                    speaker_spreadsheet_file.parent / speaker_row["Photo Path"]
                    if ("Photo Path" in speaker_row) and (not pd.isna(speaker_row["Photo Path"]))
                    else None
                )
                speakers.add(speaker)
        self._annuary.update(speakers, force=True)
        return speakers

    def load_reviewers(self, user_spreadsheet_file: pathlib.Path, ignore_role: bool = True) -> Annuary:
        reviewers = Annuary(alternative_emails=self._annuary.alternative_emails)
        wb = load_workbook(filename=user_spreadsheet_file)
        for worksheet in wb.sheetnames:
            df = load_excel(user_spreadsheet_file, sheet_name=worksheet)

            for _, user_row in df.iterrows():
                assert not pd.isna(user_row["Email"])
                email = str(user_row["Email"]).strip().lower()
                cur_reviewer = self._annuary.find_person_by_email(email)
                if cur_reviewer is not None:
                    cur_reviewer.add_role(Role.REVIEWER)
                    reviewers.add(cur_reviewer)
                    continue

                first_name = str(user_row["First Name"]).strip()

                middle_initial = ""
                if not pd.isna(user_row["Middle Initial (optional)"]):
                    middle_initial = str(user_row["Middle Initial (optional)"]).strip()

                if pd.isna(user_row["Last Name"]) or (str(user_row["Last Name"]) == ""):
                    last_name = first_name.strip()
                    first_name = ""
                else:
                    last_name = str(user_row["Last Name"])

                affiliation = Affiliation(
                    institute=str(user_row["Organization"]).strip(),
                )

                roles = set()
                if not ignore_role:
                    for r in str(user_row["Roles"]).split(CMT_ROLE_SEP):
                        if r == "Reviewer":
                            roles.add(Role.REVIEWER)
                        elif r == "Author":
                            roles.add(Role.AUTHOR)
                        elif r == "Meta-Reviewer":
                            roles.add(Role.META_REVIEWER)
                        elif r == "Senior Meta-Reviewer":
                            roles.add(Role.SENIOR_META_REVIEWER)
                        elif r == "Proceeding-Editor":
                            roles.add(Role.PROCEEDING_EDITOR)
                        elif r == "Chair":
                            roles.add(Role.CHAIR)
                        elif r == "Track Chair":
                            roles.add(Role.TRACK_CHAIR)
                        elif r == "Setting-Reader":
                            roles.add(Role.SETTING_READER)
                        elif r == "Not in CMT":
                            self.logger.debug(
                                f'User "{str(user_row["Email"]).strip()}" is not part of CMT users, inferred to be an author'
                            )
                            roles.add(Role.AUTHOR)
                        else:
                            raise Exception(f'The role ("{r}") is unknown')

                id = self._generate_id(last_name)
                cur_user = Person(
                    id,
                    first_name.strip(),
                    last_name.strip(),
                    email=str(user_row["Email"]).strip(),
                    roles=roles,
                    default_affiliation=affiliation,
                    middle_initial=middle_initial,
                )

                reviewers.add(cur_user)

        self._annuary.update(reviewers)
        return reviewers

    def load_papers(
        self,
        submission_summary_file: pathlib.Path,
        paper_root_dir: pathlib.Path | None = None,
        updated_paper_root_dir: pathlib.Path | None = None,
    ) -> tuple[dict[str, Paper], Annuary, dict[str, list[Person]]]:

        dict_papers = dict()
        dict_presenters = dict()

        wb = load_workbook(filename=submission_summary_file)
        for worksheet in wb.sheetnames:
            df = load_excel(submission_summary_file, sheet_name=worksheet)
            total_papers = df.shape[0]
            failed_papers = 0
            word_papers = 0
            no_pdf = 0

            # Else go through not
            for _, paper_info in df.iterrows():
                paper_id = paper_info["Paper ID"]

                # Ignore withdrawn papers
                withdrawn = paper_info.get("Withdrawn", False)
                if withdrawn:
                    self.logger.info(f"[{paper_id}] The paper is withdrawn")
                    continue

                # First use the metadata as "default" information
                cur_paper, presenters = self._extract_df_information(paper_info)

                # If expected to have PDF, use the PDF to replace the information
                pdf_path = None
                if paper_root_dir is not None:
                    paper_id = str(paper_id)
                    pdf_path = paper_root_dir / f"{paper_id}.pdf"

                    if (updated_paper_root_dir is not None) and (updated_paper_root_dir / f"{paper_id}.pdf").exists():
                        self.logger.debug(
                            f"[{paper_id}] using the updated PDF",
                            extra={
                                "paper_id": paper_id,
                            },
                        )
                        pdf_path = updated_paper_root_dir / f"{paper_id}.pdf"

                if self.metadata_from_pdf:
                    try:
                        if (pdf_path is not None) and pdf_path.exists():
                            title, authors = load_pdf_information(pdf_path)
                            cur_paper.title = title
                            cur_paper.replace_authors(authors)  # TODO: for now it is not linked to any email

                            self.logger.debug(
                                f"[{paper_id}] Metadata extracted from the PDF {pdf_path}",
                                extra={
                                    "paper_id": paper_id,
                                    "metadata_from_pdf": True,
                                    "source": pdf_path,
                                },
                            )
                        else:
                            self.logger.warning(
                                f"[{paper_id}] No PDF attached",
                                extra={"paper_id": paper_id},
                            )
                            no_pdf += 1

                    except WordException:
                        self.logger.warning(
                            f"[{paper_id}] Can't extract the information from a PDF generated by word",
                            extra={
                                "paper_id": paper_id,
                            },
                        )
                        word_papers += 1
                    except (PDFMetadataException, KeyError, IndexError) as ex:
                        self.logger.error(
                            f"[{paper_id}] Extraction of the metadata from the PDF failed, falling back on the excel spreadsheet",
                            extra={
                                "paper_id": paper_id,
                                "exception": ex,
                                "traceback": traceback.format_exc(),
                            },
                        )
                        failed_papers += 1

                # Link PDF
                if pdf_path is not None:
                    cur_paper.pdf_file = pdf_path.resolve()

                # Add track
                cur_paper.track = worksheet

                dict_papers[cur_paper.id] = cur_paper
                for cur_author in cur_paper.authors:
                    self._annuary.add(cur_author)
                dict_presenters[cur_paper.id] = presenters

            self.logger.info(
                f"[{worksheet}] total number of submissions {total_papers}: "
                + f"failed_papers={failed_papers} ({failed_papers/total_papers*100:.2f}%), "
                + f"word_papers={word_papers} ({word_papers/total_papers*100:.2f}%), "
                + f"nopdf={no_pdf} ({no_pdf/total_papers*100:.2f}%)"
            )

        return dict_papers, self._annuary, dict_presenters

    def _list_bluesky_paper_ids(self, session_summary_file: pathlib.Path) -> set[str]:
        df = load_excel(
            session_summary_file,
            sheet_name=CMT_SESSION_BLUESKY_SHEET_NAME,
        )

        bs_paper_ids = set()
        for _, bs_row in df.iterrows():
            bs_paper_ids.add(str(bs_row["Paper ID"]))
        return bs_paper_ids

    def _load_keynotes(self, session_summary_file: pathlib.Path) -> tuple[dict[str, Keynote], dict[str, list[Person]]]:
        df = load_excel(
            session_summary_file,
            sheet_name=CMT_SESSION_KEYNOTES_SHEET_NAME,
        )

        keynote_chairs = dict()
        keynotes = dict()
        for _, row in df.iterrows():
            email = str(row["Email"]).lower().strip()
            speaker = self._annuary.find_person_by_email(email)
            if speaker is None:
                raise Exception(f"The keynote speaker is not part of the annuary: {email}")

            # FIXME: duration is hardcoded
            keynote = Keynote(row["Keynote ID"], row["Paper Title"], [speaker], 60, row["Abstract"])
            keynotes[keynote.id] = keynote

            if ("Session Chairs" in row) and (not pd.isna(row["Session Chairs"])):
                chairs = []
                for chair_email in row["Session Chairs"].split(CMT_AUTHOR_SEP):
                    chair_email = chair_email.strip().lower()
                    chair = self._annuary.find_person_by_email(chair_email)

                    if chair is None:
                        self.logger.error(
                            f"[{keynote.id}] The session chair <{chair_email}> is not part of the annuary so it is ignored for now",
                            extra={"keynote_id": keynote.id},
                        )
                    else:
                        chair.add_role(Role.SESSION_CHAIR)
                        chairs.append(chair)
                keynote_chairs[keynote.id] = chairs
        return keynotes, keynote_chairs

    def _load_survey_talks(self, session_summary_file: pathlib.Path) -> dict[str, SurveyTalk]:
        df = load_excel(
            session_summary_file,
            sheet_name=CMT_SESSION_SURVEY_TALKS_SHEET_NAME,
        )

        survey_talks = dict()
        for _, row in df.iterrows():
            assert not pd.isna(row["Email"])
            email = str(row["Email"]).lower().strip()
            speaker = self._annuary.find_person_by_email(email)

            if speaker is None:
                raise Exception(f"The survey speaker is not part of the annuary: {email}")

            survey = SurveyTalk(
                row["Survey ID"],
                title=row["Paper Title"],
                presenters=[speaker],
                duration=40,
                abstract=row["Abstract"],
            )
            survey_talks[row["Survey ID"]] = survey
        return survey_talks

    def _load_tutorials(
        self, session_summary_file: pathlib.Path, timeslots: dict[str, Timeslot], rooms: dict[str, Room]
    ) -> list[tuple[Timeslot, Room, TutorialSession]]:
        df = load_excel(
            session_summary_file,
            sheet_name=CMT_SESSION_TUTORIALS_SHEET_NAME,
        )

        tutorials = []
        for _, row in df.iterrows():
            timeslot = timeslots[str(row["Timeslot name*"])]
            room = rooms[str(row["Room name*"])]
            presenters = []
            for cur_presenter in str(row["Organisers"]).split("; "):
                email = cur_presenter.lower().strip()
                speaker = self._annuary.find_person_by_email(email)
                if speaker is None:
                    raise Exception(f"The tutorial speaker is not part of the annuary: {email}")

                if not isinstance(speaker, Speaker):
                    raise Exception(f"The speaker {speaker} is not a speaker, but a person (author, reviewer, ..)")
                presenters.append(speaker)

            tutorial = Tutorial(
                str(row["Tutorial ID"]), str(row["Title"]), presenters, timeslot.duration, str(row["Description"]), False
            )
            tutorial_session = TutorialSession(f"{tutorial.id}", tutorial.title, timeslot.start, timeslot.end, tutorial)
            tutorials.append((timeslot, room, tutorial_session))

        return tutorials

    def _load_events(
        self, session_summary_file: pathlib.Path, timeslots: dict[str, Timeslot], rooms: dict[str, Room]
    ) -> list[tuple[Timeslot, Room, InterspeechEvent]]:
        df = load_excel(
            session_summary_file,
            sheet_name=CMT_SESSION_EVENTS_SHEET_NAME,
        )

        events = []
        for _, row in df.iterrows():
            timeslot = timeslots[str(row["Timeslot name*"])]
            room = rooms[str(row["Room name*"])]
            organiser = str(row["Organiser"])
            event_type = str(row["Event Type"]).lower()
            if event_type == "social":
                event_session = SocialSession(str(row["Event ID"]), str(row["Title"]))
            else:
                if event_type == "meeting":
                    event_type = InterspeechEventType.MEETING
                elif event_type == "ceremony":
                    event_type = InterspeechEventType.CEREMONY
                elif event_type.startswith("young res"):
                    event_type = InterspeechEventType.YOUNG_RESEARCHER
                else:
                    raise Exception(f"This event type is unknown: {event_type}")

                description = None
                if not pd.isna(row["Description"]):
                    description = str(row["Description"])
                event_session = InterspeechEvent(str(row["Event ID"]), str(row["Title"]), organiser, event_type, description)
            self._logger.warning(f"{repr(event_session)} => {repr(room)}")
            events.append((timeslot, room, event_session))

        return events

    def _load_theme_award_nominees(self, session_summary_file: pathlib.Path) -> set[str]:
        df = load_excel(
            session_summary_file,
            sheet_name=CMT_SESSION_THEME_AWARD_NOMINEES_SHEET_NAME,
        )

        list_nominees = set()
        for _, nominee_info in df.iterrows():
            list_nominees.add(str(nominee_info["Paper ID"]))
        return list_nominees

    def _load_student_award_nominees(self, session_summary_file: pathlib.Path) -> set[str]:
        df = load_excel(
            session_summary_file,
            sheet_name=CMT_SESSION_STUDENT_AWARD_NOMINEES_SHEET_NAME,
        )

        list_nominees = set()
        for _, nominee_info in df.iterrows():
            list_nominees.add(str(nominee_info["Paper ID"]))
        return list_nominees

    def load_sessions(
        self,
        session_summary_file: pathlib.Path,
        dict_papers: dict[str, Paper],
        dict_presenters: dict[str, list[Person] | None] = {},
    ) -> tuple[list[Session], Program, set[str], set[str]]:

        list_sessions = []

        # Load rooms
        dict_rooms = dict()
        df = load_excel(session_summary_file, sheet_name=CMT_SESSION_ROOMS_SHEET_NAME)
        plenary_room = None
        for _, room_info in df.iterrows():
            capacity = str(room_info["Capacity"]).strip()
            if (capacity == "") or (capacity == "nan"):
                capacity = None
            elif "-" in capacity:
                capacity = [int(c.strip()) for c in capacity.split("-")]
            else:
                capacity = int(capacity)

            nb_zones = 1
            zones = None
            if (
                ("Zones" in room_info)
                and (not pd.isna(room_info["Zones"]))
                and ("Nb Zones" in room_info)
                and (not pd.isna(room_info["Nb Zones"]))
            ):
                raise Exception(
                    f"[{room_info['Room ID']}] Can't define a map of zones and also impose the number of zones simultaneously"
                )
            elif ("Nb Zones" in room_info) and (not pd.isna(room_info["Nb Zones"])):
                nb_zones = int(room_info["Nb Zones"])
                zones = None
            elif ("Zones" in room_info) and (not pd.isna(room_info["Zones"])):
                zones = [z.strip() for z in str(room_info["Zones"]).split(",")]
                nb_zones = None

            room = Room(
                str(room_info["Room ID"]),
                str(room_info["Room name"]),
                str(room_info["Room type"]).lower(),
                nb_zones=nb_zones,
                zones=zones,
            )
            dict_rooms[room.id] = room
            if room.type == "plenary":
                if plenary_room is not None:
                    raise Exception(f"There is already a plenary room {plenary_room}, can't have another one: {room}")
                plenary_room = room

        assert plenary_room is not None, "There is no plenary room, which is impossible for Interspeech"

        # Now load timeslots
        dict_timeslots = dict()
        df = load_excel(session_summary_file, sheet_name=CMT_SESSION_TIMESLOTS_SHEET_NAME)
        df["Date"] = df["Date"].astype(str)
        for _, timeslot_info in df.iterrows():
            start_time = f"{timeslot_info['Date']} {timeslot_info['Start']}"
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_time = f"{timeslot_info['Date']} {timeslot_info['End']}"
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

            timeslot_type_str = str(timeslot_info["Timeslot type"]).lower().replace(" ", "_")
            if timeslot_type_str == "ceremony":
                timeslot_type = TimeslotType.CEREMONY
            elif timeslot_type_str == "keynote":
                timeslot_type = TimeslotType.KEYNOTE
            elif timeslot_type_str == "coffee_break":
                timeslot_type = TimeslotType.COFFEE_BREAK
            elif timeslot_type_str == "lunch_break":
                timeslot_type = TimeslotType.LUNCH_BREAK
            elif timeslot_type_str == "science":
                timeslot_type = TimeslotType.SCIENCE
            elif timeslot_type_str == "tutorial":
                timeslot_type = TimeslotType.TUTORIAL
            elif timeslot_type_str == "social":
                timeslot_type = TimeslotType.SOCIAL
            elif (timeslot_type_str == "general_assembly") or (timeslot_type_str == "ga"):
                timeslot_type = TimeslotType.GENERAL_ASSEMBLY
            else:
                raise Exception(f'The timeslot type "{timeslot_type_str}" is unknown')

            cur_timeslot = Timeslot(
                timeslot_info["Timeslot name"],
                timeslot_info["Timeslot string"] if "Timeslot string" in timeslot_info else timeslot_info["Timeslot name"],
                timeslot_type,
                start_time,
                end_time,
            )

            dict_timeslots[timeslot_info["Timeslot name"]] = cur_timeslot

        program = Program(list(dict_timeslots.values()), list(dict_rooms.values()))

        # Load the keynotes
        keynotes, keynote_chairs = self._load_keynotes(session_summary_file)
        for keynote_id, keynote in keynotes.items():
            if keynote.presenters is None:
                raise Exception(f"[{keynote.id}] The keynote doesn't have speaker")
            title = ", ".join([p.name for p in keynote.presenters]) + ": " + keynote.title
            timeslot = dict_timeslots[keynote.id]
            if timeslot is None:
                raise Exception("The timeslot should be defined and have the same id than the keynote")

            session = KeynoteSession(
                keynote.id, title, timeslot.start, timeslot.end, presentations=[keynote], chairs=keynote_chairs[keynote_id]
            )
            list_sessions.append(session)
            program.add_session(timeslot, plenary_room, session)

        # Load additional elements
        survey_talks = self._load_survey_talks(session_summary_file)
        bs_paper_ids = self._list_bluesky_paper_ids(session_summary_file)

        # Add the scientific sessions
        df = load_excel(session_summary_file, sheet_name=CMT_SESSION_SESSIONS_SHEET_NAME)
        for _, session_info in df.iterrows():
            if pd.isna(session_info["Session name"]):
                continue

            # Prepare basic information
            session_id = str(session_info["Session name"])
            session_id = re.sub(r"Area([0-9])-", r"Area0\1-", session_id)
            session_name = str(session_info["Session title"])

            # Get chairs
            chairs = []
            if ("Session Chairs" in session_info) and (not pd.isna(session_info["Session Chairs"])):
                for chair_email in session_info["Session Chairs"].split(CMT_AUTHOR_SEP):
                    chair_email = chair_email.strip().lower()
                    chair = self._annuary.find_person_by_email(chair_email)

                    if chair is None:
                        self.logger.error(
                            f"[{session_id}] The session chair <{chair_email}> is not part of the annuary so it is ignored for now",
                            extra={"session_id": session_id, "session_name": session_name},
                        )
                    else:
                        chair.add_role(Role.SESSION_CHAIR)
                        chairs.append(chair)

            # Create the sessions
            cur_time_slot = dict_timeslots[session_info["Timeslot name*"]]
            cur_room = dict_rooms[session_info["Room name*"]]  # FIXME: why this "*"?

            session_type = str(session_info["Session type"])
            presentation_type = str(session_info["Presentation type"])
            if session_type.lower() == "oral":
                cur_session = OralSession(session_id, session_name, cur_time_slot.start, cur_time_slot.end, chairs=chairs)
            elif session_type.lower() == "poster":
                cur_session = PosterSession(session_id, session_name, cur_time_slot.start, cur_time_slot.end, chairs=chairs)
            elif session_type.lower() == "show and tell":
                cur_session = ShowAndTellSession(session_id, session_name, cur_time_slot.start, cur_time_slot.end, chairs=chairs)
            elif session_type.lower() == "special":
                if ("Description" not in session_info) or (pd.isna(session_info["Description"])):
                    self.logger.warning(f'The description for the special session "{session_id}" is missing')
                    description = None
                else:
                    description = str(session_info["Description"])
                session_name = session_name.replace("Special Session - ", "")
                cur_session = SpecialSession(
                    session_id, session_name, cur_time_slot.start, cur_time_slot.end, description=description, chairs=chairs
                )
            else:
                self.logger.error(
                    f'[{session_id}] This session type "{session_type}" is not yet supported (ignored)',
                    extra={"session_id": session_id, "session_name": session_name},
                )
                continue

            # Now deal add the papers
            session_paper_ids = [str(id).strip() for id in str(session_info["Papers"]).split(CMT_SESSION_PAPER_SEPARATOR)]
            for paper_idx, paper_id in enumerate(session_paper_ids, 1):
                paper_id = paper_id.strip()

                if paper_id == CMT_FREE_SLOT_TOKEN:
                    self.logger.debug(
                        f"Slot {paper_idx} in the session {session_id} is free",
                        extra={"session_id": session_id, "session_name": session_name},
                    )
                    continue

                if paper_id in dict_papers:
                    cur_paper = dict_papers[paper_id]
                    paper_presenters = None
                    if (dict_presenters is not None) and (paper_id in dict_presenters):
                        paper_presenters = dict_presenters[paper_id]

                    if isinstance(cur_session, OralSession):
                        if paper_id in bs_paper_ids:
                            cur_presentation = BlueSkyPresentation(
                                f"{session_id}-{paper_idx:02d}",
                                cur_paper.title,
                                paper_presenters,
                                40,  # TODO: the duration is hardcoded
                                cur_paper.abstract,
                                cur_paper,
                            )
                        else:
                            cur_presentation = OralPresentation(
                                f"{session_id}-{paper_idx:02d}",
                                cur_paper.title,
                                paper_presenters,
                                cur_session.default_duration,
                                cur_paper.abstract,
                                cur_paper,
                            )
                    elif isinstance(cur_session, PosterSession):
                        cur_presentation = PosterPresentation(
                            f"{session_id}-{paper_idx:02d}",
                            cur_paper.title,
                            paper_presenters,
                            cur_paper.abstract,
                            cur_paper,
                        )
                    elif isinstance(cur_session, ShowAndTellSession):
                        cur_presentation = ShowAndTellPresentation(
                            f"{session_id}-{paper_idx:02d}",
                            cur_paper.title,
                            paper_presenters,
                            cur_paper.abstract,
                            cur_paper,
                        )
                    elif isinstance(cur_session, SpecialSession):
                        if presentation_type.lower() == "poster":
                            cur_presentation = PosterPresentation(
                                f"{session_id}-{paper_idx:02d}",
                                cur_paper.title,
                                paper_presenters,
                                cur_paper.abstract,
                                cur_paper,
                            )
                        elif presentation_type.lower() == "oral":
                            cur_presentation = OralPresentation(
                                f"{session_id}-{paper_idx:02d}",
                                cur_paper.title,
                                paper_presenters,
                                20,  # FIXME: this is hardcoded
                                cur_paper.abstract,
                                cur_paper,
                            )
                        else:
                            cur_presentation = SpecialPresentation(
                                f"{session_id}-{paper_idx:02d}",
                                cur_paper.title,
                                paper_presenters,
                                cur_paper.abstract,
                                cur_paper,
                            )
                    else:
                        raise Exception(f"Should not have happnened, {type(cur_session)} is not known")
                elif paper_id in survey_talks:
                    cur_presentation = survey_talks[paper_id]
                else:
                    self.logger.error(
                        f"[{session_id}] {paper_id} is not an available papers (it could have been withdrawn), so it is ignored",
                        extra={"session_id": session_id, "session_name": session_name},
                    )
                    continue

                cur_session.add_presentation(cur_presentation)

            self.logger.debug(f"{session_id} has been loaded", extra={"session_id": session_id, "session_obj": cur_session})

            if ("Zone" not in session_info) or pd.isna(session_info["Zone"]):
                program.add_session(cur_time_slot, cur_room, cur_session)
            else:
                if not ("," in str(session_info["Zone"])):
                    zones = [session_info["Zone"]]
                else:
                    zones = [s.strip() for s in str(session_info["Zone"]).split(",")]

                for zone in zones:
                    program.add_session(cur_time_slot, cur_room, cur_session, zone)

            list_sessions.append(cur_session)

        # Load the events
        event_informations = self._load_events(session_summary_file, dict_timeslots, dict_rooms)
        for evt_elts in event_informations:
            list_sessions.append(evt_elts[2])
            program.add_session(timeslot=evt_elts[0], room=evt_elts[1], session=evt_elts[2])

        # Load the tutorials
        tutorial_informations = self._load_tutorials(session_summary_file, dict_timeslots, dict_rooms)
        for tuto_elts in tutorial_informations:
            list_sessions.append(tuto_elts[2])
            program.add_session(timeslot=tuto_elts[0], room=tuto_elts[1], session=tuto_elts[2])

        student_nominees_id = self._load_student_award_nominees(session_summary_file)
        theme_nominees_id = self._load_theme_award_nominees(session_summary_file)
        return list_sessions, program, student_nominees_id, theme_nominees_id

    def load_satellite_events(self, satellite_summary_file: pathlib.Path) -> list[Satellite]:

        list_satellite = []
        wb = load_workbook(filename=satellite_summary_file)
        for worksheet in wb.sheetnames:
            df = load_excel(satellite_summary_file, worksheet)  #
            for _, satellite_info in df.iterrows():
                event = Satellite(
                    id=satellite_info["Id"],
                    name=satellite_info["Title"],
                    start_date=satellite_info["Start"],
                    end_date=satellite_info["End"],
                    location=satellite_info["Location"],
                    description=satellite_info["Description"],
                    url=satellite_info["URL"],
                )
                list_satellite.append(event)

        return sorted(list_satellite, key=lambda x: str(x.start_date) + "_" + x.id.lower())

    def load_conference(
        self,
        conference_info_file: pathlib.Path,
        papers: dict[str, Paper],
        program: Program | None = None,
        sessions: list[Session] | None = None,
        student_award_nominees: set[str] | None = None,
        theme_award_nominees: set[str] | None = None,
    ) -> Conference:

        if (sessions is not None) and (papers is not None):
            raise Exception(
                "Either the sessions OR the papers should be given. The papers will be loaded from the sessions. In case no sessions, the provide the papers."
            )

        conf_info = dict()
        yaml = YAML(typ="rt", pure=True)
        with open(conference_info_file) as f_in:
            conf_info = yaml.load(f_in.read())

        # NOTE: apparently autamtically converted into a date when loading the YAML configuration
        # # Convert the dates to datetime
        # conf_info["startDate"] = datetime.strptime(conf_info["startDate"], "%Y-%m-%d")
        # conf_info["endDate"] = datetime.strptime(conf_info["endDate"], "%Y-%m-%d")

        chairs = None
        if "chairs" in conf_info:
            chairs = []
            for chair in conf_info["chairs"].split(CMT_CHAIR_CONF_SEPARATOR):
                if "{" in chair:
                    raise NotImplementedError("Last name with spaces is not yet supported, but should be")
                else:
                    elts = chair.strip().split(" ")
                    first_name = " ".join(elts[:-1])
                    last_name = elts[-1]

                    id = self._generate_id(last_name)
                    cur_chair = Person(
                        id, first_name, last_name, "noemail@nodomain.org"
                    )  # FIXME: for now the email is slightly forced
                    cur_chair.add_role(Role.CHAIR)
                    chairs.append(cur_chair)

        conf = Interspeech(
            conf_info["id"],
            conf_info["name"],
            conf_info["startDate"],
            conf_info["endDate"],
            papers,
            program if (program is not None) else None,
            sessions if (program is None) and (sessions is not None) else None,
            conf_info["location"] if "location" in conf_info else None,
            conf_info["URL"] if "URL" in conf_info else None,
            chairs,
            conf_info["generateDOIs"] if "generateDOIs" in conf_info else False,
            conf_info["theme"] if "theme" in conf_info else None,
            annuary=self._annuary,
        )

        if student_award_nominees is not None:
            for paper_id in student_award_nominees:
                conf.add_student_award_nominees(paper_id)

        if theme_award_nominees is not None:
            for paper_id in theme_award_nominees:
                conf.add_theme_award_nominees(paper_id)

        if "ignore_rooms" in conf_info:
            ignored_rooms = set()
            ignored_room_names = set(conf_info["ignore_rooms"])
            if conf.program is not None:
                for room in conf.program.rooms:
                    if room.name in ignored_room_names:
                        ignored_rooms.add(room)

                conf.update_ignored_rooms(ignored_rooms)

        if "ignore_timeslots" in conf_info:
            ignored_timeslots = set()
            ignored_timeslot_ids = set(conf_info["ignore_timeslots"])
            if conf.program is not None:
                for timeslot in conf.program.timeslots:
                    if timeslot.id in ignored_timeslot_ids:
                        ignored_timeslots.add(timeslot)
                conf.update_ignored_timeslots(ignored_timeslots)

        return conf

    def dump_papers(self, papers: dict[str, Paper], output_file: pathlib.Path):
        list_papers = []
        for paper_id, cur_paper in papers.items():
            author_emails = []
            author_names = []
            for author in cur_paper.authors:
                author_emails.append(author.email)
                author_str = f"{author.firstname} "
                if author.middle_initial != "":
                    author_str += f"{author.middle_initial} "
                author_str += f"{{{author.lastname}}}"

                # TODO: add affiliations
                list_aff = [str(author.default_affiliation)]
                for aff in author.paper_affiliations[paper_id]:
                    list_aff.append(str(aff))
                author_str += f"({CMT_AFFILIATION_SEPARATOR.join(list_aff)})"

                author_names.append(author_str)

            paper_info = {
                "Paper ID": int(paper_id),
                "Paper Title": cur_paper.title,
                "Paper Abstract": cur_paper.abstract,
                # "Author Emails": CMT_AUTHOR_SEP.join(author_emails),
                "Author Names": CMT_AUTHOR_SEP.join(author_names),
            }
            list_papers.append(paper_info)
        df = pd.DataFrame(list_papers)
        df.sort_values("Paper ID", inplace=True)

        with pd.ExcelWriter(output_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name="papers", index=False)

    def _generate_id(self, last_name: str) -> str:

        id = last_name.strip().lower().replace(" ", "")[:MAX_ID_NAME_LENGTH]
        id = "".join(char for char in id if char.isalpha())
        if id in self._id_generator:
            self._id_generator[id] += 1
            id = id + str(self._id_generator[id])
        else:
            self._id_generator[id] = 0

        return id
