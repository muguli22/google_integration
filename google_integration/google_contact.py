from __future__ import unicode_literals
import frappe
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data
from frappe.utils import cint, get_datetime
from dateutil.relativedelta import relativedelta
from google_integration.utils import get_credentials, get_service_object, get_rule_dict, get_gd_client

def create_or_update_contact(doc, method):
	"""triggered by hook on update of contact"""
	if not doc.google_contact_id:
		create_contact(doc)
	else:
		if doc.creation != doc.modified:
			update_contact(doc)
	
def create_contact(doc):
	"""if google_contact_id is not exist then create contact"""
	gd_client = get_gd_client(frappe.session.user)
	
	new_contact = gdata.contacts.data.ContactEntry()
	new_contact.name = gdata.data.Name(given_name=gdata.data.GivenName(text=doc.first_name),
		family_name=gdata.data.FamilyName(text=doc.last_name))
		
	new_contact.email.append(gdata.data.Email(address=doc.email_id, primary='true', 
		rel=gdata.data.WORK_REL, display_name=doc.first_name))
		
	new_contact.phone_number.append(gdata.data.PhoneNumber(text=doc.phone, rel=gdata.data.WORK_REL, 
		primary='true'))
		
	contact_entry = gd_client.CreateContact(new_contact)
	
	frappe.db.set_value("Contact", doc.name, "google_contact_id", contact_entry.id.text)

def update_contact(doc):
	"""update existing contact"""
	gd_client = get_gd_client(frappe.session.user)
	
	contact_entry = gd_client.GetContact(doc.google_contact_id)
	contact_entry.name.given_name.text = doc.first_name
	
	if doc.last_name:
		if contact_entry.name.__dict__.get("family_name"): 
			contact_entry.name.family_name.text = doc.last_name
		else:
			contact_entry.name = gdata.data.Name(given_name=gdata.data.GivenName(text=doc.first_name),
				family_name=gdata.data.FamilyName(text=doc.last_name))
			
	if contact_entry.email:
		contact_entry.email[0].address = doc.email_id
	else:
		contact_entry.email.append(gdata.data.Email(address=doc.email_id, primary='true', 
			rel=gdata.data.WORK_REL, display_name=doc.first_name))
			
	if contact_entry.phone_number:	
		contact_entry.phone_number[0].text = doc.phone
	else:
		if doc.phone:
			contact_entry.phone_number.append(gdata.data.PhoneNumber(text=doc.phone, rel=gdata.data.WORK_REL, 
				primary='true'))
	
	try:
		updated_contact = gd_client.Update(contact_entry)
	except gdata.client.RequestError, e:
		pass
		
def delete_contact(doc, method):
	"""delete contact from google"""
	gd_client = get_gd_client(frappe.session.user)
	contact = gd_client.GetContact(doc.google_contact_id)

	try:
		gd_client.Delete(contact)
	except gdata.client.RequestError, e:
		if e.status == 412:
			pass