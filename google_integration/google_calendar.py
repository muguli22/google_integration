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

	credentials = get_credentials(user)
	
	eventsResult = get_gcal_events(credentials)
	events = eventsResult.get('items', [])

	if not events:
		frappe.msgprint("No Events to Sync")
	else:		
		for event in events:
			# check if event alreay synced if exist update else create new event
			existing_event_name = is_existing_event(event)
			if existing_event_name:
				update_event(existing_event_name, event)
			else:
				create_event(event)

def get_gcal_events(credentials):
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
	# frappe.errprint(event)
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
	# remove timezone from str_date
	import dateutil.parser
	return dateutil.parser.parse(str_date).strftime("%Y-%m-%d %H:%M:%S")

def is_existing_event(event):
	name = frappe.db.get_value("Event",{"google_event_id":event.get("id")},"name")
	return name

def get_formatted_updated_date(str_date):
	""" converting 2015-08-21T13:11:39.335Z string date to datetime """
	return datetime.strptime(str_date, "%Y-%m-%dT%H:%M:%S.%fZ")

def update_gcal_event(doc, method):
	# check if event newly created or updated
	event = None
	service = get_service_object(frappe.session.user)

	if doc.google_event_id:
		# update google calender event
		if not (doc.modified == doc.creation):
			event = get_google_event_dict(doc)
			event = service.events().update(calendarId='primary', eventId=doc.google_event_id, body=event).execute()

			if event: frappe.msgprint("Google Calender Event is updated successfully")
	else:
		# create new google calender event
		event = get_google_event_dict(doc)
		event = service.events().insert(calendarId='primary', body=event).execute()

		if event:
			frappe.db.set_value("Event", doc.name, "google_event_id", event.get("id"))
			frappe.msgprint("New Google Calender Event is created successfully")

def delete_gcal_event(doc, method):
	service = get_service_object(frappe.session.user)
	if doc.google_event_id:
		try:
			service.events().delete(calendarId='primary', eventId=doc.google_event_id).execute()
			frappe.msgprint("New Google Calender Event is deleted successfully")
			
		except Exception, e:
			frappe.msgprint("Error occured while deleting google event\nDeleting Event from Frappe, Please delete the google event manually")
			frappe.delete_doc("Event", doc.name)
			
		finally:
			# redirect to event list
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/desk#List/Event"

def get_google_event_dict(doc):
	start_date, end_date = get_gcal_date(doc.starts_on, doc.ends_on, doc.all_day)
	event = {
		"summary": doc.subject,
		"location": None,
		"description": doc.description,
		"start": start_date,
		"end": end_date,
		"recurrence":get_recurrence_rule(doc) if doc.repeat_this_event else [],
		"attendees": get_attendees(doc),
		"reminders":{
			'useDefault':False,
			'overrides': [
				{'method': 'email','minutes': 60}
			]
		}
	}
	return event

def get_gcal_date(starts_on, ends_on=None, is_all_day=0):
	gcal_date = {}
	gcal_starts_on = get_dates_in_gcal_format(starts_on, is_all_day)
	gcal_ends_on = get_dates_in_gcal_format(ends_on if ends_on else starts_on, is_all_day)

	return gcal_starts_on, gcal_ends_on

def get_dates_in_gcal_format(date, is_all_day=0):
	str_date = str(date) if isinstance(date, datetime) else date
	
	if is_all_day:
		return {'date': datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")}
	else:
		timezone = frappe.db.get_value("System Settings", None, "time_zone")
	
		if timezone:
			return {
				'dateTime':datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%dT%H:%M:%S"),
				'timeZone': timezone
			}
		else:
			frappe.msgprint("Please set Time Zone under Setup > Settings > System Settings", raise_exception=1)

def get_attendees(doc):	
	emails = []
	if doc.roles:
		roles, attendees = [], []

		for ch_doc in doc.roles:
			if ch_doc.role:
				roles.append(str(ch_doc.role))
			if ch_doc.attendees:
				attendees.extend(eval(ch_doc.attendees))

		if roles:
			condition = "('%s')" % "','".join(tuple(roles))

			result_set = frappe.db.sql("""SELECT DISTINCT email FROM tabUser WHERE name <> '%s' AND name IN
				(SELECT DISTINCT parent FROM tabUserRole WHERE role in %s)"""%(frappe.session.user, condition), as_dict=True)

			emails = result_set if result_set else []

		if attendees:
			emails.extend(attendees)

	return emails

def get_recurrence_rule(doc):
	"""Recurring Event not implemeted."""
		
	if doc.repeat_on == "Every Day": 
		rule = ["RRULE:FREQ=DAILY;BYDAY=%s"%(get_by_day_string(doc))]
		
	elif doc.repeat_on == "Every Week": 
		rule = ["RRULE:FREQ=WEEKLY"]
	elif doc.repeat_on == "Every Month": 
		rule = ["RRULE:FREQ=MONTHLY"]
	else: 
		rule = ["RRULE:FREQ=YEARLY;UNTIL=%s"%(until)]
	
	if doc.repeat_till:
		until = datetime.strptime(doc.repeat_till, '%Y-%m-%d').strftime("%Y%m%dT%H%M%SZ")
		rule = ["%s;UNTIL=%s"%(rule[0],until)]
		
	return rule
	
def get_by_day_string(doc):
	by_days = []
	if doc.sunday : by_days.append("SU")
	if doc.monday : by_days.append("MO")
	if doc.tuesday : by_days.append("TU")
	if doc.wednesday : by_days.append("WE")
	if doc.thursday : by_days.append("TH")
	if doc.friday : by_days.append("FR")
	if doc.saturday : by_days.append("SA")

	return "%s" % ",".join(by_days)