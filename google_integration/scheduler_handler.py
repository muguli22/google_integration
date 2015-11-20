from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

def sync_all():
	for user in frappe.db.sql("""select gmail_id from `tabSync Configuration` 
		where sync_google_calendar=1 """%(mode),as_list=True): 
		sync_google_calendar(user[0])
