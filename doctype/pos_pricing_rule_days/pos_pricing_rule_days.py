# Copyright (c) 2025, Muhammad Hafla and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class POSPricingRuleDays(Document):
    def validate(self):
        """Validate days of week data"""
        self.validate_day_of_week()
        self.set_day_name()
        
    def validate_day_of_week(self):
        """Validate day of week selection"""
        if not self.day_of_week:
            frappe.throw(_("Day of Week is required"))
            
        # Check if day already exists in this pricing rule
        parent_doc = frappe.get_doc("POS Pricing Rule", self.parent)
        if parent_doc:
            existing_days = [item.day_of_week for item in parent_doc.days_of_week 
                           if item.name != self.name and item.day_of_week == self.day_of_week]
            if existing_days:
                day_name = self.get_day_name_by_number(self.day_of_week)
                frappe.throw(_("Day '{0}' already exists in this pricing rule").format(day_name))
                
    def set_day_name(self):
        """Set day name based on day number"""
        if self.day_of_week:
            self.day_name = self.get_day_name_by_number(self.day_of_week)
            
    def get_day_name_by_number(self, day_number):
        """Get day name from day number"""
        day_names = {
            "1": "Monday",
            "2": "Tuesday", 
            "3": "Wednesday",
            "4": "Thursday",
            "5": "Friday",
            "6": "Saturday",
            "7": "Sunday"
        }
        return day_names.get(day_number, f"Day {day_number}")
        
    def before_save(self):
        """Set defaults before saving"""
        if self.is_active is None:
            self.is_active = 1