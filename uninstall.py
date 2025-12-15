# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def before_uninstall():
	"""Execute before app uninstallation"""
	frappe.log_error("Starting ERPNext POS Integration uninstallation", "POS Uninstallation")


def after_uninstall():
	"""Execute after successful app uninstallation"""
	try:
		# Clean up custom fields
		cleanup_custom_fields()
		
		# Remove configurations
		cleanup_configurations()
		
		# Remove indexes
		cleanup_indexes()
		
		frappe.db.commit()
		
		frappe.log_error("ERPNext POS Integration uninstallation completed", "POS Uninstallation")
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error during POS uninstallation: {str(e)}", "POS Uninstallation Error")
		raise


def cleanup_custom_fields():
	"""Remove custom fields during uninstallation"""
	
	try:
		# Remove custom fields
		custom_field_names = frappe.get_all("Custom Field", 
			filters={"dt": ["in", ["Sales Invoice", "Item"]]},
			fields=["name"]
		)
		
		for field in custom_field_names:
			try:
				frappe.delete_doc("Custom Field", field.name)
			except Exception as e:
				frappe.log_error(f"Error removing custom field {field.name}: {str(e)}", "POS Uninstallation")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error cleaning up custom fields: {str(e)}", "POS Uninstallation")


def cleanup_configurations():
	"""Remove configuration settings during uninstallation"""
	
	try:
		# Remove POS Integration Settings
		if frappe.db.exists("DocType", "POS Integration Settings"):
			if frappe.db.exists("POS Integration Settings", "POS Integration Settings"):
				try:
					frappe.delete_doc("POS Integration Settings", "POS Integration Settings")
				except Exception as e:
					frappe.log_error(f"Error removing POS settings: {str(e)}", "POS Uninstallation")
		
		# Remove default pricing rules
		default_rules = frappe.get_all("POS Pricing Rule", 
			filters={"rule_name": ["like", "Default%"]},
			fields=["name"]
		)
		
		for rule in default_rules:
			try:
				frappe.delete_doc("POS Pricing Rule", rule.name)
			except Exception as e:
				frappe.log_error(f"Error removing pricing rule {rule.name}: {str(e)}", "POS Uninstallation")
		
		# Remove DocType if no other instances exist
		if frappe.db.exists("DocType", "POS Integration Settings"):
			doc_count = frappe.db.count("POS Integration Settings")
			if doc_count == 0:
				try:
					frappe.delete_doc("DocType", "POS Integration Settings")
				except Exception as e:
					frappe.log_error(f"Error removing POS Integration Settings DocType: {str(e)}", "POS Uninstallation")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error cleaning up configurations: {str(e)}", "POS Uninstallation")


def cleanup_indexes():
	"""Remove database indexes created during installation"""
	
	indexes = [
		"DROP INDEX IF EXISTS idx_pos_device_branch ON `tabPOS Device`",
		"DROP INDEX IF EXISTS idx_pos_device_status ON `tabPOS Device`",
		"DROP INDEX IF EXISTS idx_pos_pricing_active ON `tabPOS Pricing Rule`",
		"DROP INDEX IF EXISTS idx_pos_pricing_item ON `tabPOS Pricing Rule`",
		"DROP INDEX IF EXISTS idx_pos_sync_status ON `tabPOS Sync Log`"
	]
	
	for index_sql in indexes:
		try:
			frappe.db.sql(index_sql)
		except Exception as e:
			frappe.log_error(f"Error dropping index: {str(e)}", "POS Uninstallation")