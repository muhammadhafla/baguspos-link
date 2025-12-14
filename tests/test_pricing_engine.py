# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
import unittest
from unittest.mock import patch, MagicMock
from frappe.utils import flt
from erpnext_pos_integration.utils.pricing_engine import PricingEngine
from erpnext_pos_integration.api.pricing_api import calculate_price, get_pricing_rules, validate_pricing
from erpnext_pos_integration.api.pricing_api import calculate_bulk_prices, clear_pricing_cache
import json

class TestPricingEngine(unittest.TestCase):
    """Test suite for the 8-level pricing engine"""
    
    def setUp(self):
        """Set up test environment"""
        self.pricing_engine = PricingEngine()
        
        # Mock data for testing
        self.sample_item_code = "TEST-ITEM-001"
        self.sample_base_price = 100.0
        self.sample_quantity = 2
        self.sample_total_amount = 200.0
        self.sample_customer = "TEST-CUSTOMER-001"
        self.sample_branch_id = "TEST-BRANCH-001"
        self.sample_device_id = "TEST-DEVICE-001"
    
    def test_pricing_engine_initialization(self):
        """Test pricing engine initialization"""
        self.assertIsInstance(self.pricing_engine, PricingEngine)
        self.assertEqual(self.pricing_engine.cache_ttl, 300)
        self.assertIsNotNone(self.pricing_engine._cache_lock)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        cache_key = self.pricing_engine._generate_cache_key(
            item_code=self.sample_item_code,
            quantity=self.sample_quantity,
            total_amount=self.sample_total_amount,
            customer=self.sample_customer,
            branch_id=self.sample_branch_id
        )
        
        # Verify cache key contains expected components
        self.assertIn("pricing", cache_key)
        self.assertIn(self.sample_item_code, cache_key)
        self.assertIn(str(self.sample_quantity), cache_key)
        self.assertIn(str(self.sample_total_amount), cache_key)
        self.assertIn(self.sample_customer, cache_key)
        self.assertIn(self.sample_branch_id, cache_key)
    
    def test_item_info_retrieval(self):
        """Test item information retrieval"""
        with patch.object(frappe, 'get_value') as mock_get_value:
            # Mock frappe.get_value to return sample item data
            mock_get_value.return_value = {
                'item_group': 'Test Group',
                'brand': 'Test Brand',
                'stock_uom': 'Nos',
                'item_name': 'Test Item'
            }
            
            item_info = self.pricing_engine._get_item_info(self.sample_item_code)
            
            self.assertIsInstance(item_info, dict)
            self.assertEqual(item_info['item_group'], 'Test Group')
            self.assertEqual(item_info['brand'], 'Test Brand')
            self.assertEqual(item_info['stock_uom'], 'Nos')
            self.assertEqual(item_info['item_name'], 'Test Item')
    
    def test_price_response_builder(self):
        """Test standardized price response building"""
        response = self.pricing_engine._build_price_response(
            original_price=self.sample_base_price,
            final_price=80.0,
            discount_amount=20.0,
            discount_percentage=20.0,
            rule_applied="TEST-RULE-001",
            rule_name="Test Rule",
            pricing_type="Discount",
            priority_level=8
        )
        
        self.assertEqual(response['original_price'], flt(self.sample_base_price))
        self.assertEqual(response['final_price'], flt(80.0))
        self.assertEqual(response['discount_amount'], flt(20.0))
        self.assertEqual(response['discount_percentage'], flt(20.0))
        self.assertEqual(response['rule_applied'], "TEST-RULE-001")
        self.assertEqual(response['rule_name'], "Test Rule")
        self.assertEqual(response['pricing_type'], "Discount")
        self.assertEqual(response['priority_level'], 8)
        self.assertIn('timestamp', response)
    
    @patch('frappe.get_all')
    def test_applicable_pricing_rules_retrieval(self, mock_get_all):
        """Test retrieval of applicable pricing rules"""
        # Mock frappe.get_all to return sample pricing rules
        mock_rule = MagicMock()
        mock_rule.name = "TEST-RULE-001"
        mock_get_all.return_value = [mock_rule]
        
        with patch.object(frappe, 'get_doc') as mock_get_doc:
            # Mock frappe.get_doc to return a pricing rule document
            mock_rule_doc = MagicMock()
            mock_rule_doc.is_applicable.return_value = True
            mock_rule_doc.priority_level = "8"
            mock_rule_doc.pricing_type = "Manual Override"
            mock_rule_doc.rule_name = "Test Manual Override"
            mock_get_doc.return_value = mock_rule_doc
            
            rules = self.pricing_engine.get_applicable_pricing_rules(
                item_code=self.sample_item_code,
                quantity=self.sample_quantity,
                total_amount=self.sample_total_amount,
                customer=self.sample_customer,
                branch_id=self.sample_branch_id
            )
            
            self.assertIsInstance(rules, list)
            self.assertEqual(len(rules), 1)
            self.assertEqual(rules[0], mock_rule_doc)
    
    def test_pricing_configuration_validation(self):
        """Test pricing engine configuration validation"""
        with patch.object(frappe.db, 'exists') as mock_exists, \
             patch.object(frappe.db, 'count') as mock_count, \
             patch.object(frappe.db, 'sql') as mock_sql:
            
            # Mock existence checks
            mock_exists.side_effect = lambda doctype, name: doctype == 'POS Pricing Rule'
            
            # Mock count for active rules
            mock_count.return_value = 5
            
            # Mock SQL for priority distribution
            mock_sql.return_value = [('8', 2), ('7', 1), ('6', 2)]
            
            # Mock branch count
            def mock_count_side_effect(doctype, filters=None):
                if doctype == 'Branch' and filters and not filters.get('is_group'):
                    return 3
                return 0
            
            mock_count.side_effect = mock_count_side_effect
            
            result = self.pricing_engine.validate_pricing_configuration()
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('statistics', result)
            self.assertEqual(result['statistics']['active_rules'], 5)
            self.assertEqual(result['statistics']['priority_distribution'], {'8': 2, '7': 1, '6': 2})
            self.assertEqual(result['statistics']['branches'], 3)

