# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
import os

from apiclient.discovery import build
from httplib2 import Http
import oauth2client
import json 
from oauth2client import client
from oauth2client import tools
from oauth2client.client import Credentials, OAuth2Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.keyring_storage import Storage
from google_integration.utils import get_auth_cred_obj

oauth2_providers = {
	"google_connect": {
		"flow_params": {
			"name": "Google Integration",
			"authorize_url": "https://accounts.google.com/o/oauth2/auth",
			"access_token_url": "https://accounts.google.com/o/oauth2/token",
			"base_url": "https://www.googleapis.com",
		},

		"redirect_uri": "/api/method/google_integration.auth_handler.get_credentials",

		"auth_url_data": {
			# "approval_prompt":"force",
			'access_type': 'offline',
			"scope": 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/calendar https://www.google.com/m8/feeds',
			"response_type": "code"
		},

		# relative to base_url
		"api_endpoint": "oauth2/v3/calendar"
	},
}

def get_oauth2_authorize_url(provider):
	flow = get_oauth2_flow(provider)
	# relative to absolute url
	data = { "redirect_uri": get_redirect_uri(provider) }

	# additional data if any
	data.update(oauth2_providers[provider].get("auth_url_data", {}))

	return flow.get_authorize_url(**data)
	# return flow.step1_get_authorize_url(**data)

def get_oauth2_flow(provider):
	from rauth import OAuth2Service

	# get client_id and client_secret
	params = get_oauth_keys()

	# additional params for getting the flow
	params.update(oauth2_providers[provider]["flow_params"])

	# and we have setup the communication lines

	return OAuth2Service(**params)

def get_oauth_keys():
	"""get client_id and client_secret from database or conf"""

	social = frappe.get_doc("Google App Setup", "Google App Setup")

	if social.client_id and social.client_secret:
		return {
			"client_id":social.client_id,
			"client_secret":social.client_secret
		}
	else:
		frappe.msgprint("Please set Client Id and Client Secret.",raise_exception=1)

def get_redirect_uri(provider):
	redirect_uri = oauth2_providers[provider]["redirect_uri"]
	return frappe.utils.get_url(redirect_uri)

@frappe.whitelist()
def generate_token():
	# check storage for credentials
	credentials = get_auth_cred_obj(frappe.session.user)
	if not credentials or credentials.invalid:
		url = get_oauth2_authorize_url('google_connect')
		return {
			"url":url,
			"is_synced": False
		}

@frappe.whitelist()
def get_credentials(code):
	if code:
		params = get_oauth_keys()
		params.update({
			"scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/calendar https://www.google.com/m8/feeds",
			"redirect_uri": get_redirect_uri('google_connect'),
			"params": {
				"approval_prompt":"force",
				'access_type': 'offline',
				"response_type": "code"
			}
		})
		flow = OAuth2WebServerFlow(**params)
		credentials = flow.step2_exchange(code)
		
		frappe.db.sql("""update tabUser set authenticated=1, auth_token=%s 
			where name=%s""", (json.dumps(credentials.to_json()), frappe.session.user))		

		frappe.db.commit()
		
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/desk#Form/User/%s"%frappe.session.user
		