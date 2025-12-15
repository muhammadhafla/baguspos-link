# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def before_install():
	"""Execute before app installation"""
	frappe.log_error("Starting ERPNext POS Integration installation", "POS Installation")


def after_install():
	"""Execute after successful app installation"""
	try:
		# Create custom fields
		create_custom_fields()
		
		# Setup initial configurations
		setup_initial_config()
		
		# Create default pricing rules
		create_default_pricing_rules()
		
		# Setup permissions
		setup_permissions()
		
		frappe.log_error("ERPNext POS Integration installation completed successfully", "POS Installation")
		
	except Exception as e:
		frappe.log_error(f"Error during POS installation: {str(e)}", "POS Installation Error")
		raise


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
		
		frappe.log_error("ERPNext POS Integration uninstallation completed", "POS Uninstallation")
		
	except Exception as e:
		frappe.log_error(f"Error during POS uninstallation: {str(e)}", "POS Uninstallation Error")
		raise


def create_custom_fields():
	"""Create custom fields for ERPNext integration"""
	custom_fields = [
		# Sales Invoice custom fields
		{
			"dt": "Sales Invoice",
			"fieldname": "pos_branch_id",
			"fieldtype": "Data",
			"label": "POS Branch ID",
			"description": "Original POS branch identifier",
			"insert_after": "customer"
		},
		{
			"dt": "Sales Invoice",
			"fieldname": "pos_device_id",
			"fieldtype": "Data",
			"label": "POS Device ID",
			"description": "Source POS device identifier",
			"insert_after": "pos_branch_id"
		},
		{
			"dt": "Sales Invoice",
			"fieldname": "pos_transaction_id",
			"fieldtype": "Data",
			"label": "POS Transaction ID",
			"unique": 1,
			"description": "Unique POS transaction identifier",
			"insert_after": "pos_device_id"
		},
		
		# Item custom fields
		{
			"dt": "Item",
			"fieldname": "is_pos_item",
			"fieldtype": "Check",
			"default": 1,
			"label": "Is POS Item",
			"description": "Item available for POS transactions",
			"insert_after": "is_stock_item"
		}
	]
	
	for field in custom_fields:
		if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
			doc = frappe.get_doc({
				"doctype": "Custom Field",
				"dt": field["dt"],
				"fieldname": field["fieldname"],
				"fieldtype": field["fieldtype"],
				"label": field["label"],
				"description": field.get("description", ""),
				"default": field.get("default"),
				"unique": field.get("unique", 0),
				"insert_after": field.get("insert_after")
			})
			doc.insert(ignore_permissions=True)
	
	frappe.db.commit()


def setup_initial_config():
	"""Setup initial configuration settings"""
	# Create system settings for POS integration
	doc = frappe.get_doc({
		"doctype": "POS Integration Settings",
		"enable_offline_mode": 1,
		"cache_ttl": 300,
		"max_retry_attempts": 3,
		"enable_logging": 1
	})
	
	if not frappe.db.exists("POS Integration Settings", "POS Integration Settings"):
		doc.insert(ignore_permissions=True)
		frappe.db.commit()


def create_default_pricing_rules():
	"""Create default pricing rules for testing"""
	default_rules = [
		{
			"rule_name": "Default POS Price",
			"pricing_type": "Base Price",
			"priority_level": "1",
			"base_price": 0,
			"is_active": 1
		}
	]
	
	for rule_data in default_rules:
		if not frappe.db.exists("POS Pricing Rule", {"rule_name": rule_data["rule_name"]}):
			doc = frappe.get_doc({
				"doctype": "POS Pricing Rule",
				"rule_name": rule_data["rule_name"],
				"pricing_type": rule_data["pricing_type"],
				"priority_level": rule_data["priority_level"],
				"base_price": rule_data["base_price"],
				"is_active": rule_data["is_active"]
			})
			doc.insert(ignore_permissions=True)
	
	frappe.db.commit()


def setup_permissions():
	"""Setup role permissions for POS integration"""
	roles = ["System Manager", "POS User"]
	
	for role in roles:
		if frappe.db.exists("Role", role):
			# Add permissions for custom doctypes
			frappe.permissions.add_permission("POS Device", role)
			frappe.permissions.add_permission("POS Pricing Rule", role)
			frappe.permissions.add_permission("POS Sync Log", role)
	
	frappe.db.commit()


def cleanup_custom_fields():
	"""Remove custom fields during uninstallation"""
	# Remove custom fields
	custom_field_names = frappe.get_all("Custom Field", 
		filters={"dt": ["in", ["Sales Invoice", "Item"]]},
		fields=["name"]
	)
	
	for field in custom_field_names:
		try:
			frappe.delete_doc("Custom Field", field.name)
		except Exception as e:
			frappe.log_error(f"Error removing custom field {field.name}: {str(e)}", "POS Cleanup")
	
	frappe.db.commit()


def cleanup_configurations():
	"""Remove configuration settings during uninstallation"""
	# Remove POS Integration Settings
	if frappe.db.exists("POS Integration Settings", "POS Integration Settings"):
		try:
			frappe.delete_doc("POS Integration Settings", "POS Integration Settings")
		except Exception as e:
			frappe.log_error(f"Error removing POS settings: {str(e)}", "POS Cleanup")
	
	# Remove default pricing rules
	default_rules = frappe.get_all("POS Pricing Rule", 
		filters={"rule_name": ["like", "Default%"]},
		fields=["name"]
	)
	
	for rule in default_rules:
		try:
			frappe.delete_doc("POS Pricing Rule", rule.name)
		except Exception as e:
			frappe.log_error(f"Error removing pricing rule {rule.name}: {str(e)}", "POS Cleanup")
	
	frappe.db.commit()