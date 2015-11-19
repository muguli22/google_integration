from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from datetime import datetime, timedelta, date
from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client.client import Credentials
from oauth2client.keyring_storage import Storage
from google_integration.utils import get_credentials, get_service_object
import json

@frappe.whitelist()
def sync_google_calendar(user):
	"""initiates event syncing"""
	credentials = get_credentials(user)
	
	eventsResult = get_gcal_events(credentials)
	events = eventsResult.get('items', [])

	if not events:
		frappe.msgprint("No Events to Sync")
	else:		
		for event in events:
			check if event alreay synced if exist update else create new event
			existing_event_name = is_existing_event(event)
			if existing_event_name:
				update_event(existing_event_name, event)
			else:
				create_event(event)

def get_gcal_events(credentials):
	"""fetch event from google calendar"""
	now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	service = build('calendar', 'v3', http=credentials.authorize(Http()))
	eventsResult = service.events().list(
		calendarId='primary', timeMin=now).execute()
	events = eventsResult.get('items', [])
	return eventsResult

def create_event(event):
	e = frappe.new_doc("Event")
	e = set_values(e, event)
	e.save(ignore_permissions=True)

def update_event(name, event):
	e = frappe.get_doc("Event", name)

	if e.modified != get_formatted_updated_date(event['updated']):
		e = set_values(e, event)
		e.save(ignore_permissions=True)

def set_values(doc, event):
	"""create event dict from google event """
	doc.subject = event.get('summary')

	start_date = event['start'].get('dateTime', event['start'].get('date'))
	end_date = event['end'].get('dateTime', event['start'].get('date'))
			
	doc.starts_on = get_formatted_date(start_date)
	doc.ends_on = get_formatted_date(end_date)

	if not event['end'].get('dateTime'):
		doc.all_day = 1 
	else:
		doc.all_day = 0

	if not event.get('visibility'):
		doc.event_type = "Private"
	else:
		doc.event_type =  "Private" if event['visibility'] == "private" else "Public"
		
	doc.description = event.get("description")
	doc.is_gcal_event = 1
	doc.event_owner = event.get("organizer").get("email")
	doc.google_event_id = event.get("id")
	add_attendees(doc, event)

	return doc

def add_attendees(doc, event):
	"""add attendees from google event"""
	att = []
	event_attendees = ""
	if event.get("attendees"):
		for attendee in event.get("attendees"):

			att.append({"email": attendee.get("email")})
			event_attendees += "%s : %s \n"%(attendee.get("displayName") or "Name", attendee.get("email"))
	
	if not doc.get("roles"):
		doc.set("roles",[])
	
	if att:
		ch = doc.append('roles', {})
		ch.attendees = str(att)
		ch.event_attendees = str(event_attendees)

def get_formatted_date(str_date):
	""" convert iso date format to datetime """
	import dateutil.parser
	return dateutil.parser.parse(str_date).strftime("%Y-%m-%d %H:%M:%S")

def is_existing_event(event):
	"""return matching event name"""
	name = frappe.db.get_value("Event",{"google_event_id":event.get("id")},"name")
	return name

def get_formatted_updated_date(str_date):
	""" converting 2015-08-21T13:11:39.335Z string date to datetime """
	return datetime.strptime(str_date, "%Y-%m-%dT%H:%M:%S.%fZ")
		