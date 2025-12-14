# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
import secrets
import string
from frappe.model.document import Document
from frappe import _


class POSDevice(Document):
    def before_insert(self):
        """Auto-generate device ID if not provided"""
        if not self.device_id:
            self.device_id = self.generate_device_id()
    
    def validate(self):
        """Validate device data before saving"""
        self.validate_registration_code()
        self.validate_branch_company_link()
    
    def after_insert(self):
        """Generate API credentials after device creation"""
        if self.is_registered and not self.api_key:
            self.generate_api_credentials()
            self.save()
    
    def generate_device_id(self):
        """Generate unique device ID"""
        timestamp = frappe.utils.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"POS_{timestamp}_{random_suffix}"
    
    def generate_api_credentials(self):
        """Generate API key and secret for device"""
        self.api_key = self.generate_api_key()
        self.api_secret = self.generate_api_secret()
    
    def generate_api_key(self):
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    def generate_api_secret(self):
        """Generate secure API secret"""
        return secrets.token_urlsafe(48)
    
    def validate_registration_code(self):
        """Validate registration code format"""
        if self.registration_code and len(self.registration_code) < 6:
            frappe.throw(_("Registration code must be at least 6 characters long"))
    
    def validate_branch_company_link(self):
        """Ensure branch belongs to the selected company"""
        if self.branch and self.company:
            branch_company = frappe.db.get_value("Branch", self.branch, "company")
            if branch_company != self.company:
                frappe.throw(_("Branch must belong to the selected company"))
    
    def update_sync_status(self, status, last_sync=None):
        """Update device sync status"""
        self.sync_status = status
        if last_sync:
            self.last_sync_at = last_sync
        self.last_heartbeat = frappe.utils.now()
        self.save(ignore_permissions=True)
    
    def mark_online(self):
        """Mark device as online"""
        self.update_sync_status("Online")
    
    def mark_offline(self):
        """Mark device as offline"""
        self.update_sync_status("Offline")
    
    def mark_syncing(self):
        """Mark device as syncing"""
        self.update_sync_status("Syncing")
    
    def mark_error(self, error_message=None):
        """Mark device as having error"""
        self.update_sync_status("Error")
        if error_message:
            frappe.log_error(
                f"POS Device Error - {self.device_name}: {error_message}",
                "POS Device Error"
            )


@frappe.whitelist()
def register_new_device(branch, device_name, registration_code, device_type=None, os_version=None, app_version=None):
    """Register a new POS device with generated credentials"""
    
    try:
        # Validate registration code (in production, this would be more sophisticated)
        if not validate_registration_code_format(registration_code):
            frappe.throw(_("Invalid registration code format"))
        
        # Check if device with this ID already exists
        existing_device = frappe.db.exists("POS Device", {"device_name": device_name})
        if existing_device:
            frappe.throw(_("Device with this name already exists"))
        
        # Create new device
        device = frappe.new_doc("POS Device")
        device.update({
            "device_name": device_name,
            "branch": branch,
            "company": frappe.db.get_value("Branch", branch, "company"),
            "registration_code": registration_code,
            "is_registered": 1,
            "device_type": device_type,
            "os_version": os_version,
            "app_version": app_version
        })
        
        device.save()
        frappe.db.commit()
        
        return {
            "status": "success",
            "device_id": device.device_id,
            "api_key": device.api_key,
            "api_secret": device.api_secret,
            "device_name": device.device_name
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Device registration failed: {str(e)}", "POS Device Registration")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_device_status(device_id):
    """Get current status of a POS device"""
    
    try:
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            return {"status": "error", "message": "Device not found"}
        
        return {
            "status": "success",
            "device": {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "sync_status": device.sync_status,
                "last_heartbeat": device.last_heartbeat,
                "last_sync_at": device.last_sync_at,
                "is_registered": device.is_registered
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def update_device_heartbeat(device_id, api_key):
    """Update device heartbeat to mark it as online"""
    
    try:
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {"status": "error", "message": "Invalid device credentials"}
        
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        device.mark_online()
        frappe.db.commit()
        
        return {"status": "success", "message": "Heartbeat updated"}
        
    except Exception as e:
        frappe.db.rollback()
        return {"status": "error", "message": str(e)}


def validate_registration_code_format(code):
    """Validate registration code format"""
    # Basic validation - in production, this would check against a database
    return len(code) >= 6 and code.isalnum()


def validate_device_credentials(device_id, api_key):
    """Validate device credentials"""
    device = frappe.db.get_value("POS Device", 
        {"device_id": device_id, "api_key": api_key, "is_registered": 1}, 
        ["name"], as_dict=True)
    
    return bool(device)


def get_active_devices(branch=None):
    """Get list of active devices"""
    filters = {"sync_status": "Online", "is_registered": 1}
    if branch:
        filters["branch"] = branch
    
    devices = frappe.get_all("POS Device", 
        filters=filters,
        fields=["device_id", "device_name", "branch", "last_heartbeat"],
        order_by="last_heartbeat desc")
    
    return devices


def get_device_statistics():
    """Get overall device statistics"""
    stats = {
        "total_devices": frappe.db.count("POS Device", {"is_registered": 1}),
        "online_devices": frappe.db.count("POS Device", {"sync_status": "Online", "is_registered": 1}),
        "offline_devices": frappe.db.count("POS Device", {"sync_status": "Offline", "is_registered": 1}),
        "error_devices": frappe.db.count("POS Device", {"sync_status": "Error", "is_registered": 1}),
        "syncing_devices": frappe.db.count("POS Device", {"sync_status": "Syncing", "is_registered": 1})
    }
    
    return stats