import pathlib
import logging

import pandas as pd
import pandas.io.formats.excel

from isca.model.person import Role
from isca.model.program import (
    BlueSkyPresentation,
    Keynote,
    KeynoteSession,
    OralPresentation,
    PosterPresentation,
    PosterSession,
    PresentationSession,
    OralSession,
    ShowAndTellPresentation,
    ShowAndTellSession,
    SpecialPresentation,
    SpecialSession,
    SurveyTalk,
)
from ...model import Interspeech
from ..books.jinja_helpers import short_presentation_id

pandas.io.formats.excel.ExcelFormatter.header_style = None


class CompassDataGenerator:
    AGENDA_COLUMNS = [
        "id",
        "name",
        "subtitle",
        "subtitleDetail",
        "configuratorType",
        "info",
        "orderingName",
        "parent",
        "date",
        "startTime",
        "endTime",
        "classifierId_1",
    ]
    PERSON_COLUMNS = [
        "id",
        "name",
        "subtitle",
        "subtitleDetail",
        "configuratorType",
        "info",
        "orderingName",
        "email",
        "firstName",
        "lastName",
        "classifierId_",
    ]
    PLACE_COLUMNS = [
        "id",
        "name",
        "subtitle",
        "subtitleDetail",
        "configuratorType",
        "info",
        "orderingName",
        "exhibitorId",
    ]
    TAG_COLUMNS = ["id", "name", "subtitle", "subtitleDetail", "configuratorType", "info", "orderingName", "color"]
    PERSON_WANTED_ROLES = [Role.AUTHOR, Role.PRESENTER]

    # FIXME: for now this is hardcoded, it could be good to be more flexible
    SUPPORTED_SESSION_TYPES = {
        OralSession: "oral",
        PosterSession: "poster",
        ShowAndTellSession: "showandtell",
        SpecialSession: "special",
        KeynoteSession: "keynote",
    }
    SUPPORTED_PRESENTATION_TYPES = {
        OralPresentation: "oral",
        PosterPresentation: "poster",
        Keynote: "keynote",
        ShowAndTellPresentation: "showandtell",
        BlueSkyPresentation: "bluesky",
        SurveyTalk: "survey",
        SpecialPresentation: "special",
    }

    def __init__(self, conference: Interspeech):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.conference = conference

    def generate_data(self, output_root_dir: pathlib.Path):
        output_root_dir.mkdir(exist_ok=True, parents=True)
        self._generate_app_person(output_root_dir / "Persons.xlsx")
        self._generate_app_place(output_root_dir / "Places.xlsx")
        self._generate_app_agenda(output_root_dir / "Timeslots.xlsx")
        self._generate_app_tags(output_root_dir / "Tags.xlsx")

    def _generate_app_place(self, output_place_file: pathlib.Path) -> None:

        list_place = []
        for cur_room in self.conference.rooms:
            # Initialise the new session
            cur_place = {"id": cur_room.id, "name": cur_room.name, "configuratorType": "place:room"}
            list_place.append(cur_place)

        df_place = pd.DataFrame(list_place)
        for col_to_add in CompassDataGenerator.PLACE_COLUMNS:
            if col_to_add not in df_place.columns:
                df_place[col_to_add] = ""
        df_place = df_place.reindex(columns=CompassDataGenerator.PLACE_COLUMNS)
        # df_place.sort_values(by=["date", "endTime"], inplace=True)
        df_place.to_excel(output_place_file, index=False)

    def _generate_app_person(self, output_person_file: pathlib.Path) -> None:

        list_persons = []

        # List the authors
        authors = self.conference.authors
        for author in authors:
            firstname = author.firstname
            if firstname is None:
                firstname = "PLACE_HOLDER"
            elif author.middle_initial is not None:
                firstname += " " + author.middle_initial

            affiliations = set([a.institute for aff_list in list(author.paper_affiliations.values()) for a in aff_list])
            cur_person = {
                "id": author.id,
                "email": author.email,
                "name": author.name,
                "orderingName": author.str_sorting_by_last_name(),
                "firstName": firstname,
                "lastName": author.lastname,
                "subtitle": "; ".join(affiliations),
                "configuratorType": "person:person",
            }

            # Entry is done
            list_persons.append(cur_person)

        # Save the generated dataframe to the excel file
        df_persons = pd.DataFrame(list_persons)
        for col_to_add in CompassDataGenerator.PERSON_COLUMNS:
            if col_to_add not in df_persons.columns:
                df_persons[col_to_add] = ""
        df_persons = df_persons.reindex(columns=CompassDataGenerator.PERSON_COLUMNS)
        df_persons.sort_values(by=["lastName", "firstName"], inplace=True)
        df_persons.to_excel(output_person_file, index=False)

    def _generate_app_tags(self, output_tag_file: pathlib.Path) -> None:

        list_tags = []
        for _, session_type in CompassDataGenerator.SUPPORTED_SESSION_TYPES.items():
            if (
                (self.conference.theme is not None)
                and ("colors" in self.conference.theme)
                and ("foreground" in self.conference.theme["colors"])
            ):
                color = str(self.conference.theme["colors"]["foreground"])

            color = None
            if (
                (self.conference.theme is not None)
                and (session_type in self.conference.theme)
                and ("colors" in self.conference.theme[session_type])
                and ("foreground" in self.conference.theme[session_type]["colors"])
            ):
                color = str(self.conference.theme[session_type]["colors"]["foreground"])

            list_tags.append(
                {
                    "id": f"{session_type}_session",
                    "color": color,
                    "subtitle": session_type,
                    "configuratorType": "classifier:session_type",
                }
            )

        for _, presentation_type in CompassDataGenerator.SUPPORTED_PRESENTATION_TYPES.items():
            if (
                (self.conference.theme is not None)
                and ("colors" in self.conference.theme)
                and ("foreground" in self.conference.theme["colors"])
            ):
                color = str(self.conference.theme["colors"]["foreground"])

            color = None
            if (
                (self.conference.theme is not None)
                and (presentation_type in self.conference.theme)
                and ("colors" in self.conference.theme[presentation_type])
                and ("foreground" in self.conference.theme[presentation_type]["colors"])
            ):
                color = str(self.conference.theme[presentation_type]["colors"]["foreground"])

            list_tags.append(
                {
                    "id": f"{presentation_type}_presentation",
                    "color": color,
                    "subtitle": presentation_type,
                    "configuratorType": "classifier:presentation_type",
                }
            )

        list_tags.append(
            {
                "id": "best_student_paper_nominee",
                "subtitle": "best student paper nominee",
                "configuratorType": "classifier:paper_flag",
            }
        )
        # Save the generated dataframe to the excel file
        df_tags = pd.DataFrame(list_tags)
        for col_to_add in CompassDataGenerator.TAG_COLUMNS:
            if col_to_add not in df_tags.columns:
                df_tags[col_to_add] = ""
        df_tags = df_tags.reindex(columns=CompassDataGenerator.TAG_COLUMNS)
        df_tags.sort_values(by=["configuratorType", "id"], inplace=True)
        df_tags.to_excel(output_tag_file, index=False)

    def _generate_app_agenda(self, output_agenda_file: pathlib.Path) -> None:
        list_agenda = []
        cur_session = None

        if self.conference.program is None:
            raise Exception("The program is not defined, so the agenda can't be generated")

        for session_info in self.conference.program.sessions:
            timeslot, room, session = session_info
            if not isinstance(session, PresentationSession):
                self._logger.warning(
                    f"[{session.id}] The session is not a presentation session",
                    extra={"session_id": session.id, "session": session},
                )
                continue

            if type(session) not in CompassDataGenerator.SUPPORTED_SESSION_TYPES:
                raise Exception(f"This session type {type(session)} is not yet supported")
            session_type = CompassDataGenerator.SUPPORTED_SESSION_TYPES[type(session)]

            # Initialise the new session
            cur_session = {
                "id": session.id,
                "name": session.name,
                "subtitle": session.id,
                "orderingName": session.id,
                "placeId": room.id,
                "date": timeslot.start.strftime("%d-%m-%y"),
                "startTime": timeslot.start.strftime("%H:%M"),
                "endTime": timeslot.end.strftime("%H:%M"),
                "configuratorType": "timeslot:session",
                "classifierId_1": f"{session_type}_session",
            }

            # Add session chairs
            if session.chairs is not None:
                for chair_idx, chair in enumerate(session.chairs):
                    cur_session[f"roleId_role:chair_{chair_idx}"] = chair.id

            list_agenda.append(cur_session)

            # Add presentations
            for presentation_idx, presentation in enumerate(session.presentations, 0):
                cur_presentation = {
                    "id": presentation.presented_paper.id if presentation.presented_paper is not None else presentation.id,
                    "parent": cur_session["id"],
                    "configuratorType": "timeslot:presentation",
                    "name": presentation.title,
                    "subtitle": short_presentation_id(presentation),
                    "orderingName": presentation.id,
                    "placeId": cur_session["placeId"],
                    "date": cur_session["date"],
                    "startTime": cur_session["startTime"],
                    "endTime": cur_session["endTime"],
                }

                # Add abstract
                abstract = ""
                if (presentation.abstract is not None) and (not pd.isna(presentation.abstract)):
                    abstract = "<p>" + presentation.abstract.replace("\n\n", "</p>\n<p>") + "</p>"

                cur_presentation["info"] = abstract
                if isinstance(session, OralSession):
                    cur_presentation["startTime"] = session.start_presentation(presentation_idx).strftime("%H:%M")
                    cur_presentation["endTime"] = session.end_presentation(presentation_idx).strftime("%H:%M")

                # Add tags
                if type(presentation) not in CompassDataGenerator.SUPPORTED_PRESENTATION_TYPES:
                    raise Exception(f"This presentation type {type(presentation)} is not yet supported")
                presentation_type = CompassDataGenerator.SUPPORTED_PRESENTATION_TYPES[type(presentation)]
                cur_presentation["classifierId_1"] = f"{presentation_type}_presentation"

                if (presentation.presented_paper is not None) and (
                    self.conference.is_student_award_nominee(presentation.presented_paper)
                ):
                    cur_presentation["classifierId_2"] = "best_student_paper_nominee"

                # Add presenters
                if presentation.presenters is not None:
                    for i_presenter, presenter in enumerate(presentation.presenters, 1):
                        cur_presentation[f"roleId_role:presenter_{i_presenter}"] = presenter.id

                # And authors
                if presentation.presented_paper is not None:
                    for i_author, author in enumerate(presentation.presented_paper.authors, 1):
                        cur_presentation[f"roleId_role:author_{i_author}"] = author.id

                list_agenda.append(cur_presentation)

        # Save the generated dataframe to the excel file
        df_agenda = pd.DataFrame(list_agenda)
        for col_to_add in CompassDataGenerator.AGENDA_COLUMNS:
            if col_to_add not in df_agenda.columns:
                df_agenda[col_to_add] = ""

        # Added columns
        columns = CompassDataGenerator.AGENDA_COLUMNS.copy()
        other_columns = []
        for col_to_keep in df_agenda.columns:
            if col_to_keep not in columns:
                other_columns.append(col_to_keep)

        columns = columns + sorted(other_columns)
        df_agenda = df_agenda.reindex(columns=columns)
        df_agenda.to_excel(output_agenda_file, index=False)
