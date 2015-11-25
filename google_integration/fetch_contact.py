# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data
from frappe.utils import cint, get_datetime
from dateutil.relativedelta import relativedelta
from google_integration.utils import get_credentials, get_service_object, \
	get_rule_dict, get_gd_client, get_formatted_update_date

@frappe.whitelist()
def sync_google_contact(user=None):
	if not user:
		user = frappe.session.user
		
	feed = get_feed(user)
	for i, entry in enumerate(feed.entry):
		if entry.name:
			contact = get_contact(entry)
			if not contact:
				create_contact(entry)
			else:
				update_contact(entry, contact)
					
def get_feed(user):
	""" return contacts in xml form"""
	gd_client = get_gd_client(user)
	try:
		feed = gd_client.GetContacts()
		return feed
	except:
		frappe.db.set_value("Google Account", user, "authenticated", 0)
		frappe.db.commit()
		frappe.throw(_("Invalid Access Token"))
	
def create_contact(entry):
	try:
		frappe.get_doc(get_contact_dict(entry)).insert()
	except:
		pass

def update_contact(entry, name):
	contact = frappe.get_doc("Contact", name)
	if contact.modified != get_formatted_update_date(entry.updated.text):
		contact.update(get_contact_dict(entry))
		contact.save()
	
def get_contact_dict(entry):
	contact = {
		"doctype": "Contact",
		"google_contact_id": entry.id.text,
		"first_name": entry.name.given_name.text,
		"last_name": entry.name.__dict__.get("family_name").text
	}

	for email in entry.email:
		contact.update({
			"email_id": email.address
		})
		break

	for phone in entry.phone_number:
		contact.update({
			"phone":phone.text
		})
		break
	
	return contact
	
def get_contact(entry):
	return frappe.db.get_value("Contact", {"google_contact_id": entry.id.text}, "name")