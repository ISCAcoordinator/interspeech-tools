import pathlib
import logging

import pandas as pd
import pandas.io.formats.excel

from isca.model.person import Role, Speaker
from isca.model.program import (
    Keynote,
    KeynoteSession,
    OralPresentation,
    PosterPresentation,
    PosterSession,
    PresentationSession,
    OralSession,
    SocialSession,
)
from ...model import (
    Interspeech,
    InterspeechEvent,
    InterspeechEventType,
    ShowAndTellPresentation,
    ShowAndTellSession,
    SpecialPresentation,
    SpecialSession,
    SurveyTalk,
    BlueSkyPresentation,
    Tutorial,
    TutorialSession,
)
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
    LIVE_CAPTION_TAG = "68777baead7a96c528c16e59"
    PERSON_WANTED_ROLES = [Role.AUTHOR, Role.PRESENTER]

    # FIXME: for now this is hardcoded, it could be good to be more flexible
    SUPPORTED_SESSION_TYPES = {
        OralSession: "oral",
        PosterSession: "poster",
        ShowAndTellSession: "showandtell",
        SpecialSession: "special",
        KeynoteSession: "keynote",
        TutorialSession: "tutorial",
        SocialSession: "social",
    }
    SUPPORTED_PRESENTATION_TYPES = {
        OralPresentation: "oral",
        PosterPresentation: "poster",
        Keynote: "keynote",
        Tutorial: "tutorial",
        ShowAndTellPresentation: "showandtell",
        BlueSkyPresentation: "bluesky",
        SurveyTalk: "survey",
        SpecialPresentation: "special",
    }

    def __init__(self, conference: Interspeech, size_split: int = -1):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.conference = conference
        self.size_split = size_split
        self.conference.compress_annuary(lambda x: bool(x.validate_roles(set([Role.AUTHOR, Role.PRESENTER]))))

    def generate_data(self, output_root_dir: pathlib.Path):
        output_root_dir.mkdir(exist_ok=True, parents=True)
        self._generate_app_person(output_root_dir / "Persons.xlsx")
        self._generate_app_place(output_root_dir / "Places.xlsx")
        self._generate_app_agenda(output_root_dir / "Timeslots.xlsx")
        self._generate_app_tags(output_root_dir / "Tags.xlsx")

    def _generate_app_place(self, output_place_file: pathlib.Path) -> None:

        list_place = []
        for cur_room in self.conference.rooms:
            if cur_room.nb_zones == 1:
                # Initialise the new session
                cur_place = {"id": cur_room.id.replace(" ", "_"), "name": cur_room.name, "configuratorType": "place:room"}
                list_place.append(cur_place)
            else:
                for zone in cur_room.zones:
                    zone_id = cur_room.id.replace(" ", "_") + "_" + zone.lower()
                    cur_place = {"id": zone_id, "name": cur_room.name + " - " + zone, "configuratorType": "place:room"}
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
        seen_ids = set()

        # List the authors
        authors = self.conference.authors
        for author in authors:
            firstname = author.firstname
            if firstname is None:
                firstname = " "  # FIXME: this should not be valid
            elif author.middle_initial is not None:
                firstname += " " + author.middle_initial

            affiliations = author.str_affiliations(short=True)
            cur_person = {
                "id": author.id,
                "email": author.email,
                "name": author.name,
                "orderingName": author.str_sorting_by_last_name(),
                "firstName": firstname,
                "lastName": author.lastname,
                "subtitle": affiliations,
                "configuratorType": "person:person",
            }

            if isinstance(author, Speaker):
                cur_person["info"] = author.biography

            # Entry is done
            list_persons.append(cur_person)
            seen_ids.add(author.id)

        # List chairs
        for session in self.conference.sessions:
            if not isinstance(session, PresentationSession):
                continue
            for chair in session.chairs:

                if chair.id in seen_ids:
                    continue

                firstname = chair.firstname
                if firstname is None:
                    firstname = " "  # FIXME: this should not be valid
                elif chair.middle_initial is not None:
                    firstname += " " + chair.middle_initial

                affiliations = chair.str_affiliations(short=True)
                cur_person = {
                    "id": chair.id,
                    "email": chair.email,
                    "name": chair.name,
                    "orderingName": chair.str_sorting_by_last_name(),
                    "firstName": firstname,
                    "lastName": chair.lastname,
                    "subtitle": affiliations,
                    "configuratorType": "person:person",
                }

                if isinstance(chair, Speaker):
                    cur_person["info"] = chair.biography

                list_persons.append(cur_person)
                seen_ids.add(chair.id)

        # List presenters
        for session in self.conference.sessions:
            if not isinstance(session, PresentationSession):
                continue

            for presentation in session.presentations:
                if presentation.presenters is None:
                    continue

                for presenter in presentation.presenters:
                    if presenter.id in seen_ids:
                        continue

                    firstname = presenter.firstname
                    if firstname is None:
                        firstname = " "  # FIXME: this should not be valid
                    elif presenter.middle_initial is not None:
                        firstname += " " + presenter.middle_initial

                    affiliations = presenter.str_affiliations(short=True)
                    cur_person = {
                        "id": presenter.id,
                        "email": presenter.email,
                        "name": presenter.name,
                        "orderingName": presenter.str_sorting_by_last_name(),
                        "firstName": firstname,
                        "lastName": presenter.lastname,
                        "subtitle": affiliations,
                        "configuratorType": "person:person",
                    }

                    if isinstance(presenter, Speaker):
                        cur_person["info"] = presenter.biography

                    list_persons.append(cur_person)
                    seen_ids.add(presenter.id)

        # Prepare the dataframe
        df_persons = pd.DataFrame(list_persons)
        for col_to_add in CompassDataGenerator.PERSON_COLUMNS:
            if col_to_add not in df_persons.columns:
                df_persons[col_to_add] = ""
        df_persons = df_persons.reindex(columns=CompassDataGenerator.PERSON_COLUMNS)
        df_persons.sort_values(by=["lastName", "firstName"], inplace=True)

        # Split and save
        if self.size_split > 0:
            nb_persons = df_persons.index.shape[0]
            nb_slices = nb_persons // self.size_split
            for i_slice in range(0, nb_slices):
                cur_file = output_person_file.parent / (output_person_file.stem + f"_{i_slice+1}" + output_person_file.suffix)
                df_persons.iloc[i_slice * self.size_split : (i_slice + 1) * self.size_split].to_excel(cur_file, index=False)

            i_slice = nb_slices
            cur_file = output_person_file.parent / (output_person_file.stem + f"_{i_slice+1}" + output_person_file.suffix)
            df_persons.iloc[i_slice * self.size_split : (i_slice + 1) * nb_persons].to_excel(cur_file, index=False)
        else:
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
                    "name": f"{session_type} (Session)",
                    "configuratorType": "classifier:session_type",
                }
            )

        for _, event_type_value in CompassDataGenerator.SUPPORTED_PRESENTATION_TYPES.items():
            if (
                (self.conference.theme is not None)
                and ("colors" in self.conference.theme)
                and ("foreground" in self.conference.theme["colors"])
            ):
                color = str(self.conference.theme["colors"]["foreground"])

            color = None
            if (
                (self.conference.theme is not None)
                and (event_type_value in self.conference.theme)
                and ("colors" in self.conference.theme[event_type_value])
                and ("foreground" in self.conference.theme[event_type_value]["colors"])
            ):
                color = str(self.conference.theme[event_type_value]["colors"]["foreground"])

            list_tags.append(
                {
                    "id": f"{event_type_value}_presentation",
                    "color": color,
                    "name": event_type_value,
                    "configuratorType": "classifier:presentation_type",
                }
            )

        for event_type in InterspeechEventType:
            event_type_value = str(event_type).lower()
            if (
                (self.conference.theme is not None)
                and ("colors" in self.conference.theme)
                and ("foreground" in self.conference.theme["colors"])
            ):
                color = str(self.conference.theme["colors"]["foreground"])

            color = None
            if (
                (self.conference.theme is not None)
                and (event_type_value in self.conference.theme)
                and ("colors" in self.conference.theme[event_type_value])
                and ("foreground" in self.conference.theme[event_type_value]["colors"])
            ):
                color = str(self.conference.theme[event_type_value]["colors"]["foreground"])

            list_tags.append(
                {
                    "id": f"{event_type_value}",
                    "color": color,
                    "name": event_type_value.replace("_", " "),
                    "configuratorType": "classifier:event_type",
                }
            )

        list_tags.append(
            {
                "id": "best_student_paper_nominee",
                "name": "best student paper nominee",
                "configuratorType": "classifier:paper_flag",
            }
        )

        list_tags.append(
            {
                "id": "best_theme_paper_nominee",
                "name": "best theme paper nominee",
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

        # Reorganise sessions
        processed_sessions = []
        for session, timeslot, room, zone_idx in self.conference.program.sessions:
            zone = None
            if room.nb_zones > 1:
                place_id = room.name
            else:
                zone = room.zones[zone_idx]
                place_id = room.id.replace(" ", "_") + "_" + zone.replace(" ", "_")

            if (len(processed_sessions) > 0) and (processed_sessions[-1][0] == session):
                processed_sessions[-1][-1].append(place_id)
            else:
                processed_sessions.append([session, timeslot, [place_id]])

        for session, timeslot, places in processed_sessions:
            # Non presentation session have a specific use case
            if not isinstance(session, PresentationSession):
                self._logger.debug(
                    f"[{session.id}] The session is not a presentation session",
                    extra={"session_id": session.id, "session": session},
                )

                if isinstance(session, SocialSession):
                    cur_session = {
                        "id": f"timeslot_{session.id}",
                        "name": session.name,
                        "subtitle": session.id,
                        "orderingName": session.id,
                        "date": timeslot.start.strftime("%Y-%m-%d"),
                        "startTime": timeslot.start.strftime("%H:%M"),
                        "endTime": timeslot.end.strftime("%H:%M"),
                        "configuratorType": "timeslot:session",
                        "classifierId_1": "social_session",
                    }
                    for i_place, place_id in enumerate(places, 1):
                        cur_session[f"placeId_{i_place}"] = place_id

                elif isinstance(session, InterspeechEvent):
                    cur_session = {
                        "id": f"timeslot_{session.id}_session",
                        "name": session.name,
                        "subtitle": session.id,
                        "orderingName": session.id,
                        "info": session.description,
                        "date": timeslot.start.strftime("%Y-%m-%d"),
                        "startTime": timeslot.start.strftime("%H:%M"),
                        "endTime": timeslot.end.strftime("%H:%M"),
                        "configuratorType": "timeslot:session",
                        "classifierId_1": str(session.event_type).lower(),
                    }
                    for i_place, place_id in enumerate(places, 1):
                        cur_session[f"placeId_{i_place}"] = place_id
                else:
                    raise Exception(f"The non presentation session type {type(session)} is not supported")

                list_agenda.append(cur_session)
                continue

            if type(session) not in CompassDataGenerator.SUPPORTED_SESSION_TYPES:
                raise Exception(f"This session type {type(session)} is not yet supported")
            session_type = CompassDataGenerator.SUPPORTED_SESSION_TYPES[type(session)]

            # Initialise the new session
            cur_session = {
                "id": f"timeslot_{session.id}",
                "name": session.name,
                "subtitle": session.id,
                "orderingName": session.id,
                "date": timeslot.start.strftime("%Y-%m-%d"),
                "startTime": timeslot.start.strftime("%H:%M"),
                "endTime": timeslot.end.strftime("%H:%M"),
                "configuratorType": "timeslot:session",
                "classifierId_1": f"{session_type}_session",
            }
            for i_place, place_id in enumerate(places, 1):
                cur_session[f"placeId_{i_place}"] = place_id

            # FIXME: this is a ugly patch!
            # if not (isinstance(session, OralSession) or isinstance(session, PosterSession)):
            if not ((type(session) is OralSession) or (type(session) is PosterSession) or (type(session) is ShowAndTellSession)):
                cur_session["id"] = cur_session["id"] + "_session"

            # Add session chairs
            if session.chairs is not None:
                for chair_idx, chair in enumerate(session.chairs):
                    cur_session[f"roleId_role:chair_{chair_idx+1}"] = chair.id

            # If special session add description
            if isinstance(session, SpecialSession) and (session.description is not None):
                cur_session["info"] = "<p>" + session.description.replace("\n\n", "</p>\n<p>") + "</p>"

            list_agenda.append(cur_session)

            # Add presentations
            for presentation_idx, presentation in enumerate(session.presentations, 0):
                timeslot_id = presentation.presented_paper.id if presentation.presented_paper is not None else presentation.id
                timeslot_id = f"timeslot_{timeslot_id}"
                cur_presentation = {
                    "id": timeslot_id,
                    "parent": cur_session["id"],
                    "configuratorType": "timeslot:presentation",
                    "name": presentation.title,
                    "subtitle": short_presentation_id(presentation),
                    "orderingName": presentation.id,
                    "placeId_1": cur_session["placeId_1"],
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

                if (presentation.presented_paper is not None) and (
                    self.conference.is_theme_award_nominee(presentation.presented_paper)
                ):
                    cur_presentation["classifierId_3"] = "best_theme_paper_nominee"

                if (presentation_type == "oral") or (presentation_type == "survey") or (presentation_type == "keynote"):
                    cur_presentation["classifierId_4"] = CompassDataGenerator.LIVE_CAPTION_TAG

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

        def _custom_key(x: str) -> tuple[str, int]:
            elts = x.split("_")
            if len(elts) == 1:
                return (elts[0], 0)
            else:
                return ("_".join(elts[:-1]), int(elts[-1]))

        columns = columns + sorted(other_columns, key=lambda x: _custom_key(x))
        df_agenda = df_agenda.reindex(columns=columns)
        df_agenda.to_excel(output_agenda_file, index=False)
