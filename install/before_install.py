# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def before_install():
	"""Execute before app installation to check prerequisites"""
	
	# Check ERPNext version compatibility
	erpnext_version = frappe.__version__
	if not erpnext_version:
		frappe.throw(_("ERPNext version not detected. This app requires ERPNext to be installed."))
	
	# Check if required modules exist
	required_modules = ["erpnext", "frappe"]
	for module in required_modules:
		if not frappe.db.exists("Module Def", module):
			frappe.throw(_("Required module '{0}' not found. Please install ERPNext first.").format(module))
	
	# Check database permissions
	if not frappe.db.sql("SELECT 1", as_dict=True):
		frappe.throw(_("Database connection failed. Please check database configuration."))
	
	# Check if user has admin permissions
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("You need System Manager permissions to install this app."))
	
	# Log installation start
	frappe.log_error("Starting ERPNext POS Integration installation", "POS Installation")
	
	return True