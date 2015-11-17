from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from datetime import datetime, timedelta, date
from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client.client import Credentials
from oauth2client.keyring_storage import Storage

def sync_all():
	# get the list of user with
	users = get_users_by_sync_optios('Hourly')
	sych_users_calender(users)

def sync_hourly():
	# get the list of user having sync option as "hourly"
	users = get_users_by_sync_optios('Hourly')
	sych_users_calender(users)

def sync_daily():
	# get the list of user having sync option as "Daily"
	users = get_users_by_sync_optios('Daily')
	sych_users_calender(users)

def sync_weekly():
	# get the list of user having sync option as "Weekly"
	users = get_users_by_sync_optios('Weekly')
	sych_users_calender(users)

def sync_monthly():
	# get the list of user having sync option as "Monthly"
	users = get_users_by_sync_optios('Monthly')
	sych_users_calender(users)

def get_users_by_sync_optios(mode):
	return frappe.db.sql("select gmail_id from `tabSync Configuration` where is_sync=1 and sync_options='%s'"%(mode),as_list=True)

def sych_users_calender(users):
	for user in users:
		# get user credentials from keyring storage
		store = Storage('GCal', user[0])
		credentials = store.get()
		if not credentials or credentials.invalid:
			# invalid credentials
			print "invalid credentials", user[0]
		else:
			sync_google_calendar(credentials)
			
def get_credentials(user):
	store = Storage('Google Account', user)
	credentials = store.get()
	
	return credentials
	
def get_service_object(user):
	# get google credentials from storage
	service = None
	credentials = get_credentials(user)
	if not credentials or credentials.invalid:
		# get credentials
		frappe.throw("Invalid Credentials")
	else:
		service = build('calendar', 'v3', http=credentials.authorize(Http()))

	return service