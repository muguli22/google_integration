from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta, date
from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client.client import Credentials
from oauth2client.keyring_storage import Storage
from google_integration.utils import get_credentials, get_service_object, get_rule_dict,\
	get_formatted_update_date
from frappe.utils import cint, get_datetime
from dateutil.relativedelta import relativedelta

@frappe.whitelist()
def sync_google_calendar(user):
	"""initiates event syncing"""
	credentials = get_credentials(user)
	
	events = get_gcal_events(credentials, user)

	if not events:
		frappe.msgprint("No Events to Sync")
	else:		
		for event in events:
			existing_event_name = is_existing_event(event)
			if existing_event_name:
				update_event(existing_event_name, event)
			else:
				create_event(event)

def get_gcal_events(credentials, user):
	"""fetch event from google calendar"""
	try:
		now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
		service = build('calendar', 'v3', http=credentials.authorize(Http()))
		eventsResult = service.events().list(
			calendarId='primary', timeMin=now).execute()
		events = eventsResult.get('items', [])
		return events
	except:
		frappe.db.set_value("Google Account", user, "authenticated", 0)
		frappe.db.commit()
		frappe.throw(_("Invalid Access Token"))
		
def create_event(event):
	e = frappe.new_doc("Event")
	e = set_values(e, event)
	e.save(ignore_permissions=True)

def update_event(name, event):
	e = frappe.get_doc("Event", name)

	if e.modified != get_formatted_update_date(event['updated']):
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
	
	if event.get("recurrence"):
		doc.repeat_this_event = 1
		setup_recurring_event(doc, event.get("recurrence")[0])

	return doc

def add_attendees(doc, event):
	"""add attendees from google event"""
	att = []
	event_attendees = ""
	if event.get("attendees"):
		for attendee in event.get("attendees"):
			print attendee
			att.append({"email": attendee.get("email")})
			event_attendees += "%s : %s \n"%(attendee.get("displayName") or "Email Id", attendee.get("email"))
	
	doc.set("roles",[])
	print att
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

def setup_recurring_event(doc, recurring_rule):
	rule_dict = get_rule_dict(recurring_rule)
	frappe.errprint(rule_dict)
	if rule_dict['FREQ'] == "DAILY":
		setup_daily_rule(doc, rule_dict)
	
	if rule_dict['FREQ'] == "WEEKLY":
		setup_weekly_rule(doc, rule_dict)
		
	if rule_dict['FREQ'] == "MONTHLY":
		setup_monthly_rule(doc, rule_dict)
	
	if rule_dict['FREQ'] == "YEARLY":
		setup_yearly_rule(doc, rule_dict)
	
	set_repeat_till_date(doc, until=rule_dict.get("UNTIL"), count=cint(rule_dict.get("COUNT")), 
		event_type=rule_dict['FREQ'])

def setup_daily_rule(doc, rule_dict):
	count = cint(rule_dict.get("COUNT"), 7)
	doc.repeat_on = "Every Day"
	
	day_list = []
	if count >= 7:
		set_recurring_day(doc, ['monday', 'tuesday', 'wednesday', 
			'thursday', 'friday', 'saturday', 'sunday'])
		
	else:
		for i in range(0, cint(rule_dict.get("COUNT"))):
			next_day = get_datetime(doc.starts_on) + timedelta(days=i)
			day_list.append(next_day.strftime("%A").lower())
			
		set_recurring_day(doc, day_list)
		
def set_recurring_day(doc, day_list):
	for day in day_list:
		doc.set(day,1)
		
def setup_weekly_rule(doc, rule_dict):
	doc.repeat_on = "Every Week"
	
def setup_monthly_rule(doc, rule_dict):
	doc.repeat_on = "Every Month"
	
def setup_yearly_rule(doc, rule_dict):
	doc.repeat_on = "Every Year"

def set_repeat_till_date(doc, until=None, count=0, event_type="DAILY"):
	relativedelta_dict = {
		"DAILY": relativedelta(days=(count-1)),
		"WEEKLY": relativedelta(weeks=(count-1)),
		"MONTHLY": relativedelta(months=(count-1)),
		"YEARLY": relativedelta(years=(count-1))
	}
	
	if until:
		doc.repeat_till = datetime.strptime(until, "%Y%m%dT%H%M%SZ")
		
	if count:
		doc.repeat_till = get_datetime(doc.starts_on)+ relativedelta_dict[event_type]
	