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
	""" return event dict """
	start_date, end_date = get_formated_event_dates(doc.starts_on, doc.ends_on, doc.all_day)
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

def get_formated_event_dates(starts_on, ends_on=None, is_all_day=0):
	""" return formated event date """
	gcal_date = {}
	gcal_starts_on = get_dates_in_gcal_format(starts_on, is_all_day)
	gcal_ends_on = get_dates_in_gcal_format(ends_on if ends_on else starts_on, is_all_day)

	return gcal_starts_on, gcal_ends_on

def get_dates_in_gcal_format(date, is_all_day=0):
	"""returns date and timezone dict to create google event"""
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
	"""return attendees including all users for specified roles and attendees"""
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

			result_set = frappe.db.sql("""select distinct parent from tabUserRole 
				where parent not in('Guest', 'Administrator', '%s') 
					and role in %s""", (frappe.session.user, condition), as_dict=True)

			emails = result_set if result_set else []

		if attendees:
			emails.extend(attendees)

	return emails

def get_recurrence_rule(doc):
	"""return recurring rule based on repeat on"""
		
	if doc.repeat_on == "Every Day": 
		rule = get_daily_rule(doc)
		
	elif doc.repeat_on == "Every Week": 
		rule = get_weekly_rule(doc)
		
	elif doc.repeat_on == "Every Month": 
		rule = ["RRULE:FREQ=MONTHLY"]
		
	else: 
		rule = ["RRULE:FREQ=YEARLY"]
	
	return add_end_term_for_recurring_event(rule, doc)

def get_daily_rule(doc):
	"""Return daily rule for recurring event"""
	byday = get_byday(doc)
	
	if byday:
		return ["RRULE:FREQ=DAILY;BYDAY=%s"%(byday)]
	else:
		return ["RRULE:FREQ=DAILY"]

def get_byday(doc):
	from frappe.utils import get_datetime
	"""return day short name"""
	
	if doc.repeat_on == "Every Day": 
		by_days = []

		if doc.monday : by_days.append(get_day_short_name(index=0))
		if doc.tuesday : by_days.append(get_day_short_name(index=1))
		if doc.wednesday : by_days.append(get_day_short_name(index=2))
		if doc.thursday : by_days.append(get_day_short_name(index=3))
		if doc.friday : by_days.append(get_day_short_name(index=4))
		if doc.saturday : by_days.append(get_day_short_name(index=5))
		if doc.sunday : by_days.append(get_day_short_name(index=6))

		return "%s" % ",".join(by_days)
	
	else:
		return get_day_short_name(day=get_datetime(doc.starts_on).strftime("%A"))
		
def add_end_term_for_recurring_event(rule, doc):
	""" return rule by adding end date"""
	if doc.repeat_till:
		until = datetime.strptime(doc.repeat_till, '%Y-%m-%d').strftime("%Y%m%dT%H%M%SZ")
		rule = ["%s;UNTIL=%s"%(rule[0],until)]
	
	return rule

def get_weekly_rule(doc):
	return ["RRULE:FREQ=WEEKLY;BYDAY=%s"%get_byday(doc)]

def get_day_short_name(day=None, index=None):
	"""return day short name"""
	import calendar
	
	day_dict = {"Monday": "MO", "Tuesday":"TU", "Wednesday":"WE", "Thursday": "TH", 
		"Friday": "FR", "Saturday": "SA", "Sunday": "SU"}
	
	if day:
		return day_dict[day]
	
	if index==0 or index:
		return day_dict[calendar.day_name[index]]
