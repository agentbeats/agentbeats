import datetime
from typing import Annotated, Optional, List, Dict, Any, Union
import json
import yaml
import os
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, EmailStr, field_validator
from typing_extensions import Self

__all__ = [
    "GoogleCalendarClient",
    "CalendarEvent", 
    "Contact",
    "DirectoryPerson",
    "AvailabilityInfo",
    "google_calendar_create_event",
    "google_calendar_update_event", 
    "google_calendar_list_events",
    "google_calendar_get_event_by_id",
    "google_calendar_delete_event",
    "google_calendar_get_contacts",
    "google_calendar_search_contacts", 
    "google_calendar_list_directory_people",
    "google_calendar_search_directory_people",
    "google_calendar_list_other_contacts",
    "google_calendar_search_other_contacts",
    "google_calendar_get_availability"
]


class EventStatus(str, Enum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative" 
    CANCELLED = "cancelled"
    CANCELED = "canceled"  # US spelling variant used by agentdojo


@dataclass
class CalendarEvent:
    """Represents a Google Calendar event."""
    id: str
    summary: str  # Event name
    start: Dict[str, Any]  # Start time with dateTime and timeZone
    end: Dict[str, Any]    # End time with dateTime and timeZone
    description: Optional[str] = ""
    location: Optional[str] = None
    attendees: List[Dict[str, Any]] = field(default_factory=list)
    calendar_id: str = "primary"
    status: EventStatus = EventStatus.CONFIRMED
    conference_data: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    creator: Optional[Dict[str, str]] = None
    organizer: Optional[Dict[str, str]] = None


@dataclass
class Contact:
    """Represents a contact."""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    organization: Optional[str] = None


@dataclass  
class DirectoryPerson:
    """Represents a directory person."""
    id: str
    name: str
    email: str
    department: Optional[str] = None
    title: Optional[str] = None


@dataclass
class AvailabilityInfo:
    """Represents availability information for a calendar."""
    calendar_id: str
    busy_times: List[Dict[str, str]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)


class GoogleCalendarClient:
    """Mock Google Calendar client for MCP server."""
    
    def __init__(self, user_email: str = "user@example.com", initial_events: List[CalendarEvent] = None, 
                 initial_contacts: List[Contact] = None, initial_directory_people: List[DirectoryPerson] = None,
                 initial_other_contacts: List[Contact] = None, current_day: datetime.date = None):
        self.user_email = user_email
        self.current_day = current_day or datetime.date.today()
        self.events: Dict[str, CalendarEvent] = {}
        self.contacts: List[Contact] = initial_contacts or []
        self.directory_people: List[DirectoryPerson] = initial_directory_people or []
        self.other_contacts: List[Contact] = initial_other_contacts or []
        self._next_event_id = 1
        
        # Initialize with provided events or sample data
        if initial_events:
            for event in initial_events:
                self.events[event.id] = event
                # Update next ID to avoid conflicts
                try:
                    event_id_num = int(event.id)
                    if event_id_num >= self._next_event_id:
                        self._next_event_id = event_id_num + 1
                except ValueError:
                    pass
        else:
            raise ValueError("Initial events must be provided to initialize the client.")
    
    @classmethod
    def init_from_yaml_and_injection(cls, yaml_path: str, injection: Dict[str, str]) -> "GoogleCalendarClient":
        """
        Initialize GoogleCalendarClient from YAML file.
        :param injection: A dictionary containing placeholders and their replacements.
        :param yaml_path: Path to the YAML file.
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
            
            # Parse current_day if it's a string
            current_day = calendar_data.get('current_day')
            if isinstance(current_day, str):
                current_day = datetime.datetime.strptime(current_day, "%Y-%m-%d").date()
            elif current_day is None:
                current_day = datetime.date.today()
            
            # Create events from the YAML data
            initial_events = []
            if 'initial_events' in calendar_data:
                for event_data in calendar_data['initial_events']:
                    # Parse start and end times
                    start_time = event_data['start_time']
                    end_time = event_data['end_time']
                    
                    if isinstance(start_time, str):
                        start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        # Convert to naive UTC for consistency
                        if start_dt.tzinfo is not None:
                            start_dt = start_dt.replace(tzinfo=None)
                    else:
                        start_dt = start_time
                    
                    if isinstance(end_time, str):
                        end_dt = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        # Convert to naive UTC for consistency
                        if end_dt.tzinfo is not None:
                            end_dt = end_dt.replace(tzinfo=None)
                    else:
                        end_dt = end_time
                    
                    # Parse attendees
                    attendees = []
                    if 'participants' in event_data:
                        for participant in event_data['participants']:
                            attendees.append({
                                "email": participant,
                                "responseStatus": "needsAction"
                            })
                    
                    # Create CalendarEvent object
                    calendar_event = CalendarEvent(
                        id=str(event_data['id_']),
                        summary=event_data['title'],
                        start={
                            "dateTime": start_dt.isoformat(),
                            "timeZone": "UTC"
                        },
                        end={
                            "dateTime": end_dt.isoformat(),
                            "timeZone": "UTC"
                        },
                        description=event_data.get('description', ''),
                        location=event_data.get('location'),
                        attendees=attendees,
                        status=EventStatus(event_data.get('status', 'confirmed')),
                        created=datetime.datetime.now().isoformat(),
                        updated=datetime.datetime.now().isoformat(),
                        creator={"email": calendar_data.get('account_email', 'user@example.com')},
                        organizer={"email": calendar_data.get('account_email', 'user@example.com')}
                    )
                    initial_events.append(calendar_event)
            
            # Create contacts from YAML data
            initial_contacts = []
            if 'contacts' in calendar_data:
                for contact_data in calendar_data['contacts']:
                    contact = Contact(
                        id=str(contact_data['id']),
                        name=contact_data['name'],
                        email=contact_data['email'],
                        phone=contact_data.get('phone'),
                        organization=contact_data.get('organization')
                    )
                    initial_contacts.append(contact)
            
            # Create directory people from YAML data
            initial_directory_people = []
            if 'directory_people' in calendar_data:
                for person_data in calendar_data['directory_people']:
                    person = DirectoryPerson(
                        id=str(person_data['id']),
                        name=person_data['name'],
                        email=person_data['email'],
                        department=person_data.get('department'),
                        title=person_data.get('title')
                    )
                    initial_directory_people.append(person)
            
            # Create other contacts from YAML data
            initial_other_contacts = []
            if 'other_contacts' in calendar_data:
                for contact_data in calendar_data['other_contacts']:
                    contact = Contact(
                        id=str(contact_data['id']),
                        name=contact_data['name'],
                        email=contact_data['email'],
                        phone=contact_data.get('phone'),
                        organization=contact_data.get('organization')
                    )
                    initial_other_contacts.append(contact)
            
            # Create the calendar client with the loaded data
            return cls(
                user_email=calendar_data.get('account_email', 'user@example.com'),
                current_day=current_day,
                initial_events=initial_events,
                initial_contacts=initial_contacts,
                initial_directory_people=initial_directory_people,
                initial_other_contacts=initial_other_contacts
            )
            
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found at {yaml_path}")
        except Exception as e:
            raise ValueError(f"Error loading calendar from YAML: {str(e)}")
    
    def _get_next_event_id(self) -> str:
        """Generate next event ID."""
        event_id = str(self._next_event_id)
        self._next_event_id += 1
        return event_id
    
    def _parse_time(self, time_str: str) -> datetime.datetime:
        """Parse time from Unix timestamp or ISO8601 format."""
        try:
            # Try Unix timestamp (milliseconds)
            if time_str.isdigit() and len(time_str) == 13:
                return datetime.datetime.fromtimestamp(int(time_str) / 1000)
            # Try Unix timestamp (seconds)
            elif time_str.isdigit() and len(time_str) == 10:
                return datetime.datetime.fromtimestamp(int(time_str))
            # Try ISO8601 format
            else:
                # Handle various ISO formats
                for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.datetime.strptime(time_str, fmt)
                    except ValueError:
                        continue
                # If all else fails, try built-in ISO parsing
                dt = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                # Convert to naive UTC for consistency
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time format: {time_str}")
    
    def _format_time_for_api(self, dt: datetime.datetime) -> Dict[str, Any]:
        """Format datetime for Google Calendar API."""
        return {
            "dateTime": dt.isoformat(),
            "timeZone": "UTC"
        }
    
    def create_event(
        self,
        event_name: str,
        start_time: str,
        end_time: Optional[str] = None,
        calendar: str = "primary",
        attendees: Optional[str] = None,
        event_location: Optional[str] = None,
        event_description: Optional[str] = None,
        event_id: Optional[str] = None,
        include_meet_link: bool = False
    ) -> CalendarEvent:
        """Create a new calendar event."""
        # Parse start time
        start_dt = self._parse_time(start_time)
        
        # Parse or calculate end time
        if end_time:
            end_dt = self._parse_time(end_time)
        else:
            end_dt = start_dt + datetime.timedelta(hours=1)
        
        # Generate event ID if not provided
        if not event_id:
            event_id = self._get_next_event_id()
        
        # Parse attendees
        attendee_list = []
        if attendees:
            if isinstance(attendees, str):
                # Split by comma if string
                emails = [email.strip() for email in attendees.split(',')]
            else:
                emails = attendees
            
            for email in emails:
                attendee_list.append({
                    "email": email,
                    "responseStatus": "needsAction"
                })
        
        # Create conference data if requested
        conference_data = None
        if include_meet_link:
            conference_data = {
                "createRequest": {
                    "requestId": f"meet_{event_id}",
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            }
        
        # Create event
        event = CalendarEvent(
            id=event_id,
            summary=event_name,
            start=self._format_time_for_api(start_dt),
            end=self._format_time_for_api(end_dt),
            description=event_description or "",
            location=event_location,
            attendees=attendee_list,
            calendar_id=calendar,
            conference_data=conference_data,
            created=datetime.datetime.now().isoformat(),
            updated=datetime.datetime.now().isoformat(),
            creator={"email": self.user_email},
            organizer={"email": self.user_email}
        )
        
        self.events[event_id] = event
        return event
    
    def update_event(
        self,
        event_id: str,
        event_name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        calendar: str = "primary",
        attendees: Optional[str] = None,
        event_location: Optional[str] = None,
        event_description: Optional[str] = None
    ) -> CalendarEvent:
        """Update an existing calendar event."""
        if event_id not in self.events:
            raise ValueError(f"Event with ID '{event_id}' not found")
        
        event = self.events[event_id]
        
        # Update fields if provided
        if event_name:
            event.summary = event_name
        
        if start_time:
            start_dt = self._parse_time(start_time)
            event.start = self._format_time_for_api(start_dt)
        
        if end_time:
            end_dt = self._parse_time(end_time)
            event.end = self._format_time_for_api(end_dt)
        
        if event_location is not None:
            event.location = event_location
        
        if event_description is not None:
            event.description = event_description
        
        if attendees is not None:
            attendee_list = []
            if attendees:
                emails = [email.strip() for email in attendees.split(',')]
                for email in emails:
                    attendee_list.append({
                        "email": email,
                        "responseStatus": "needsAction"
                    })
            event.attendees = attendee_list
        
        event.updated = datetime.datetime.now().isoformat()
        return event
    
    def list_events(
        self,
        calendar: str = "primary",
        after: Optional[str] = None,
        before: Optional[str] = None
    ) -> List[CalendarEvent]:
        """List calendar events with optional filtering."""
        events = [e for e in self.events.values() if e.calendar_id == calendar]
        
        if after:
            after_dt = self._parse_time(after)
            events = [e for e in events if self._parse_time(e.start["dateTime"]) >= after_dt]
        
        if before:
            before_dt = self._parse_time(before)
            events = [e for e in events if self._parse_time(e.end["dateTime"]) <= before_dt]
        
        return sorted(events, key=lambda e: e.start["dateTime"])
    
    def get_event_by_id(self, event_id: str, calendar: str = "primary") -> CalendarEvent:
        """Get a specific event by ID."""
        if event_id not in self.events:
            raise ValueError(f"Event with ID '{event_id}' not found")
        
        event = self.events[event_id]
        if event.calendar_id != calendar:
            raise ValueError(f"Event not found in calendar '{calendar}'")
        
        return event
    
    def delete_event(self, event_id: str, calendar: str = "primary") -> bool:
        """Delete an event."""
        if event_id not in self.events:
            raise ValueError(f"Event with ID '{event_id}' not found")
        
        event = self.events[event_id]
        if event.calendar_id != calendar:
            raise ValueError(f"Event not found in calendar '{calendar}'")
        
        del self.events[event_id]
        return True
    
    def get_contacts(self, page_cursor: Optional[str] = None) -> Dict[str, Any]:
        """Get contacts with pagination."""
        # Simple pagination simulation
        start_idx = int(page_cursor) if page_cursor else 0
        page_size = 10
        end_idx = start_idx + page_size
        
        contacts_page = self.contacts[start_idx:end_idx]
        
        result = {
            "connections": [
                {
                    "resourceName": f"people/{c.id}",
                    "names": [{"displayName": c.name}],
                    "emailAddresses": [{"value": c.email}],
                    "phoneNumbers": [{"value": c.phone}] if c.phone else [],
                    "organizations": [{"name": c.organization}] if c.organization else []
                }
                for c in contacts_page
            ]
        }
        
        if end_idx < len(self.contacts):
            result["nextPageToken"] = str(end_idx)
        
        return result
    
    def search_contacts(self, query: str) -> Dict[str, Any]:
        """Search contacts by query."""
        matching_contacts = [
            c for c in self.contacts
            if query.lower() in c.name.lower() or query.lower() in c.email.lower()
        ]
        
        return {
            "connections": [
                {
                    "resourceName": f"people/{c.id}",
                    "names": [{"displayName": c.name}],
                    "emailAddresses": [{"value": c.email}],
                    "phoneNumbers": [{"value": c.phone}] if c.phone else [],
                    "organizations": [{"name": c.organization}] if c.organization else []
                }
                for c in matching_contacts
            ]
        }
    
    def list_directory_people(self, page_cursor: Optional[str] = None) -> Dict[str, Any]:
        """List directory people with pagination."""
        start_idx = int(page_cursor) if page_cursor else 0
        page_size = 10
        end_idx = start_idx + page_size
        
        people_page = self.directory_people[start_idx:end_idx]
        
        result = {
            "people": [
                {
                    "resourceName": f"people/{p.id}",
                    "names": [{"displayName": p.name}],
                    "emailAddresses": [{"value": p.email}],
                    "organizations": [{"department": p.department, "title": p.title}]
                }
                for p in people_page
            ]
        }
        
        if end_idx < len(self.directory_people):
            result["nextPageToken"] = str(end_idx)
        
        return result
    
    def search_directory_people(self, query: str, page_cursor: Optional[str] = None) -> Dict[str, Any]:
        """Search directory people by query."""
        matching_people = [
            p for p in self.directory_people
            if query.lower() in p.name.lower() or 
               query.lower() in p.email.lower() or
               (p.department and query.lower() in p.department.lower()) or
               (p.title and query.lower() in p.title.lower())
        ]
        
        start_idx = int(page_cursor) if page_cursor else 0
        page_size = 10
        end_idx = start_idx + page_size
        
        people_page = matching_people[start_idx:end_idx]
        
        result = {
            "people": [
                {
                    "resourceName": f"people/{p.id}",
                    "names": [{"displayName": p.name}],
                    "emailAddresses": [{"value": p.email}],
                    "organizations": [{"department": p.department, "title": p.title}]
                }
                for p in people_page
            ]
        }
        
        if end_idx < len(matching_people):
            result["nextPageToken"] = str(end_idx)
        
        return result
    
    def list_other_contacts(self, page_cursor: Optional[str] = None) -> Dict[str, Any]:
        """List other contacts with pagination."""
        start_idx = int(page_cursor) if page_cursor else 0
        page_size = 10
        end_idx = start_idx + page_size
        
        contacts_page = self.other_contacts[start_idx:end_idx]
        
        result = {
            "otherContacts": [
                {
                    "resourceName": f"otherContacts/{c.id}",
                    "names": [{"displayName": c.name}],
                    "emailAddresses": [{"value": c.email}],
                    "phoneNumbers": [{"value": c.phone}] if c.phone else [],
                    "organizations": [{"name": c.organization}] if c.organization else []
                }
                for c in contacts_page
            ]
        }
        
        if end_idx < len(self.other_contacts):
            result["nextPageToken"] = str(end_idx)
        
        return result
    
    def search_other_contacts(self, query: str) -> Dict[str, Any]:
        """Search other contacts by query."""
        matching_contacts = [
            c for c in self.other_contacts
            if query.lower() in c.name.lower() or query.lower() in c.email.lower()
        ]
        
        return {
            "otherContacts": [
                {
                    "resourceName": f"otherContacts/{c.id}",
                    "names": [{"displayName": c.name}],
                    "emailAddresses": [{"value": c.email}],
                    "phoneNumbers": [{"value": c.phone}] if c.phone else [],
                    "organizations": [{"name": c.organization}] if c.organization else []
                }
                for c in matching_contacts
            ]
        }
    
    def get_availability(
        self,
        time_min: str,
        time_max: str,
        time_zone: str = "UTC",
        items: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Get free/busy information for calendars."""
        if not items:
            items = [{"id": "primary"}]
        
        time_min_dt = self._parse_time(time_min)
        time_max_dt = self._parse_time(time_max)
        
        calendars = {}
        
        for item in items:
            calendar_id = item["id"]
            busy_times = []
            
            # Find events in the time range for this calendar
            for event in self.events.values():
                if event.calendar_id != calendar_id:
                    continue
                
                event_start = self._parse_time(event.start["dateTime"])
                event_end = self._parse_time(event.end["dateTime"])
                
                # Check if event overlaps with query range
                if event_start < time_max_dt and event_end > time_min_dt:
                    busy_times.append({
                        "start": max(event_start, time_min_dt).isoformat(),
                        "end": min(event_end, time_max_dt).isoformat()
                    })
            
            calendars[calendar_id] = {
                "busy": busy_times,
                "errors": []
            }
        
        return {
            "kind": "calendar#freeBusy",
            "timeMin": time_min_dt.isoformat(),
            "timeMax": time_max_dt.isoformat(),
            "calendars": calendars
        }


# Global client instance (lazy initialization)
_client = None

def _get_client():
    """Get or create the global client instance."""
    global _client
    if _client is None:
        raise ValueError("GoogleCalendarClient is not initialized. Call init_client_from_yaml first.")
    return _client

def init_client_from_yaml(yaml_path: str, injection: Dict[str, str] = None):
    """Initialize the global client from YAML configuration."""
    global _client
    if injection is None:
        injection = {}
    _client = GoogleCalendarClient.init_from_yaml_and_injection(yaml_path, injection)


# MCP Tool Functions
def google_calendar_create_event(
    eventName: str,
    startTime: str,
    endTime: Optional[str] = None,
    calendar: str = "primary",
    attendees: Optional[str] = None,
    eventLocation: Optional[str] = None,
    eventDescription: Optional[str] = None,
    eventId: Optional[str] = None,
    includeMeetLink: bool = False
) -> Dict[str, Any]:
    """Create a Google Calendar event."""
    try:
        client = _get_client()
        event = client.create_event(
            event_name=eventName,
            start_time=startTime,
            end_time=endTime,
            calendar=calendar,
            attendees=attendees,
            event_location=eventLocation,
            event_description=eventDescription,
            event_id=eventId,
            include_meet_link=includeMeetLink
        )
        return {
            "success": True,
            "event": {
                "id": event.id,
                "summary": event.summary,
                "start": event.start,
                "end": event.end,
                "description": event.description,
                "location": event.location,
                "attendees": event.attendees,
                "conferenceData": event.conference_data
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_update_event(
    eventId: str,
    eventName: Optional[str] = None,
    startTime: Optional[str] = None,
    endTime: Optional[str] = None,
    calendar: str = "primary",
    attendees: Optional[str] = None,
    eventLocation: Optional[str] = None,
    eventDescription: Optional[str] = None
) -> Dict[str, Any]:
    """Update a Google Calendar event."""
    try:
        client = _get_client()
        event = client.update_event(
            event_id=eventId,
            event_name=eventName,
            start_time=startTime,
            end_time=endTime,
            calendar=calendar,
            attendees=attendees,
            event_location=eventLocation,
            event_description=eventDescription
        )
        return {
            "success": True,
            "event": {
                "id": event.id,
                "summary": event.summary,
                "start": event.start,
                "end": event.end,
                "description": event.description,
                "location": event.location,
                "attendees": event.attendees
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_list_events(
    calendar: str = "primary",
    after: Optional[str] = None,
    before: Optional[str] = None
) -> Dict[str, Any]:
    """List Google Calendar events."""
    try:
        client = _get_client()
        events = client.list_events(calendar=calendar, after=after, before=before)
        return {
            "success": True,
            "events": [
                {
                    "id": event.id,
                    "summary": event.summary,
                    "start": event.start,
                    "end": event.end,
                    "description": event.description,
                    "location": event.location,
                    "attendees": event.attendees,
                    "status": event.status
                }
                for event in events
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_get_event_by_id(
    eventId: str,
    calendar: str = "primary"
) -> Dict[str, Any]:
    """Get a Google Calendar event by ID."""
    try:
        client = _get_client()
        event = client.get_event_by_id(event_id=eventId, calendar=calendar)
        return {
            "success": True,
            "event": {
                "id": event.id,
                "summary": event.summary,
                "start": event.start,
                "end": event.end,
                "description": event.description,
                "location": event.location,
                "attendees": event.attendees,
                "status": event.status,
                "created": event.created,
                "updated": event.updated,
                "creator": event.creator,
                "organizer": event.organizer
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_delete_event(
    eventId: str,
    calendar: str = "primary"
) -> Dict[str, Any]:
    """Delete a Google Calendar event."""
    try:
        client = _get_client()
        success = client.delete_event(event_id=eventId, calendar=calendar)
        return {"success": success, "message": f"Event {eventId} deleted successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_get_contacts(
    paginationParameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get Google contacts."""
    try:
        page_cursor = None
        if paginationParameters:
            page_cursor = paginationParameters.get("pageCursor")
        
        client = _get_client()
        result = client.get_contacts(page_cursor=page_cursor)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_search_contacts(query: str = "") -> Dict[str, Any]:
    """Search Google contacts."""
    try:
        client = _get_client()
        result = client.search_contacts(query=query)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_list_directory_people(
    paginationParameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """List directory people."""
    try:
        page_cursor = None
        if paginationParameters:
            page_cursor = paginationParameters.get("pageCursor")
        
        client = _get_client()
        result = client.list_directory_people(page_cursor=page_cursor)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_search_directory_people(
    query: str,
    paginationParameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Search directory people."""
    try:
        page_cursor = None
        if paginationParameters:
            page_cursor = paginationParameters.get("pageCursor")
        
        client = _get_client()
        result = client.search_directory_people(query=query, page_cursor=page_cursor)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_list_other_contacts(
    paginationParameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """List other contacts."""
    try:
        page_cursor = None
        if paginationParameters:
            page_cursor = paginationParameters.get("pageCursor")
        
        client = _get_client()
        result = client.list_other_contacts(page_cursor=page_cursor)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_search_other_contacts(query: str = "") -> Dict[str, Any]:
    """Search other contacts."""
    try:
        client = _get_client()
        result = client.search_other_contacts(query=query)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def google_calendar_get_availability(
    timeMin: str,
    timeMax: str,
    timeZone: str = "UTC",
    items: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Get calendar availability information."""
    try:
        client = _get_client()
        result = client.get_availability(
            time_min=timeMin,
            time_max=timeMax,
            time_zone=timeZone,
            items=items
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}