class TestPricingAPI(unittest.TestCase):
    """Test suite for pricing API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.sample_device_id = "TEST-DEVICE-001"
        self.sample_api_key = "test-api-key-123"
        self.sample_item_code = "TEST-ITEM-001"
        self.sample_base_price = 100.0
        self.sample_quantity = 2
    
    @patch('erpnext_pos_integration.doctype.pos_device.pos_device.validate_device_credentials')
    @patch.object(frappe, 'get_doc')
    def test_calculate_price_endpoint_success(self, mock_get_doc, mock_validate_credentials):
        """Test successful price calculation API endpoint"""
        # Mock device validation
        mock_validate_credentials.return_value = True
        
        # Mock device document
        mock_device = MagicMock()
        mock_device.device_name = "Test Device"
        mock_device.branch = "TEST-BRANCH-001"
        mock_get_doc.return_value = mock_device
        
        with patch.object(PricingEngine, 'calculate_price') as mock_calculate:
            mock_calculate.return_value = {
                'original_price': 100.0,
                'final_price': 80.0,
                'discount_amount': 20.0,
                'discount_percentage': 20.0,
                'rule_applied': 'TEST-RULE-001',
                'timestamp': '2025-12-01T07:00:00'
            }
            
            result = calculate_price(
                device_id=self.sample_device_id,
                api_key=self.sample_api_key,
                item_code=self.sample_item_code,
                base_price=self.sample_base_price,
                quantity=self.sample_quantity
            )
            
            self.assertEqual(result['status'], 'success')
            self.assertTrue(result['authenticated'])
            self.assertEqual(result['device_id'], self.sample_device_id)
            self.assertEqual(result['device_name'], "Test Device")
            self.assertEqual(result['price_data']['final_price'], 80.0)
            self.assertEqual(result['price_data']['rule_applied'], 'TEST-RULE-001')
    
    def test_calculate_price_endpoint_authentication_failure(self):
        """Test price calculation API with invalid credentials"""
        with patch('erpnext_pos_integration.doctype.pos_device.pos_device.validate_device_credentials') as mock_validate:
            mock_validate.return_value = False
            
            result = calculate_price(
                device_id=self.sample_device_id,
                api_key="invalid-key",
                item_code=self.sample_item_code,
                base_price=self.sample_base_price
            )
            
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['message'], 'Invalid device credentials')
            self.assertFalse(result['authenticated'])
    
    def test_calculate_price_endpoint_missing_params(self):
        """Test price calculation API with missing parameters"""
        result = calculate_price(
            device_id=self.sample_device_id,
            # Missing api_key
            item_code=self.sample_item_code,
            base_price=self.sample_base_price
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Missing required parameters', result['message'])
        self.assertFalse(result.get('authenticated', True))
    
    @patch('erpnext_pos_integration.doctype.pos_device.pos_device.validate_device_credentials')
    def test_bulk_pricing_endpoint_success(self, mock_validate_credentials):
        """Test successful bulk pricing API endpoint"""
        # Mock device validation
        mock_validate_credentials.return_value = True
        
        # Mock device document
        with patch.object(frappe, 'get_doc') as mock_get_doc:
            mock_device = MagicMock()
            mock_device.device_name = "Test Device"
            mock_device.branch = "TEST-BRANCH-001"
            mock_get_doc.return_value = mock_device
            
            with patch.object(PricingEngine, 'calculate_bulk_prices') as mock_bulk_calc:
                mock_bulk_calc.return_value = {
                    'items': [
                        {
                            'item_code': 'ITEM-001',
                            'quantity': 1,
                            'original_price': 100.0,
                            'final_price': 80.0,
                            'discount_amount': 20.0,
                            'rule_applied': 'TEST-RULE-001'
                        }
                    ],
                    'total_original': 100.0,
                    'total_final': 80.0,
                    'total_discount': 20.0,
                    'calculation_time': 0.05,
                    'rules_applied': ['TEST-RULE-001']
                }
                
                items_data = [
                    {
                        'item_code': 'ITEM-001',
                        'base_price': 100.0,
                        'quantity': 1
                    }
                ]
                
                result = calculate_bulk_prices(
                    device_id=self.sample_device_id,
                    api_key=self.sample_api_key,
                    items_data=items_data
                )
                
                self.assertEqual(result['status'], 'success')
                self.assertTrue(result['authenticated'])
                self.assertEqual(result['items_processed'], 1)
                self.assertEqual(result['bulk_calculation']['total_final'], 80.0)
    
    def test_bulk_pricing_endpoint_invalid_json(self):
        """Test bulk pricing API with invalid JSON data"""
        with patch('erpnext_pos_integration.doctype.pos_device.pos_device.validate_device_credentials') as mock_validate:
            mock_validate.return_value = True
            
            result = calculate_bulk_prices(
                device_id=self.sample_device_id,
                api_key=self.sample_api_key,
                items_data="invalid-json-string"
            )
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('Invalid items_data JSON format', result['message'])
    
    def test_bulk_pricing_endpoint_empty_items(self):
        """Test bulk pricing API with empty items list"""
        with patch('erpnext_pos_integration.doctype.pos_device.pos_device.validate_device_credentials') as mock_validate:
            mock_validate.return_value = True
            
            result = calculate_bulk_prices(
                device_id=self.sample_device_id,
                api_key=self.sample_api_key,
                items_data=[]
            )
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('items_data cannot be empty', result['message'])
    
    @patch('erpnext_pos_integration.doctype.pos_device.pos_device.validate_device_credentials')
    def test_validate_pricing_endpoint_success(self, mock_validate_credentials):
        """Test successful pricing validation API endpoint"""
        # Mock device validation
        mock_validate_credentials.return_value = True
        
        # Mock device document
        with patch.object(frappe, 'get_doc') as mock_get_doc:
            mock_device = MagicMock()
            mock_device.device_name = "Test Device"
            mock_device.branch = "TEST-BRANCH-001"
            mock_device.is_registered = True
            mock_get_doc.return_value = mock_device
            
            with patch.object(PricingEngine, 'validate_pricing_configuration') as mock_validate:
                mock_validate.return_value = {
                    'status': 'success',
                    'issues': [],
                    'statistics': {
                        'active_rules': 5,
                        'priority_distribution': {'8': 2, '7': 1, '6': 2},
                        'branches': 3
                    }
                }
                
                with patch.object(PricingEngine, 'calculate_price') as mock_calculate:
                    mock_calculate.return_value = {
                        'original_price': 100.0,
                        'final_price': 100.0,
                        'discount_amount': 0.0,
                        'discount_percentage': 0.0,
                        'rule_applied': None
                    }
                    
                    result = validate_pricing(
                        device_id=self.sample_device_id,
                        api_key=self.sample_api_key
                    )
                    
                    self.assertEqual(result['status'], 'success')
                    self.assertTrue(result['authenticated'])
                    self.assertEqual(result['overall_status'], 'healthy')
                    self.assertEqual(result['pricing_engine']['status'], 'success')
                    self.assertEqual(result['pricing_engine']['statistics']['active_rules'], 5)

class TestPricingEngineIntegration(unittest.TestCase):
    """Integration tests for pricing engine workflow"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.pricing_engine = PricingEngine()
    
    @patch('frappe.get_all')
    @patch.object(frappe, 'get_doc')
    def test_end_to_end_price_calculation(self, mock_get_doc, mock_get_all):
        """Test end-to-end price calculation workflow"""
        # Mock pricing rules
        mock_rule1 = MagicMock()
        mock_rule1.name = "HIGH-PRIORITY-RULE"
        
        mock_rule2 = MagicMock()
        mock_rule2.name = "LOW-PRIORITY-RULE"
        
        mock_get_all.return_value = [mock_rule1, mock_rule2]
        
        # Mock rule documents
        mock_rule_doc1 = MagicMock()
        mock_rule_doc1.name = "HIGH-PRIORITY-RULE"
        mock_rule_doc1.is_applicable.return_value = True
        mock_rule_doc1.priority_level = "8"  # Highest priority
        mock_rule_doc1.pricing_type = "Manual Override"
        mock_rule_doc1.calculate_price.return_value = {
            'original_price': 100.0,
            'final_price': 90.0,
            'discount_amount': 10.0,
            'discount_percentage': 10.0,
            'rule_applied': 'HIGH-PRIORITY-RULE'
        }
        
        mock_rule_doc2 = MagicMock()
        mock_rule_doc2.name = "LOW-PRIORITY-RULE"
        mock_rule_doc2.is_applicable.return_value = True
        mock_rule_doc2.priority_level = "5"  # Lower priority
        mock_rule_doc2.pricing_type = "Quantity Break"
        
        def mock_get_doc_side_effect(doc_type, filters=None):
            if doc_type == "POS Pricing Rule":
                if filters and filters.get("name") == "HIGH-PRIORITY-RULE":
                    return mock_rule_doc1
                elif filters and filters.get("name") == "LOW-PRIORITY-RULE":
                    return mock_rule_doc2
            return None
        
        mock_get_doc.side_effect = mock_get_doc_side_effect
        
        # Mock item info
        with patch.object(self.pricing_engine, '_get_item_info') as mock_get_item_info:
            mock_get_item_info.return_value = {
                'item_group': 'Test Group',
                'brand': 'Test Brand'
            }
            
            result = self.pricing_engine.calculate_price(
                item_code="TEST-ITEM-001",
                base_price=100.0,
                quantity=2,
                total_amount=200.0,
                customer="TEST-CUSTOMER-001",
                branch_id="TEST-BRANCH-001"
            )
            
            self.assertEqual(result['final_price'], 90.0)
            self.assertEqual(result['discount_amount'], 10.0)
            self.assertEqual(result['discount_percentage'], 10.0)
            self.assertEqual(result['rule_applied'], 'HIGH-PRIORITY-RULE')
            self.assertEqual(result['pricing_type'], 'Manual Override')
            self.assertEqual(result['priority_level'], 8)

