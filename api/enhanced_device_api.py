import frappe
from frappe import _
from datetime import datetime, timedelta

@frappe.whitelist()
def test_device_connection(device_name):
    """Test connection to a specific device"""
    
    try:
        device = frappe.get_doc("POS Device", device_name)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        # Simulate connection test
        # In real implementation, this would attempt actual connection
        connection_result = {
            "device_name": device.device_name,
            "device_type": device.device_type,
            "status": "connected",
            "response_time": 150,  # milliseconds
            "timestamp": datetime.now().isoformat()
        }
        
        # Update device last sync time
        device.last_sync = datetime.now()
        device.save()
        frappe.db.commit()
        
        return {"success": True, "result": connection_result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def sync_device_data(device_name, sync_type="Full Sync"):
    """Sync data with a specific device"""
    
    try:
        device = frappe.get_doc("POS Device", device_name)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        # Create sync log entry
        sync_log = frappe.get_doc({
            "doctype": "POS Sync Log",
            "device_name": device.device_name,
            "sync_type": sync_type,
            "status": "Pending",
            "creation": datetime.now()
        })
        sync_log.insert()
        
        # Simulate sync process
        # In real implementation, this would trigger actual sync
        sync_log.status = "Success"
        sync_log.completion_time = datetime.now()
        sync_log.save()
        
        # Update device last sync
        device.last_sync = datetime.now()
        device.save()
        frappe.db.commit()
        
        return {"success": True, "message": "Device sync completed"}
        
    except Exception as e:
        frappe.db.rollback()
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def sync_all_devices():
    """Sync data with all active devices"""
    
    try:
        active_devices = frappe.get_all("POS Device", 
            filters={"status": "Active"},
            fields=["name", "device_name"]
        )
        
        results = []
        for device in active_devices:
            result = sync_device_data(device.name, "Bulk Sync")
            results.append({
                "device_name": device.device_name,
                "result": result
            })
        
        return {"success": True, "results": results}
        
    except Exception as e:
        return {"success": False, "error": str(e)}