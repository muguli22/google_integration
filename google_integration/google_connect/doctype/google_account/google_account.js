frappe.ui.form.on("Google Account", "refresh", function(frm){
	if(!frm.doc.__islocal && !frm.doc.authenticated){
		cur_frm.add_custom_button(__('Authenticate'),
			function() {  
				frappe.call({
					method:"google_integration.google_connect.doctype.google_account.google_account.generate_token",
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
	if(!frm.doc.__islocal && frm.doc.sync_google_calendar && frm.doc.authenticated) {
		cur_frm.add_custom_button(__("Sync Calendar"), sync_calendar)
	}
	
	if(!frm.doc.__islocal && frm.doc.sync_google_contact && frm.doc.authenticated) {
		cur_frm.add_custom_button(__("Sync Contact"), sync_contact)
	}
})

sync_calendar = function() {
	frappe.call({
		method: "google_integration.fetch_google_calendar.sync_google_calendar",
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
	alert("contact")
}