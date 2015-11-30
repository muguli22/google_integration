from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from datetime import datetime, timedelta, date
from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client.client import Credentials
from oauth2client.keyring_storage import Storage

def sync_activated(user=None):
	doc = frappe.get_doc("User", user or frappe.session.user)

	if doc.authenticated:
		return True
			
	return False
	
def get_credentials(user):
	store = Storage('User', user)
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

def get_rule_dict(recurring_rule):
	""" 
		get rule dict for google calendar recurring rule
		eg: recurring_rule = RRULE:FREQ=DAILY;COUNT=5
		o/p : {'FREQ': 'DAILY', 'COUNT': 5}
	"""
	rule_dict = {}
	rule_details = recurring_rule[6:].split(';')
	
	for param in rule_details:
		temp_list = param.split("=")
		rule_dict[temp_list[0]] = temp_list[1]
	
	return rule_dict

def get_gd_client(user):
	import atom.data
	import gdata.data
	import gdata.contacts.client
	import gdata.contacts.data
	
	gd_client = gdata.contacts.client.ContactsClient(source='Google Integration')
	cred = get_credentials(user)
	auth = gdata.gauth.OAuth2TokenFromCredentials(cred)
	gd_client = auth.authorize(gd_client)
	return gd_client
	
def get_formatted_update_date(str_date):
	""" converting 2015-08-21T13:11:39.335Z string date to datetime """
	return datetime.strptime(str_date, "%Y-%m-%dT%H:%M:%S.%fZ")