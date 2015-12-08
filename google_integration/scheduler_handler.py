from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from google_integration.fetch_event import sync_google_calendar
from google_integration.fetch_contact import sync_google_contact

def sync_with_google():
	for user in frappe.db.sql("""select name, sync_calendar, sync_contact  
		from `tabUser` where authenticated=1""", as_dict=True):
		frappe.set_user(user['name'])
		
		if user.get("sync_calendar"):
			try:
				sync_google_calendar(user['name'])
			except:
				frappe.db.set_value("User", user['name'], "sync_contact", 0)
				frappe.throw(_("Something went wrong in contact syncing"))
	
		if user.get("sync_contact"):
			try:
				sync_google_contact(user['name'])
			except:
				frappe.db.set_value("User", user['name'], "sync_contact", 0)
				frappe.throw(_("Something went wrong in contact syncing"))
