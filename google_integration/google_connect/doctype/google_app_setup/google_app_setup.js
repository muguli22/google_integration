frappe.ui.form.on("Google App Setup", "refresh", function(frm){
	if(frm.doc.__islocal){
		cur_frm.add_custom_button(__('Create project on Google Developer Console'),
			function() {  
				window.open("https://console.developers.google.com/")
			}, 
		'icon-sitemap').addClass("btn-primary")
	}
})