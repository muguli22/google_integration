###Configuration Steps


####Enable Google Calendar and Contact API
1. Create a project on [Google Developer Consle](https://developers.google.com/console/help/new/)
	<img class="screenshot" src="{{ docs_base_url }}/assets/img/create-project-on-google.png">

1. <b>Set redirect uri as,</b> `{Your Server Url}/api/method/gcal.gcal_sync.doctype.sync_configuration.sync_configuration.get_credentials`
    <img class="screenshot" src="{{ docs_base_url }}/assets/img/redirect-uri.png">
    <b>JavaScript origins : </b> `{Your Server Url}`
    <img class="screenshot" src="{{ docs_base_url }}/assets/img/javascript-origin.png">

1. Enable calendar and contact api's for newly created project
	<img class="screenshot" src="{{ docs_base_url }}/assets/img/api-screen.png">
	
 ---
 
####Setup Google Project Credentials on Google Integration App

1. `Setup > Help > Google App Setup` 
	Set Client secret and client id in erpnext from google project
	<img class="screenshot" src="{{ docs_base_url }}/assets/img/frappe-cred-screen.png">

---

####Setup individual profile
1. `Setup > Integration > Google Account`, setup your google account by creating Oauth token.
    <img class="screenshot" src="{{ docs_base_url }}/assets/img/setup-account.png">

1. Enable sync option by setting `Sync Google Calendar` and `Sync Google Contact`
    <img class="screenshot" src="{{ docs_base_url }}/assets/img/setup-sync-options.png">
