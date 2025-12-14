# Copyright (c) 2025, Muhammad Hafla and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, time
import json

class POSPricingRule(Document):
    def before_save(self):
        """Validate and set defaults before saving"""
        self.validate_priority_mapping()
        self.validate_time_range()
        self.set_creation_info()
        
    def validate(self):
        """Validate pricing rule data"""
        self.validate_priority_mapping()
        self.validate_time_range()
        self.validate_pricing_values()
        self.validate_branch_conditions()
        
    def validate_priority_mapping(self):
        """Validate priority level and map to ERPNext priorities"""
        priority_mapping = {
            "1": 20,  # Base Item Price
            "2": 19,  # Branch Price Override  
            "3": 18,  # Member/Customer Price
            "4": 17,  # Time-based Promotion
            "5": 16,  # Quantity Break Discount
            "6": 15,  # Spend X Discount
            "7": 14,  # Buy X Get Y (BXGY)
            "8": 13   # Manual Override
        }
        
        if self.priority_level not in priority_mapping:
            frappe.throw(_("Invalid priority level. Must be between 1-8"))
            
        self.erpnext_priority = priority_mapping[self.priority_level]
        
    def validate_time_range(self):
        """Validate time-based pricing conditions"""
        if self.from_time and self.to_time:
            if self.from_time >= self.to_time:
                frappe.throw(_("From Time must be before To Time"))
                
        # Validate days of week if time conditions are set
        if (self.from_time or self.to_time) and not self.days_of_week:
            frappe.throw(_("Days of Week must be specified when time conditions are set"))
            
    def validate_pricing_values(self):
        """Validate pricing values based on pricing type"""
        if self.pricing_type == "Base Price" and not self.base_price:
            frappe.throw(_("Base Price is required for Base Price type"))
            
        elif self.pricing_type in ["Spend Discount", "Quantity Break"]:
            if not self.discount_percentage and not self.discount_amount:
                frappe.throw(_("Either Discount Percentage or Discount Amount is required"))
                
        elif self.pricing_type == "BXGY":
            if not self.bxgy_buy_qty or not self.bxgy_get_qty:
                frappe.throw(_("BXGY Buy Quantity and Get Quantity are required"))
                
        elif self.pricing_type == "Manual Override":
            if not self.base_price and not self.discount_percentage and not self.discount_amount:
                frappe.throw(_("Manual Override requires at least one pricing value"))
                
    def validate_branch_conditions(self):
        """Validate branch conditions"""
        if self.branch_conditions:
            branch_ids = [item.branch_id for item in self.branch_conditions if item.branch_id]
            if len(branch_ids) != len(set(branch_ids)):
                frappe.throw(_("Duplicate branch IDs found in branch conditions"))
                
    def set_creation_info(self):
        """Set creation and modification info"""
        if not self.owner:
            self.owner = frappe.session.user
        if not self.creation:
            self.creation = datetime.now()
        self.modified = datetime.now()
        self.modified_by = frappe.session.user
        
    def is_applicable(self, transaction_context):
        """
        Check if pricing rule is applicable for given transaction context
        transaction_context: dict containing transaction details
        """
        # Check if rule is active
        if not self.is_active:
            return False
            
        # Check time validity
        if not self._is_time_valid():
            return False
            
        # Check branch conditions
        if not self._is_branch_valid(transaction_context.get('branch_id')):
            return False
            
        # Check item conditions  
        if not self._is_item_valid(transaction_context.get('item_code')):
            return False
            
        # Check customer conditions
        if not self._is_customer_valid(transaction_context.get('customer')):
            return False
            
        # Check quantity conditions
        if not self._is_quantity_valid(transaction_context.get('quantity', 0)):
            return False
            
        # Check spend amount conditions
        if not self._is_spend_valid(transaction_context.get('total_amount', 0)):
            return False
            
        return True
        
    def _is_time_valid(self):
        """Check if current time is valid for this rule"""
        now = datetime.now()
        
        # Check date range
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_upto and now > self.valid_upto:
            return False
            
        # Check day of week
        if self.days_of_week:
            current_day = now.weekday()  # 0=Monday, 6=Sunday
            valid_days = [item.day_of_week for item in self.days_of_week]
            if current_day not in [int(day)-1 for day in valid_days if day.isdigit()]:
                return False
                
        # Check time range
        if self.from_time and self.to_time:
            current_time = now.time()
            from_time = datetime.strptime(self.from_time, "%H:%M:%S").time()
            to_time = datetime.strptime(self.to_time, "%H:%M:%S").time()
            
            if from_time <= to_time:
                # Same day time range
                if not (from_time <= current_time <= to_time):
                    return False
            else:
                # Overnight time range
                if not (current_time >= from_time or current_time <= to_time):
                    return False
                    
        return True
        
    def _is_branch_valid(self, branch_id):
        """Check if branch is valid for this rule"""
        if not self.branch_conditions:
            return True  # No branch restrictions
            
        if not branch_id:
            return False  # Branch required but not provided
            
        valid_branches = [item.branch_id for item in self.branch_conditions if item.branch_id]
        return branch_id in valid_branches
        
    def _is_item_valid(self, item_code):
        """Check if item is valid for this rule"""
        # Check specific item
        if self.item_code and self.item_code != item_code:
            return False
            
        # Check item group
        if self.item_group:
            item_group = frappe.get_value("Item", item_code, "item_group") if item_code else None
            if item_group != self.item_group:
                return False
                
        # Check brand
        if self.brand:
            item_brand = frappe.get_value("Item", item_code, "brand") if item_code else None
            if item_brand != self.brand:
                return False
                
        return True
        
    def _is_customer_valid(self, customer):
        """Check if customer is valid for this rule"""
        # Check specific customer
        if self.customer and self.customer != customer:
            return False
            
        # Check customer group
        if self.customer_group:
            customer_group = frappe.get_value("Customer", customer, "customer_group") if customer else None
            if customer_group != self.customer_group:
                return False
                
        # Check territory
        if self.territory:
            customer_territory = frappe.get_value("Customer", customer, "territory") if customer else None
            if customer_territory != self.territory:
                return False
                
        return True
        
    def _is_quantity_valid(self, quantity):
        """Check if quantity is valid for this rule"""
        if self.min_quantity and quantity < self.min_quantity:
            return False
        if self.max_quantity and quantity > self.max_quantity:
            return False
        return True
        
    def _is_spend_valid(self, total_amount):
        """Check if spend amount is valid for this rule"""
        if self.min_spend_amount and total_amount < self.min_spend_amount:
            return False
        return True
        
    def calculate_price(self, base_price, quantity=1, total_amount=0):
        """
        Calculate final price based on this pricing rule
        Returns: dict with price_breakdown
        """
        result = {
            'original_price': base_price,
            'final_price': base_price,
            'discount_amount': 0,
            'discount_percentage': 0,
            'rule_applied': self.name
        }
        
        if self.pricing_type == "Base Price":
            result['final_price'] = self.base_price or base_price
            
        elif self.pricing_type == "Branch Override":
            result['final_price'] = self.base_price or base_price
            
        elif self.pricing_type == "Customer Price":
            result['final_price'] = self.base_price or base_price
            
        elif self.pricing_type == "Time-based":
            if self.discount_percentage:
                discount = base_price * (self.discount_percentage / 100)
                result['final_price'] = base_price - discount
                result['discount_amount'] = discount
                result['discount_percentage'] = self.discount_percentage
            elif self.discount_amount:
                result['final_price'] = max(0, base_price - self.discount_amount)
                result['discount_amount'] = self.discount_amount
                
        elif self.pricing_type == "Quantity Break":
            if self.discount_percentage:
                discount = base_price * (self.discount_percentage / 100)
                result['final_price'] = base_price - discount
                result['discount_amount'] = discount
                result['discount_percentage'] = self.discount_percentage
            elif self.discount_amount:
                result['final_price'] = max(0, base_price - self.discount_amount)
                result['discount_amount'] = self.discount_amount
                
        elif self.pricing_type == "Spend Discount":
            if self.discount_percentage:
                discount = base_price * (self.discount_percentage / 100)
                result['final_price'] = base_price - discount
                result['discount_amount'] = discount
                result['discount_percentage'] = self.discount_percentage
            elif self.discount_amount:
                result['final_price'] = max(0, base_price - self.discount_amount)
                result['discount_amount'] = self.discount_amount
                
        elif self.pricing_type == "BXGY":
            # BXGY logic - calculate effective price for promotional items
            if self.bxgy_buy_qty > 0:
                free_items = quantity // (self.bxgy_buy_qty + self.bxgy_get_qty) * self.bxgy_get_qty
                if free_items > 0:
                    effective_quantity = quantity - free_items
                    result['final_price'] = (base_price * effective_quantity) / quantity
                    result['free_items'] = free_items
                    
        elif self.pricing_type == "Manual Override":
            if self.base_price:
                result['final_price'] = self.base_price
            elif self.discount_percentage:
                discount = base_price * (self.discount_percentage / 100)
                result['final_price'] = base_price - discount
                result['discount_amount'] = discount
                result['discount_percentage'] = self.discount_percentage
            elif self.discount_amount:
                result['final_price'] = max(0, base_price - self.discount_amount)
                result['discount_amount'] = self.discount_amount
                
        return result

