# Copyright (c) 2025, Muhammad Hafla and contributors
# For license information, please see license.txt

import frappe
import unittest

class TestPOSPricingRule(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test pricing rule
        self.pricing_rule = frappe.get_doc({
            "doctype": "POS Pricing Rule",
            "rule_name": "Test Pricing Rule",
            "pricing_type": "Base Price",
            "priority_level": "1",
            "base_price": 100.0,
            "is_active": 1
        })
        
    def test_priority_mapping(self):
        """Test priority level to ERPNext mapping"""
        # Test each priority level
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
        
        for level, expected_erpnext_priority in priority_mapping.items():
            self.pricing_rule.priority_level = level
            self.pricing_rule.validate_priority_mapping()
            self.assertEqual(self.pricing_rule.erpnext_priority, expected_erpnext_priority)
            
    def test_invalid_priority_level(self):
        """Test invalid priority level validation"""
        self.pricing_rule.priority_level = "9"  # Invalid level
        
        with self.assertRaises(frappe.ValidationError):
            self.pricing_rule.validate_priority_mapping()
            
    def test_time_range_validation(self):
        """Test time range validation"""
        # Valid time range
        self.pricing_rule.from_time = "09:00:00"
        self.pricing_rule.to_time = "17:00:00"
        self.pricing_rule.validate_time_range()  # Should not raise exception
        
        # Invalid time range
        self.pricing_rule.from_time = "17:00:00"
        self.pricing_rule.to_time = "09:00:00"
        
        with self.assertRaises(frappe.ValidationError):
            self.pricing_rule.validate_time_range()
            
    def test_pricing_type_validation(self):
        """Test pricing type specific validations"""
        # Base Price requires base_price
        self.pricing_rule.pricing_type = "Base Price"
        self.pricing_rule.base_price = None
        
        with self.assertRaises(frappe.ValidationError):
            self.pricing_rule.validate_pricing_values()
            
        # BXGY requires buy and get quantities
        self.pricing_rule.pricing_type = "BXGY"
        self.pricing_rule.bxgy_buy_qty = None
        self.pricing_rule.bxgy_get_qty = None
        
        with self.assertRaises(frappe.ValidationError):
            self.pricing_rule.validate_pricing_values()
            
    def test_price_calculation(self):
        """Test price calculation for different pricing types"""
        base_price = 100.0
        
        # Test Base Price
        self.pricing_rule.pricing_type = "Base Price"
        self.pricing_rule.base_price = 80.0
        result = self.pricing_rule.calculate_price(base_price)
        self.assertEqual(result['final_price'], 80.0)
        
        # Test Percentage Discount
        self.pricing_rule.pricing_type = "Time-based"
        self.pricing_rule.discount_percentage = 10
        result = self.pricing_rule.calculate_price(base_price)
        self.assertEqual(result['final_price'], 90.0)
        self.assertEqual(result['discount_amount'], 10.0)
        
        # Test Fixed Amount Discount
        self.pricing_rule.pricing_type = "Time-based"
        self.pricing_rule.discount_amount = 15.0
        result = self.pricing_rule.calculate_price(base_price)
        self.assertEqual(result['final_price'], 85.0)
        self.assertEqual(result['discount_amount'], 15.0)
        
    def test_bxgy_calculation(self):
        """Test Buy X Get Y calculation"""
        self.pricing_rule.pricing_type = "BXGY"
        self.pricing_rule.bxgy_buy_qty = 2
        self.pricing_rule.bxgy_get_qty = 1
        
        # Test with 3 items (buy 2, get 1 free)
        result = self.pricing_rule.calculate_price(100.0, quantity=3)
        self.assertEqual(result['final_price'], 66.67)  # Pay for 2 out of 3 items
        self.assertEqual(result['free_items'], 1)
        
        # Test with 5 items (buy 2, get 1 free twice)
        result = self.pricing_rule.calculate_price(100.0, quantity=5)
        self.assertEqual(result['final_price'], 60.0)  # Pay for 3 out of 5 items
        self.assertEqual(result['free_items'], 2)
        
    def test_is_applicable(self):
        """Test pricing rule applicability check"""
        # Create transaction context
        context = {
            'item_code': 'TEST-ITEM',
            'branch_id': 'BRANCH-001',
            'customer': 'TEST-CUSTOMER',
            'quantity': 1,
            'total_amount': 100.0
        }
        
        # Test with matching criteria
        self.pricing_rule.is_active = 1
        self.assertTrue(self.pricing_rule.is_applicable(context))
        
        # Test with inactive rule
        self.pricing_rule.is_active = 0
        self.assertFalse(self.pricing_rule.is_applicable(context))
        
        # Test quantity validation
        self.pricing_rule.is_active = 1
        self.pricing_rule.min_quantity = 10
        self.pricing_rule.is_active = 1
        context['quantity'] = 5  # Below minimum
        self.assertFalse(self.pricing_rule.is_applicable(context))
        
    def test_export_pricing_rules(self):
        """Test pricing rules export functionality"""
        # This would test the export functionality if implemented
        # Currently just testing that the function exists
        self.assertTrue(hasattr(frappe.get_doc('POS Pricing Rule', self.pricing_rule.name), 'export_pricing_rules'))
        
    def tearDown(self):
        """Clean up test data"""
        if self.pricing_rule.name:
            frappe.delete_doc("POS Pricing Rule", self.pricing_rule.name, force=True)