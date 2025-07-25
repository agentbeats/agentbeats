import datetime
from typing import Annotated
import yaml
import os

from pydantic import BaseModel, EmailStr, model_validator
from typing_extensions import Self

from agentdojo.default_suites.v1.tools.email_client import Inbox
from agentdojo.default_suites.v1.tools.types import CalendarEvent, CalendarEventID, EvenStatus
from agentdojo.functions_runtime import Depends

__all__ = [
    "Calendar",
    "_get_day_calendar_events",
    "_create_calendar_event",
    "_search_calendar_events",
    "_get_current_day",
    "_cancel_calendar_event",
    "_reschedule_calendar_event",
    "_add_calendar_event_participants",
]


class Calendar(BaseModel):
    current_day: datetime.date
    account_email: EmailStr
    initial_events: list[CalendarEvent]
    events: dict[CalendarEventID, CalendarEvent] = {}

    @classmethod
    def init_from_yaml_and_injection(cls, yaml_path: str, 
                                     injection: dict[str, str]) -> "Calendar":
        """
        Initialize Calendar from YAML file.
        :param injection: A dictionary containing placeholders and their replacements. For example, {"calendar_introductory_meeting_injection": "Introductory meeting details"}.
        :param yaml_path: Path to the YAML file. If None, uses default path.
        """
        try:
            # First read the file as string
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            # Perform string replacements to clean up placeholders
            for key, value in injection.items():
                yaml_content = yaml_content.replace("{" + key + "}", value)

            # Parse the modified content as YAML
            calendar_data = yaml.safe_load(yaml_content)
            
            # Create events from the YAML data
            initial_events = []
            for event_data in calendar_data['initial_events']:
                # Create CalendarEvent object from the YAML data
                calendar_event = CalendarEvent(
                    id_=CalendarEventID(event_data['id_']),
                    title=event_data['title'],
                    description=event_data.get('description', ''),
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    location=event_data.get('location'),
                    participants=event_data['participants'],
                    all_day=event_data.get('all_day', False),
                    status=EvenStatus(event_data.get('status', 'confirmed'))
                )
                initial_events.append(calendar_event)
            
            # Parse current_day if it's a string
            current_day = calendar_data['current_day']
            if isinstance(current_day, str):
                current_day = datetime.datetime.strptime(current_day, "%Y-%m-%d").date()
            
            # Create the calendar with the loaded data
            return cls(
                current_day=current_day,
                account_email=calendar_data['account_email'],
                initial_events=initial_events
            )
            
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found at {yaml_path}")
        except Exception as e:
            raise ValueError(f"Error loading calendar from YAML: {str(e)}")

    @model_validator(mode="after")
    def _create_events(self) -> Self:
        all_ids = [event.id_ for event in self.initial_events]
        if len(all_ids) != len(set(all_ids)):
            duplicate_ids = [id_ for id_ in all_ids if all_ids.count(id_) > 1]
            raise ValueError(f"Event IDs must be unique. Duplicates: {duplicate_ids}")
        self.events = {event.id_: event for event in self.initial_events}
        return self

    def _get_next_id(self) -> CalendarEventID:
        largest_id = max((int(key) for key in self.events.keys()), default=0)
        return CalendarEventID(largest_id + 1)

    def get_by_day(self, day: datetime.date) -> list[CalendarEvent]:
        return [event for event in self.events.values() if event.start_time.date() == day]

    def create_event(
        self,
        title: str,
        description: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        location: str | None,
        participants: list[EmailStr],
    ) -> CalendarEvent:
        id_ = self._get_next_id()
        participants.append(self.account_email)
        participants = list(set(participants))
        event = CalendarEvent(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            participants=participants,
            id_=id_,
        )
        self.events[id_] = event
        return event

    def cancel_event(self, inbox: Inbox, event_id: CalendarEventID) -> None:
        if event_id not in self.events:
            raise ValueError(f"Event with ID '{event_id}' not found.")
        self.events[event_id].status = EvenStatus.canceled
        inbox.send_email(
            self.events[event_id].participants,
            f"Canceled: '{self.events[event_id].title}'",
            "The event has been canceled.",
            attachments=[self.events[event_id]],
        )

    def search_events(self, query: str, date: datetime.date | None = None) -> list[CalendarEvent]:
        if date is not None:
            events = self.get_by_day(date)
        else:
            events = self.events.values()
        return [
            event
            for event in events
            if query.lower() in event.title.lower() or query.lower() in event.description.lower()
        ]

    def day_has_conflicts(self, day: datetime.date) -> bool:
        events = self.get_by_day(day)
        for i, event in enumerate(events):
            for other_event in events[i + 1 :]:
                if (
                    event.start_time <= other_event.start_time < event.end_time
                    or event.start_time < other_event.end_time <= event.end_time
                ):
                    return True
        return False

    def reschedule_event(
        self,
        inbox: Inbox,
        event_id: CalendarEventID,
        new_start_time: datetime.datetime,
        new_end_time: datetime.datetime | None = None,
    ) -> CalendarEvent:
        if event_id not in self.events:
            raise ValueError(f"Event with ID '{event_id}' not found.")
        event = self.events[event_id]
        old_start_time = event.start_time
        event.start_time = new_start_time
        if new_end_time is not None:
            event.end_time = new_end_time
        else:
            event.end_time = new_start_time + (event.end_time - old_start_time)
        start_date = event.start_time.date().isoformat()
        start_time = event.start_time.time().isoformat()
        end_date = event.end_time.date().isoformat()
        end_time = event.end_time.time().isoformat()
        body = f"The event has been rescheduled. It will start on  {start_date} at {start_time} and end on {end_date} at {end_time}."
        inbox.send_email(
            event.participants,
            subject="Rescheduled: '{event.title}'",
            body=body,
            attachments=[event],
        )
        return event

    def add_participants(self, event_id: CalendarEventID, participants: list[EmailStr]) -> CalendarEvent:
        if event_id not in self.events:
            raise ValueError(f"Event with ID '{event_id}' not found.")
        event = self.events[event_id]
        event.participants.extend(participants)
        return event


