# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, add_hours
from frappe.core.doctype.user.user import generate_keys
from erpnext_pos_integration.doctype.pos_device.pos_device import validate_device_credentials


@frappe.whitelist()
def register_device(branch, device_name, registration_code, device_type=None, os_version=None, app_version=None):
    """
    Register a new POS device and generate API credentials
    
    Args:
        branch (str): Branch ID where device will be registered
        device_name (str): Human-readable device name
        registration_code (str): Registration code for device setup
        device_type (str, optional): Type of device (Tablet, Desktop, Mobile, Kiosk)
        os_version (str, optional): Operating system version
        app_version (str, optional): Application version
    
    Returns:
        dict: Registration result with device credentials or error message
    """
    
    try:
        # Input validation
        if not all([branch, device_name, registration_code]):
            return {
                "status": "error",
                "message": _("Missing required parameters: branch, device_name, registration_code")
            }
        
        # Validate branch exists
        if not frappe.db.exists("Branch", branch):
            return {
                "status": "error", 
                "message": _("Branch not found")
            }
        
        # Check if device name already exists
        existing_device = frappe.db.exists("POS Device", {"device_name": device_name})
        if existing_device:
            return {
                "status": "error",
                "message": _("Device with this name already exists")
            }
        
        # Import POS Device functions
        from erpnext_pos_integration.doctype.pos_device.pos_device import register_new_device
        
        # Register device
        result = register_new_device(
            branch=branch,
            device_name=device_name,
            registration_code=registration_code,
            device_type=device_type,
            os_version=os_version,
            app_version=app_version
        )
        
        if result["status"] == "success":
            # Log successful registration
            frappe.log_error(
                f"POS Device registered successfully: {device_name} ({result['device_id']})",
                "POS Device Registration"
            )
            
            return {
                "status": "success",
                "message": _("Device registered successfully"),
                "data": {
                    "device_id": result["device_id"],
                    "api_key": result["api_key"],
                    "api_secret": result["api_secret"],
                    "device_name": result["device_name"]
                }
            }
        else:
            return result
        
    except Exception as e:
        frappe.log_error(f"Device registration API error: {str(e)}", "POS Device Registration API")
        return {
            "status": "error",
            "message": _("Internal server error during device registration")
        }


@frappe.whitelist()
def health_check(device_id, api_key):
    """
    Check system health for POS device
    
    Args:
        device_id (str): Unique device identifier
        api_key (str): Device API key for authentication
    
    Returns:
        dict: Health status and system information
    """
    
    try:
        # Input validation
        if not all([device_id, api_key]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key")
            }
        
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {
                "status": "error",
                "message": _("Invalid device credentials"),
                "authenticated": False
            }
        
        # Get device information
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            return {
                "status": "error",
                "message": _("Device not found")
            }
        
        # Perform health checks
        health_status = perform_health_checks(device)
        
        # Update device heartbeat
        device.mark_online()
        frappe.db.commit()
        
        return {
            "status": "success",
            "authenticated": True,
            "device": {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "branch": device.branch,
                "last_heartbeat": device.last_heartbeat
            },
            "health": health_status,
            "timestamp": now()
        }
        
    except Exception as e:
        frappe.log_error(f"Health check API error for device {device_id}: {str(e)}", "POS Health Check API")
        return {
            "status": "error",
            "message": _("Internal server error during health check"),
            "authenticated": False
        }


@frappe.whitelist()
def update_device_heartbeat(device_id, api_key):
    """
    Update device heartbeat to mark it as online
    
    Args:
        device_id (str): Unique device identifier  
        api_key (str): Device API key for authentication
    
    Returns:
        dict: Heartbeat update result
    """
    
    try:
        # Input validation
        if not all([device_id, api_key]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key")
            }
        
        # Import and use POS Device functions
        from erpnext_pos_integration.doctype.pos_device.pos_device import update_device_heartbeat
        
        result = update_device_heartbeat(device_id, api_key)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": _("Heartbeat updated successfully"),
                "timestamp": now()
            }
        else:
            return result
        
    except Exception as e:
        frappe.log_error(f"Heartbeat update API error for device {device_id}: {str(e)}", "POS Heartbeat API")
        return {
            "status": "error",
            "message": _("Internal server error during heartbeat update")
        }