# Utility functions for running tests
def create_test_data():
    """Create test data for pricing engine tests"""
    try:
        # Create test POS Pricing Rules
        test_rules = [
            {
                "name": "Test Manual Override",
                "rule_name": "Manual Override Rule",
                "pricing_type": "Manual Override",
                "priority_level": "8",
                "is_active": 1,
                "base_price": 90.0
            },
            {
                "name": "Test Quantity Break",
                "rule_name": "Quantity Break Rule",
                "pricing_type": "Quantity Break",
                "priority_level": "5",
                "is_active": 1,
                "min_quantity": 10,
                "discount_percentage": 15.0
            }
        ]
        
        for rule_data in test_rules:
            if not frappe.db.exists("POS Pricing Rule", rule_data["name"]):
                doc = frappe.get_doc({
                    "doctype": "POS Pricing Rule",
                    **rule_data
                })
                doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Test data creation error: {str(e)}", "Test Setup")

def cleanup_test_data():
    """Clean up test data after tests"""
    try:
        # Clean up test pricing rules
        test_rule_names = ["Test Manual Override", "Test Quantity Break"]
        
        for rule_name in test_rule_names:
            if frappe.db.exists("POS Pricing Rule", rule_name):
                frappe.delete_doc("POS Pricing Rule", rule_name)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Test data cleanup error: {str(e)}", "Test Cleanup")

if __name__ == "__main__":
    # Run tests
    unittest.main()