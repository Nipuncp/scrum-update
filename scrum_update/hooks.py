app_name = "scrum_update"
app_title = "Scrum Update"
app_publisher = "nipuncp123@gmail.com"
app_description = "App to ease scrum update"
app_email = "nipuncp123@gmail.com"
app_license = "mit"

# Inject Scrum claim button into the Task form
doctype_js = {"Task": "public/js/task.js"}

# Add a read-only "Times Claimed" counter to the Task form
custom_fields = {
	"Task": [
		{
			"fieldname": "scrum_claim_count",
			"label": "Times Claimed",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "status",
			"default": "0",
			"description": "Number of times this task has been claimed in a daily scrum",
		}
	]
}

# Sync Scrum Claim status whenever a Task is saved
doc_events = {
	"Task": {
		"on_update": "scrum_update.scrum_update.doctype.scrum_claim.scrum_claim.sync_claims_on_task_update",
	}
}

# Nightly cleanup of stale claims
scheduler_events = {
	"daily": [
		"scrum_update.scrum_update.tasks.expire_old_claims",
	]
}

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "scrum_update",
# 		"logo": "/assets/scrum_update/logo.png",
# 		"title": "Scrum Update",
# 		"route": "/scrum_update",
# 		"has_permission": "scrum_update.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/scrum_update/css/scrum_update.css"
# app_include_js = "/assets/scrum_update/js/scrum_update.js"

# include js, css files in header of web template
# web_include_css = "/assets/scrum_update/css/scrum_update.css"
# web_include_js = "/assets/scrum_update/js/scrum_update.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "scrum_update/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "scrum_update/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "scrum_update.utils.jinja_methods",
# 	"filters": "scrum_update.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "scrum_update.install.before_install"
# after_install = "scrum_update.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "scrum_update.uninstall.before_uninstall"
# after_uninstall = "scrum_update.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "scrum_update.utils.before_app_install"
# after_app_install = "scrum_update.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "scrum_update.utils.before_app_uninstall"
# after_app_uninstall = "scrum_update.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "scrum_update.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"scrum_update.tasks.all"
# 	],
# 	"daily": [
# 		"scrum_update.tasks.daily"
# 	],
# 	"hourly": [
# 		"scrum_update.tasks.hourly"
# 	],
# 	"weekly": [
# 		"scrum_update.tasks.weekly"
# 	],
# 	"monthly": [
# 		"scrum_update.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "scrum_update.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "scrum_update.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "scrum_update.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "scrum_update.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["scrum_update.utils.before_request"]
# after_request = ["scrum_update.utils.after_request"]

# Job Events
# ----------
# before_job = ["scrum_update.utils.before_job"]
# after_job = ["scrum_update.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"scrum_update.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

