from erpnext import __version__ as erpnext_version

app_name = "erpnext_pos_integration"
app_title = "ERPNext POS Integration"
app_publisher = "ERPNext Team"
app_description = "POS Integration with ERPNext for offline-first operations"
app_email = "support@erpnext.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_pos_integration/css/erpnext_pos_integration.css"
# app_include_js = "/assets/erpnext_pos_integration/js/erpnext_pos_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_pos_integration/css/erpnext_pos_integration.css"
# web_include_js = "/assets/erpnext_pos_integration/js/erpnext_pos_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_pos_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/page.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# add events and methods to standard events
# doc_events = {
#     "*": {
#         "on_update": "method",
#         "on_cancel": "method", 
#         "on_trash": "method"
#     }
# }

# Scheduler Events
# scheduler_events = {
#     "all": [
#         "erpnext_pos_integration.tasks.all"
#     ],
#     "daily": [
#         "erpnext_pos_integration.tasks.daily"
#     ],
#     "hourly": [
#         "erpnext_pos_integration.tasks.hourly"
#     ],
#     "weekly": [
#         "erpnext_pos_integration.tasks.weekly"
#     ],
#     "monthly": [
#         "erpnext_pos_integration.tasks.monthly"
#     ],
# }

# Testing
# before_install = "erpnext_pos_integration.install.before_install"
# after_install = "erpnext_pos_integration.install.after_install"

# Uninstallation
# before_uninstall = "erpnext_pos_integration.uninstall.before_uninstall"
# after_uninstall = "erpnext_pos_integration.uninstall.after_uninstall"

# Integration setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app, the app is added to the template
# before_app_install = "erpnext_pos_integration.utils.before_app_install"
# after_app_install = "erpnext_pos_integration.utils.after_app_install"

# Integration cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# before_app_uninstall = "erpnext_pos_integration.utils.before_app_uninstall"
# after_app_uninstall = "erpnext_pos_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_pos_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#     "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#     "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#     "*": {
#         "on_update": "method",
#         "on_cancel": "method",
#         "on_trash": "method"
#     }
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#     "all": [
#         "erpnext_pos_integration.tasks.all"
#     ],
#     "daily": [
#         "erpnext_pos_integration.tasks.daily"
#     ],
#     "hourly": [
#         "erpnext_pos_integration.tasks.hourly"
#     ],
#     "weekly": [
#         "erpnext_pos_integration.tasks.weekly"
#     ],
#     "monthly": [
#         "erpnext_pos_integration.tasks.monthly"
#     ],
# }

# Testing
# -------

# before_tests = "erpnext_pos_integration.install.before_tests"

# Overrides
# ---------
# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "erpnext_pos_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#     "Task": "erpnext_pos_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["erpnext_pos_integration.utils.before_request"]
# after_request = ["erpnext_pos_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["erpnext_pos_integration.utils.before_job"]
# after_job = ["erpnext_pos_integration.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": [
            "field_1",
            "field_2",
        ],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "redact_fields": [
            "field_1",
            "field_2",
        ],
        "partial": 1,
    }
]

# Automatically update python controller files with your configs
# controller_config = {
#     "erpnext_pos_integration": {
#         "events": {
#             "on_login": [
#                 "erpnext_pos_integration.events.login"
#             ]
#         }
#     }
# }

# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype}",
        "filter_by": "{filter_by}",
        "redact_fields": [
            "field_1",
            "field_2",
            "address_field"
        ],
        "partial": 1,
    }
]