@frappe.whitelist()
def get_applicable_pricing_rules(item_code, branch_id=None, customer=None, quantity=1, total_amount=0):
    """
    Get all applicable pricing rules for given context
    """
    # Get all active pricing rules
    pricing_rules = frappe.get_all(
        "POS Pricing Rule",
        filters={"is_active": 1},
        fields=["*"],
        order_by="erpnext_priority desc"
    )
    
    applicable_rules = []
    transaction_context = {
        'item_code': item_code,
        'branch_id': branch_id,
        'customer': customer,
        'quantity': quantity,
        'total_amount': total_amount
    }
    
    for rule in pricing_rules:
        rule_doc = frappe.get_doc("POS Pricing Rule", rule.name)
        if rule_doc.is_applicable(transaction_context):
            applicable_rules.append(rule_doc)
            
    return applicable_rules

@frappe.whitelist()
def calculate_final_price(item_code, base_price, branch_id=None, customer=None, quantity=1, total_amount=0):
    """
    Calculate final price using highest priority applicable rule
    """
    applicable_rules = get_applicable_pricing_rules(
        item_code, branch_id, customer, quantity, total_amount
    )
    
    if not applicable_rules:
        return {
            'original_price': base_price,
            'final_price': base_price,
            'discount_amount': 0,
            'discount_percentage': 0,
            'rule_applied': None
        }
        
    # Use highest priority rule (first in sorted list)
    best_rule = applicable_rules[0]
    return best_rule.calculate_price(base_price, quantity, total_amount)