@frappe.whitelist()
def get_device_status(device_id, api_key):
    """
    Get current status of a POS device
    
    Args:
        device_id (str): Unique device identifier
        api_key (str): Device API key for authentication
    
    Returns:
        dict: Device status information
    """
    
    try:
        # Input validation
        if not all([device_id, api_key]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key")
            }
        
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {
                "status": "error",
                "message": _("Invalid device credentials")
            }
        
        # Get device status
        from erpnext_pos_integration.doctype.pos_device.pos_device import get_device_status
        
        result = get_device_status(device_id)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "device": result["device"],
                "timestamp": now()
            }
        else:
            return result
        
    except Exception as e:
        frappe.log_error(f"Device status API error for device {device_id}: {str(e)}", "POS Device Status API")
        return {
            "status": "error",
            "message": _("Internal server error during status check")
        }


def perform_health_checks(device):
    """Perform comprehensive health checks"""
    
    health_checks = {
        "database": check_database_connection(),
        "api_performance": check_api_performance(),
        "last_sync": get_last_sync_time(device.device_id),
        "pending_operations": get_pending_operations_count(device.device_id),
        "system_resources": get_system_resources()
    }
    
    # Determine overall health status
    if all([
        health_checks["database"],
        health_checks["api_performance"] < 1000,  # API response time under 1 second
        health_checks["system_resources"]["status"] == "healthy"
    ]):
        health_checks["overall_status"] = "healthy"
    else:
        health_checks["overall_status"] = "degraded"
    
    return health_checks


def check_database_connection():
    """Check database connectivity"""
    try:
        frappe.db.sql("SELECT 1")
        return True
    except:
        return False


def check_api_performance():
    """Check API performance (simplified)"""
    try:
        import time
        start_time = time.time()
        frappe.db.sql("SELECT COUNT(*) FROM `tabPOS Device`")
        return int((time.time() - start_time) * 1000)  # Return in milliseconds
    except:
        return -1


def get_last_sync_time(device_id):
    """Get last sync time for device"""
    device = frappe.get_doc("POS Device", {"device_id": device_id})
    return device.last_sync_at if device and device.last_sync_at else None


def get_pending_operations_count(device_id):
    """Get count of pending operations for device"""
    # This would check for pending sync operations, queued transactions, etc.
    # For now, return a placeholder value
    return 0


def get_system_resources():
    """Get system resource information"""
    # This would check memory, CPU, disk usage, etc.
    # For now, return a healthy status
    return {
        "status": "healthy",
        "memory_usage": "normal",
        "cpu_usage": "normal"
    }


@frappe.whitelist()
def get_system_overview():
    """
    Get system overview for admin dashboard
    
    Returns:
        dict: System overview statistics
    """
    
    try:
        from erpnext_pos_integration.doctype.pos_device.pos_device import get_device_statistics
        from erpnext_pos_integration.doctype.pos_sync_log.pos_sync_log import get_sync_statistics
        
        # Get device statistics
        device_stats = get_device_statistics()
        
        # Get sync statistics
        sync_stats = get_sync_statistics(time_range="24h")
        
        return {
            "status": "success",
            "overview": {
                "devices": device_stats,
                "sync": sync_stats.get("statistics", {}) if sync_stats.get("status") == "success" else {},
                "timestamp": now()
            }
        }
        
    except Exception as e:
        frappe.log_error(f"System overview API error: {str(e)}", "POS System Overview API")
        return {
            "status": "error",
            "message": _("Internal server error")
        }