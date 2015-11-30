frappe.ui.form.on("User", "refresh", function(frm){
	if(!frm.doc.__islocal && !frm.doc.authenticated){
		cur_frm.add_custom_button(__('Authenticate'),
			function() {  
				frappe.call({
					method:"google_integration.auth_handler.generate_token",
					freeze: true,
					callback:function(r){
						if(!r.exc && r.message){
							if(r.message.url) {
								window.location.replace(r.message.url);
							}								
						}
					}
				})
			}, 'icon-sitemap')
	}
	if(!frm.doc.__islocal && frm.doc.authenticated) {
		cur_frm.add_custom_button(__("Sync Calendar"), sync_calendar)
	}
	
	if(!frm.doc.__islocal && frm.doc.authenticated) {
		cur_frm.add_custom_button(__("Sync Contact"), sync_contact)
	}
})

sync_calendar = function() {
	frappe.call({
		method: "google_integration.fetch_event.sync_google_calendar",
		args:{"user": user},
		freeze: true,
		callback: function(r){
			if(!r.exc) {
				frappe.msgprint(__("Calendar has been synced"))
			}
		}
	})
}

sync_contact = function() {
	frappe.call({
		method: "google_integration.fetch_contact.sync_google_contact",
		args:{"user": user},
		freeze: true,
		callback: function(r){
			if(!r.exc) {
				frappe.msgprint(__("Contact(s) has been synced"))
			}
		}
	})
}