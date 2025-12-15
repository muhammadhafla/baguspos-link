# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _


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
		
		# Create indexes for performance
		create_database_indexes()
		
		# Setup initial data
		setup_initial_data()
		
		frappe.db.commit()
		
		frappe.log_error("ERPNext POS Integration installation completed successfully", "POS Installation")
		
		return True
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error during POS installation: {str(e)}", "POS Installation Error")
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
		{
			"dt": "Sales Invoice",
			"fieldname": "pos_receipt_number",
			"fieldtype": "Data",
			"label": "POS Receipt Number",
			"description": "POS-generated receipt number",
			"insert_after": "pos_transaction_id"
		},
		{
			"dt": "Sales Invoice",
			"fieldname": "pos_sync_status",
			"fieldtype": "Select",
			"options": "Pending\nSynced\nFailed\nManual Review",
			"default": "Pending",
			"label": "POS Sync Status",
			"insert_after": "pos_receipt_number"
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
		},
		{
			"dt": "Item",
			"fieldname": "pos_display_order",
			"fieldtype": "Int",
			"label": "POS Display Order",
			"description": "Order for display in POS interface",
			"insert_after": "is_pos_item"
		}
	]
	
	for field in custom_fields:
		if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
			try:
				doc = frappe.get_doc({
					"doctype": "Custom Field",
					"dt": field["dt"],
					"fieldname": field["fieldname"],
					"fieldtype": field["fieldtype"],
					"label": field["label"],
					"description": field.get("description", ""),
					"default": field.get("default"),
					"unique": field.get("unique", 0),
					"options": field.get("options"),
					"insert_after": field.get("insert_after")
				})
				doc.insert(ignore_permissions=True)
				frappe.db.commit()
			except Exception as e:
				frappe.log_error(f"Error creating custom field {field['fieldname']}: {str(e)}", "POS Installation")


def setup_initial_config():
	"""Setup initial configuration settings"""
	
	try:
		# Create POS Integration Settings document if it doesn't exist
		if not frappe.db.exists("DocType", "POS Integration Settings"):
			# Create the DocType first
			doc = frappe.get_doc({
				"doctype": "DocType",
				"name": "POS Integration Settings",
				"module": "POS Integration",
				"is_submittable": 0,
				"naming_rule": "By fieldname",
				"autoname": "field:",
				"fields": [
					{"fieldname": "enable_offline_mode", "fieldtype": "Check", "label": "Enable Offline Mode", "default": 1},
					{"fieldname": "cache_ttl", "fieldtype": "Int", "label": "Cache TTL (seconds)", "default": 300},
					{"fieldname": "max_retry_attempts", "fieldtype": "Int", "label": "Max Retry Attempts", "default": 3},
					{"fieldname": "enable_logging", "fieldtype": "Check", "label": "Enable Logging", "default": 1},
					{"fieldname": "api_rate_limit", "fieldtype": "Int", "label": "API Rate Limit (requests/minute)", "default": 100}
				]
			})
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
		
		# Create settings instance
		if not frappe.db.exists("POS Integration Settings", "POS Integration Settings"):
			settings_doc = frappe.get_doc({
				"doctype": "POS Integration Settings",
				"name": "POS Integration Settings",
				"enable_offline_mode": 1,
				"cache_ttl": 300,
				"max_retry_attempts": 3,
				"enable_logging": 1,
				"api_rate_limit": 100
			})
			settings_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			
	except Exception as e:
		frappe.log_error(f"Error setting up initial config: {str(e)}", "POS Installation")


def create_default_pricing_rules():
	"""Create default pricing rules for testing"""
	
	default_rules = [
		{
			"rule_name": "Default POS Base Price",
			"pricing_type": "Base Price",
			"priority_level": "1",
			"base_price": 0,
			"is_active": 1,
			"rule_name": "Default base pricing rule"
		}
	]
	
	for rule_data in default_rules:
		try:
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
		except Exception as e:
			frappe.log_error(f"Error creating pricing rule {rule_data['rule_name']}: {str(e)}", "POS Installation")


def setup_permissions():
	"""Setup role permissions for POS integration"""
	
	try:
		roles = ["System Manager", "POS User", "ERPNext Manager"]
		
		for role in roles:
			if frappe.db.exists("Role", role):
				# Add permissions for custom doctypes
				for doctype in ["POS Device", "POS Pricing Rule", "POS Sync Log"]:
					frappe.permissions.add_permission(doctype, role)
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error setting up permissions: {str(e)}", "POS Installation")


def create_database_indexes():
	"""Create database indexes for better performance"""
	
	indexes = [
		"CREATE INDEX IF NOT EXISTS idx_pos_device_branch ON `tabPOS Device`(branch)",
		"CREATE INDEX IF NOT EXISTS idx_pos_device_status ON `tabPOS Device`(sync_status)",
		"CREATE INDEX IF NOT EXISTS idx_pos_pricing_active ON `tabPOS Pricing Rule`(is_active, priority_level)",
		"CREATE INDEX IF NOT EXISTS idx_pos_pricing_item ON `tabPOS Pricing Rule`(item_code)",
		"CREATE INDEX IF NOT EXISTS idx_pos_sync_status ON `tabPOS Sync Log`(sync_status, creation)"
	]
	
	for index_sql in indexes:
		try:
			frappe.db.sql(index_sql)
		except Exception as e:
			frappe.log_error(f"Error creating index: {str(e)}", "POS Installation")


def setup_initial_data():
	"""Setup any initial data needed"""
	
	try:
		# Create default branch if none exists
		if not frappe.db.exists("Branch", "Main Branch"):
			branch_doc = frappe.get_doc({
				"doctype": "Branch",
				"branch": "Main Branch",
				"company": frappe.db.get_value("Company", {}, "name") or "Default Company"
			})
			branch_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			
	except Exception as e:
		frappe.log_error(f"Error setting up initial data: {str(e)}", "POS Installation")