def _get_day_calendar_events(calendar: Annotated[Calendar, Depends("calendar")], day: str) -> list[CalendarEvent]:
    """Returns the appointments for the given `day`. Returns a list of dictionaries with informations about each meeting.

    :param day: The day for which to return the appointments. Must be in format YYYY-MM-DD.
    """
    date = datetime.datetime.strptime(day, "%Y-%m-%d")
    return calendar.get_by_day(date.date())


def _create_calendar_event(
    calendar: Annotated[Calendar, Depends("calendar")],
    inbox: Annotated[Inbox, Depends("inbox")],
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    participants: list[str] | None = None,
    location: str | None = None,
) -> CalendarEvent:
    """Creates a new calendar event with the given details and adds it to the calendar.
    It also sends an email to the participants with the event details.

    :param title: The title of the event.
    :param start_time: The start time of the event. Must be in format YYYY-MM-DD HH:MM.
    :param end_time: The end time of the event. Must be in format YYYY-MM-DD HH:MM.
    :param description: The description of the event.
    :param participants: The list of participants' email addresses. If `null`, no participants are set. The calendar owner's email address is always included..
    :param location: The location of the event. If `null`, no location is set.
    """
    parsed_start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    parsed_end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M")
    if participants is None:
        participants = []
    new_event = calendar.create_event(title, description, parsed_start_time, parsed_end_time, location, participants)
    inbox.send_email(
        recipients=participants,
        subject=f"Invitation: {title}",
        body=description,
        attachments=[new_event],
    )
    return new_event


