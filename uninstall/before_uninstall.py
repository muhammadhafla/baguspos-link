# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def before_uninstall():
	"""Execute before app uninstallation to validate conditions"""
	
	# Check if user has admin permissions
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("You need System Manager permissions to uninstall this app."))
	
	# Check for active POS devices
	active_devices = frappe.db.count("POS Device", {"sync_status": ["in", ["Online", "Syncing"]]})
	if active_devices > 0:
		frappe.throw(_("Cannot uninstall while {0} POS devices are still active. Please deactivate all devices first.").format(active_devices))
	
	# Check for pending sync operations
	pending_syncs = frappe.db.count("POS Sync Log", {"sync_status": "Pending"})
	if pending_syncs > 0:
		frappe.throw(_("Cannot uninstall while {0} sync operations are pending. Please wait for sync to complete.").format(pending_syncs))
	
	# Log uninstallation start
	frappe.log_error("Starting ERPNext POS Integration uninstallation", "POS Uninstallation")
	
	# Create backup warning
	frappe.msgprint(_("Warning: This will remove all POS integration data including devices, pricing rules, and sync logs. Please backup your data before proceeding."), title="POS Integration Uninstallation", indicator="orange")
	
	return True