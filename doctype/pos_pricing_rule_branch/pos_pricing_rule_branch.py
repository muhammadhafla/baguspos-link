# Copyright (c) 2025, Muhammad Hafla and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class POSPricingRuleBranch(Document):
    def validate(self):
        """Validate branch data"""
        self.validate_branch_id()
        self.set_branch_name()
        
    def validate_branch_id(self):
        """Validate branch ID format and uniqueness"""
        if not self.branch_id:
            frappe.throw(_("Branch ID is required"))
            
        # Check if branch ID already exists in this pricing rule
        parent_doc = frappe.get_doc("POS Pricing Rule", self.parent)
        if parent_doc:
            existing_branches = [item.branch_id for item in parent_doc.branch_conditions 
                               if item.name != self.name and item.branch_id == self.branch_id]
            if existing_branches:
                frappe.throw(_("Branch ID '{0}' already exists in this pricing rule").format(self.branch_id))
                
    def set_branch_name(self):
        """Set branch name based on branch ID"""
        if self.branch_id:
            # Try to get branch name from various sources
            # This could be enhanced to connect to actual branch master data
            if not self.branch_name:
                self.branch_name = f"Branch {self.branch_id}"
                
    def before_save(self):
        """Set defaults before saving"""
        if not self.branch_type:
            self.branch_type = "Main Branch"
        if self.is_active is None:
            self.is_active = 1