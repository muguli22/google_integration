# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "google_integration"
app_title = "Google Connect"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Application will enable syncing of Calendar and Contacts from ERPNext to Google and vice versa."
app_icon = "icon-google-plus"
app_color = "#dd4b39"
app_email = "info@frappe.io"
app_version = "0.0.1"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/google_integration/css/google_integration.css"
# app_include_js = "/assets/google_integration/js/google_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/google_integration/css/google_integration.css"
# web_include_js = "/assets/google_integration/js/google_integration.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "google_integration.install.before_install"
# after_install = "google_integration.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "google_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Event": {
		"on_update": "google_integration.google_calendar.update_gcal_event",
		"on_trash": "google_integration.google_calendar.delete_gcal_event"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"google_integration.tasks.all"
# 	],
# 	"daily": [
# 		"google_integration.tasks.daily"
# 	],
# 	"hourly": [
# 		"google_integration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"google_integration.tasks.weekly"
# 	]
# 	"monthly": [
# 		"google_integration.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "google_integration.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "google_integration.event.get_events"
# }

