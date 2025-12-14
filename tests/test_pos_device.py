# Copyright (c) 2025, ERPNext and Contributors
# See license.txt

import frappe
import unittest
from frappe.utils import now
from erpnext_pos_integration.doctype.pos_device.pos_device import POSDevice


class TestPOSDevice(unittest.TestCase):
    def setUp(self):
        """Set up test data before each test"""
        frappe.set_user("Administrator")
        self.test_branch = self.create_test_branch()
        self.test_company = self.create_test_company()
    
    def tearDown(self):
        """Clean up test data after each test"""
        # Clean up test data
        test_devices = frappe.get_all("POS Device", filters={"device_id": ["like", "TEST_%"]})
        for device in test_devices:
            frappe.delete_doc("POS Device", device.name, force=True)
        
        frappe.delete_doc("Branch", self.test_branch, force=True)
        frappe.delete_doc("Company", self.test_company, force=True)
    
    def create_test_company(self):
        """Create a test company"""
        company = frappe.new_doc("Company")
        company.update({
            "name": "Test Company",
            "company_name": "Test Company",
            "abbr": "TC",
            "default_currency": "USD",
            "country": "United States"
        })
        company.save()
        return company.name
    
    def create_test_branch(self):
        """Create a test branch"""
        branch = frappe.new_doc("Branch")
        branch.update({
            "branch": "Test Branch",
            "company": self.create_test_company()
        })
        branch.save()
        return branch.name
    
    def test_device_creation(self):
        """Test device creation and API key generation"""
        device = frappe.new_doc("POS Device")
        device.update({
            "device_id": "TEST_DEVICE_001",
            "device_name": "Test Device 1",
            "branch": self.test_branch,
            "company": self.test_company,
            "is_registered": 1
        })
        device.save()
        
        # Test that API credentials are generated
        self.assertTrue(device.api_key)
        self.assertTrue(device.api_secret)
        self.assertEqual(device.is_registered, 1)
        self.assertEqual(device.sync_status, "Offline")  # Default status
        
        # Test device ID generation if not provided
        device2 = frappe.new_doc("POS Device")
        device2.update({
            "device_name": "Test Device 2",
            "branch": self.test_branch,
            "company": self.test_company
        })
        device2.save()
        
        self.assertTrue(device2.device_id)
        self.assertTrue(device2.device_id.startswith("POS_"))
    
    def test_device_registration_api(self):
        """Test device registration through API"""
        from erpnext_pos_integration.api.device_api import register_device
        
        # Test successful registration
        result = register_device(
            branch=self.test_branch,
            device_name="API Test Device",
            registration_code="TEST123456"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIn("device_id", result["data"])
        self.assertIn("api_key", result["data"])
        self.assertIn("api_secret", result["data"])
        
        # Test duplicate device name
        result2 = register_device(
            branch=self.test_branch,
            device_name="API Test Device",  # Same name
            registration_code="TEST789012"
        )
        
        self.assertEqual(result2["status"], "error")
        self.assertIn("already exists", result2["message"])
    
    def test_device_health_check(self):
        """Test device health check functionality"""
        from erpnext_pos_integration.api.device_api import health_check
        
        # First register a device
        register_result = register_device(
            branch=self.test_branch,
            device_name="Health Test Device",
            registration_code="HEALTH123"
        )
        
        device_id = register_result["data"]["device_id"]
        api_key = register_result["data"]["api_key"]
        
        # Test health check with valid credentials
        health_result = health_check(device_id, api_key)
        
        self.assertEqual(health_result["status"], "success")
        self.assertEqual(health_result["authenticated"], True)
        self.assertIn("device", health_result)
        self.assertIn("health", health_result)
        
        # Test health check with invalid credentials
        invalid_health = health_check(device_id, "invalid_key")
        self.assertEqual(invalid_health["status"], "error")
        self.assertEqual(invalid_health["authenticated"], False)
    
    def test_device_heartbeat_update(self):
        """Test device heartbeat update"""
        from erpnext_pos_integration.api.device_api import update_device_heartbeat
        
        # Register a device
        register_result = register_device(
            branch=self.test_branch,
            device_name="Heartbeat Test Device",
            registration_code="HEART123"
        )
        
        device_id = register_result["data"]["device_id"]
        api_key = register_result["data"]["api_key"]
        
        # Update heartbeat
        heartbeat_result = update_device_heartbeat(device_id, api_key)
        
        self.assertEqual(heartbeat_result["status"], "success")
        self.assertIn("Heartbeat updated", heartbeat_result["message"])
        
        # Verify device status was updated
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        self.assertEqual(device.sync_status, "Online")
    
    def test_device_status_retrieval(self):
        """Test device status retrieval"""
        from erpnext_pos_integration.api.device_api import get_device_status
        
        # Register a device
        register_result = register_device(
            branch=self.test_branch,
            device_name="Status Test Device",
            registration_code="STATUS123"
        )
        
        device_id = register_result["data"]["device_id"]
        api_key = register_result["data"]["api_key"]
        
        # Get device status
        status_result = get_device_status(device_id, api_key)
        
        self.assertEqual(status_result["status"], "success")
        self.assertIn("device", status_result)
        self.assertEqual(status_result["device"]["device_id"], device_id)
        self.assertEqual(status_result["device"]["device_name"], "Status Test Device")
    
    def test_validate_device_credentials(self):
        """Test device credential validation"""
        from erpnext_pos_integration.doctype.pos_device.pos_device import validate_device_credentials
        
        # Register a device
        register_result = register_device(
            branch=self.test_branch,
            device_name="Credential Test Device",
            registration_code="CRED123"
        )
        
        device_id = register_result["data"]["device_id"]
        api_key = register_result["data"]["api_key"]
        
        # Test valid credentials
        self.assertTrue(validate_device_credentials(device_id, api_key))
        
        # Test invalid device ID
        self.assertFalse(validate_device_credentials("INVALID_DEVICE", api_key))
        
        # Test invalid API key
        self.assertFalse(validate_device_credentials(device_id, "INVALID_KEY"))
    
    def test_sync_status_updates(self):
        """Test device sync status update methods"""
        device = frappe.new_doc("POS Device")
        device.update({
            "device_id": "STATUS_TEST_001",
            "device_name": "Status Test Device",
            "branch": self.test_branch,
            "company": self.test_company
        })
        device.save()
        
        # Test mark_online
        device.mark_online()
        self.assertEqual(device.sync_status, "Online")
        
        # Test mark_offline
        device.mark_offline()
        self.assertEqual(device.sync_status, "Offline")
        
        # Test mark_syncing
        device.mark_syncing()
        self.assertEqual(device.sync_status, "Syncing")
        
        # Test mark_error
        device.mark_error("Test error")
        self.assertEqual(device.sync_status, "Error")


if __name__ == "__main__":
    unittest.main()