import pathlib
import logging
import pandas as pd

from isca.model.person import Role
from isca.model.program import PosterSession, PresentationSession, OralSession, SpecialSession
from isca.model import Conference

import pandas.io.formats.excel

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
    PERSON_WANTED_ROLES = [Role.AUTHOR, Role.PRESENTER]

    def __init__(self, conference: Conference):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.conference = conference

    def generate_data(self, output_root_dir: pathlib.Path):
        output_root_dir.mkdir(exist_ok=True, parents=True)
        self._generate_app_person(output_root_dir / "Persons.xlsx")
        self._generate_app_place(output_root_dir / "Places.xlsx")
        self._generate_app_agenda(output_root_dir / "Timeslots.xlsx")
        # self._generate_app_institution(output_root_dir / "Institutions.xlsx")
        # self._generate_app_classifier(output_root_dir / "Classifiers.xlsx")

    def _generate_app_classifier(self, output_classifier_file: pathlib.Path) -> None:
        pass

    def _generate_app_institution(self, output_institution_file: pathlib.Path) -> None:
        pass

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

            cur_person = {
                "id": author.id,
                "email": author.email,
                "name": author.name,
                "orderingName": author.str_sorting_by_last_name(),
                "firstName": firstname,
                "lastName": author.lastname,
                "Company": author.default_affiliation,
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

            # Initialise the new session
            cur_session = {
                "id": session.id,  # NOTE: Empty as it will be filled by the APP designer
                "name": session.name,
                "subtitle": session.id,
                "placeId": room.id,
                "date": timeslot.start.strftime("%d-%m-%y"),
                "startTime": timeslot.start.strftime("%H:%M"),
                "endTime": timeslot.end.strftime("%H:%M"),
                "configuratorType": "timeslot:session",
            }

            # Add session chairs
            if session.chairs is not None:
                for chair_idx, chair in enumerate(session.chairs):
                    cur_session[f"roleId_role:chair_{chair_idx}"] = chair.id

            list_agenda.append(cur_session)

            # TODO: deal with the different session type
            session_type = "oral"
            if isinstance(session, PosterSession):
                session_type = "poster"
            elif isinstance(session, PosterSession):
                session_type = "show_and_tell"
            elif isinstance(session, SpecialSession):
                session_type = "special"

            # TODO: add color
            color = None
            if (
                (self.conference.theme is not None)
                and ("colors" in self.conference.theme)
                and ("foreground" in self.conference.theme["colors"])
            ):
                color = str(self.conference.theme["colors"]["foreground"])

            if (
                (self.conference.theme is not None)
                and (session_type in self.conference.theme)
                and ("colors" in self.conference.theme[session_type])
                and ("foreground" in self.conference.theme[session_type]["colors"])
            ):
                color = str(self.conference.theme[session_type]["colors"]["foreground"])

            if color is not None:
                cur_session["color"] = color

            # Add presentations
            for presentation_idx, presentation in enumerate(session.presentations, 0):
                cur_presentation = {x: cur_session[x] for x in cur_session.keys()}
                cur_presentation["id"] = presentation.id
                cur_presentation["parent"] = cur_session["id"]
                cur_presentation["configuratorType"] = f"timeslot:{session_type}"
                cur_presentation["name"] = presentation.title
                abstract = ""
                if (presentation.abstract is not None) and (not pd.isna(presentation.abstract)):
                    abstract = "<p>" + presentation.abstract.replace("\n\n", "</p>\n<p>") + "</p>"

                cur_presentation["info"] = abstract
                if isinstance(session, OralSession):
                    cur_presentation["startTime"] = session.start_presentation(presentation_idx).strftime("%H:%M")
                    cur_presentation["endTime"] = session.end_presentation(presentation_idx).strftime("%H:%M")

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
        for col_to_keep in df_agenda.columns:
            if col_to_keep not in columns:
                columns.append(col_to_keep)
        df_agenda = df_agenda.reindex(columns=columns)
        df_agenda.to_excel(output_agenda_file, index=False)