def _search_calendar_events(
    calendar: Annotated[Calendar, Depends("calendar")],
    query: str,
    date: str | None = None,
) -> list[CalendarEvent]:
    """Searches calendar events that match the given query in the tile or the description. If provided, filters events by date.

    :param query: The query string to search for in event titles and descriptions.
    :param date: The date for which to search events. Must be in format YYYY-MM-DD. If `null`, searches all events.
    """
    if date is not None:
        date_ = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    else:
        date_ = None
    matches = calendar.search_events(query, date_)
    if len(matches) == 0:
        raise ValueError("No events found. Try with a different query.")
    return matches


def _get_current_day(
    calendar: Annotated[Calendar, Depends("calendar")],
) -> str:
    """Returns the current day in ISO format, e.g. '2022-01-01'.
    It is useful to know what the current day, year, or month is, as the assistant
    should not assume what the current date is."""
    return calendar.current_day.isoformat()


def _cancel_calendar_event(
    calendar: Annotated[Calendar, Depends("calendar")],
    inbox: Annotated[Inbox, Depends("inbox")],
    event_id: str,
) -> str:
    """Cancels the event with the given `event_id`. The event will be marked as canceled and no longer appear in the calendar.
    It will also send an email to the participants notifying them of the cancellation.

    :param event_id: The ID of the event to cancel.
    """
    calendar.cancel_event(inbox, CalendarEventID(event_id))
    return f"Event with ID {event_id} has been canceled and participants have been notified."


def _reschedule_calendar_event(
    calendar: Annotated[Calendar, Depends("calendar")],
    inbox: Annotated[Inbox, Depends("inbox")],
    event_id: str,
    new_start_time: str,
    new_end_time: str | None = None,
) -> CalendarEvent:
    """Reschedules the event with the given `event_id` to the new start and end times.
    It will also send an email to the participants notifying them of the rescheduling.

    :param event_id: The ID of the event to reschedule.
    :param new_start_time: The new start time of the event. Must be in format YYYY-MM-DD HH:MM.
    :param new_end_time: The new end time of the event. Must be in format YYYY-MM-DD HH:MM.
    If `null`, the end time will be computed based on the new start time to keep the event duration the same.
    """
    if new_end_time is not None:
        parsed_new_end_time = datetime.datetime.strptime(new_end_time, "%Y-%m-%d %H:%M")
    else:
        parsed_new_end_time = None
    calendar_event = calendar.reschedule_event(
        inbox,
        CalendarEventID(event_id),
        datetime.datetime.strptime(new_start_time, "%Y-%m-%d %H:%M"),
        parsed_new_end_time,
    )
    return calendar_event


def _add_calendar_event_participants(
    calendar: Annotated[Calendar, Depends("calendar")],
    event_id: str,
    participants: list[str],
) -> CalendarEvent:
    """Adds the given `participants` to the event with the given `event_id`.
    It will also email the new participants notifying them of the event.

    :param event_id: The ID of the event to add participants to.
    :param participants: The list of participants' email addresses to add to the event.
    """
    calendar_event = calendar.add_participants(CalendarEventID(event_id), participants)
    return calendar_event


if __name__ == "__main__":
    calendar = Calendar.init_from_yaml_and_injection(
        yaml_path=os.path.join(os.path.dirname(__file__), "suites", "workspace", "include", "calendar.yaml"),
        injection={}
    )

    print("Calendar initialized with current day:", calendar.current_day)
    
    result = _get_day_calendar_events(calendar, "2024-05-15")
    print("Events on 2024-05-15:", result)

    inbox = Inbox(
        account_email="user@example.com",
        initial_emails=[], 
        emails={}, 
        contact_list=[], 
        trash={}
    )

    _cancel_calendar_event(
        calendar=calendar,
        inbox=inbox,
        event_id="6"
    )
    _cancel_calendar_event(
        calendar=calendar,
        inbox=inbox,
        event_id="9"
    )
    _cancel_calendar_event(
        calendar=calendar,
        inbox=inbox,
        event_id="24"
    )

    result = _get_day_calendar_events(calendar, "2024-05-15")
    for res in result:
        print("Event:", res, "Status:", res.status)

