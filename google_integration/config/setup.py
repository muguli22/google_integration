from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Integrations"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Google App Setup",
					"description": _("Connect Shopify with ERPNext"),
					"hide_count": True
				}
			]
		}
	]
