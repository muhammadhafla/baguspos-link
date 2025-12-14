# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now, get_datetime


class POSSyncLog(Document):
    def before_insert(self):
        """Set default values before insertion"""
        if not self.start_time:
            self.start_time = now()
    
    def validate(self):
        """Validate sync log data"""
        self.validate_timing()
        self.validate_metrics()
    
    def validate_timing(self):
        """Validate timing fields"""
        if self.start_time and self.end_time:
            if get_datetime(self.end_time) < get_datetime(self.start_time):
                frappe.throw(_("End time cannot be before start time"))
    
    def validate_metrics(self):
        """Validate performance metrics"""
        if self.items_synced < 0:
            frappe.throw(_("Items synced cannot be negative"))
        if self.transactions_synced < 0:
            frappe.throw(_("Transactions synced cannot be negative"))
        if self.conflicts_detected < 0:
            frappe.throw(_("Conflicts detected cannot be negative"))
    
    def on_update(self):
        """Calculate duration when end time is set"""
        if self.end_time and not self.duration:
            self.calculate_duration()
    
    def calculate_duration(self):
        """Calculate sync duration in seconds"""
        if self.start_time and self.end_time:
            start_dt = get_datetime(self.start_time)
            end_dt = get_datetime(self.end_time)
            duration_seconds = (end_dt - start_dt).total_seconds()
            self.duration = int(duration_seconds)
    
    def mark_completed(self, items_synced=0, transactions_synced=0, conflicts_detected=0, sync_data=None):
        """Mark sync operation as completed"""
        self.sync_status = "Completed"
        self.end_time = now()
        self.items_synced = items_synced
        self.transactions_synced = transactions_synced
        self.conflicts_detected = conflicts_detected
        if sync_data:
            self.sync_data = sync_data
        self.calculate_duration()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark sync operation as failed"""
        self.sync_status = "Failed"
        self.end_time = now()
        self.error_details = error_message
        self.calculate_duration()
        self.save()
    
    def mark_in_progress(self):
        """Mark sync operation as in progress"""
        self.sync_status = "In Progress"
        self.save()


@frappe.whitelist()
def create_sync_log(device_id, sync_type, sync_status="Started", sync_data=None):
    """Create a new sync log entry"""
    
    try:
        # Get device document
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            frappe.throw(_("Device not found"))
        
        # Create sync log
        sync_log = frappe.new_doc("POS Sync Log")
        sync_log.update({
            "device": device.name,
            "sync_type": sync_type,
            "sync_status": sync_status,
            "sync_data": sync_data or {}
        })
        
        sync_log.save()
        frappe.db.commit()
        
        return {
            "status": "success",
            "sync_log_id": sync_log.name
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Sync log creation failed: {str(e)}", "POS Sync Log")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def update_sync_log(sync_log_id, sync_status, items_synced=0, transactions_synced=0, 
                   conflicts_detected=0, error_message=None, sync_data=None):
    """Update sync log entry with results"""
    
    try:
        sync_log = frappe.get_doc("POS Sync Log", sync_log_id)
        
        if sync_status == "Completed":
            sync_log.mark_completed(items_synced, transactions_synced, conflicts_detected, sync_data)
        elif sync_status == "Failed":
            sync_log.mark_failed(error_message or "Unknown error")
        elif sync_status == "In Progress":
            sync_log.mark_in_progress()
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "sync_log_id": sync_log.name,
            "duration": sync_log.duration
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Sync log update failed: {str(e)}", "POS Sync Log")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_sync_statistics(device_id=None, time_range="24h"):
    """Get sync statistics for device or all devices"""
    
    try:
        filters = {}
        if device_id:
            device_doc = frappe.get_doc("POS Device", {"device_id": device_id})
            if device_doc:
                filters["device"] = device_doc.name
        
        # Add time filter based on range
        if time_range == "24h":
            filters["start_time"] = [">=", frappe.utils.add_hours(frappe.utils.now(), -24)]
        elif time_range == "7d":
            filters["start_time"] = [">=", frappe.utils.add_days(frappe.utils.now(), -7)]
        elif time_range == "30d":
            filters["start_time"] = [">=", frappe.utils.add_days(frappe.utils.now(), -30)]
        
        # Get sync logs
        sync_logs = frappe.get_all("POS Sync Log",
            filters=filters,
            fields=["sync_status", "sync_type", "duration", "items_synced", 
                   "transactions_synced", "conflicts_detected", "start_time"],
            order_by="start_time desc")
        
        # Calculate statistics
        total_syncs = len(sync_logs)
        successful_syncs = len([log for log in sync_logs if log.sync_status == "Completed"])
        failed_syncs = len([log for log in sync_logs if log.sync_status == "Failed"])
        
        total_duration = sum([log.duration or 0 for log in sync_logs])
        avg_duration = total_duration / max(total_syncs, 1)
        
        total_items = sum([log.items_synced or 0 for log in sync_logs])
        total_transactions = sum([log.transactions_synced or 0 for log in sync_logs])
        total_conflicts = sum([log.conflicts_detected or 0 for log in sync_logs])
        
        stats = {
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": (successful_syncs / max(total_syncs, 1)) * 100 if total_syncs > 0 else 0,
            "average_duration": avg_duration,
            "total_items_synced": total_items,
            "total_transactions_synced": total_transactions,
            "total_conflicts_detected": total_conflicts,
            "time_range": time_range
        }
        
        return {
            "status": "success",
            "statistics": stats,
            "recent_syncs": sync_logs[:10]  # Return recent 10 sync logs
        }
        
    except Exception as e:
        frappe.log_error(f"Sync statistics retrieval failed: {str(e)}", "POS Sync Log")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_device_sync_history(device_id, limit=50):
    """Get sync history for a specific device"""
    
    try:
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            return {"status": "error", "message": "Device not found"}
        
        sync_history = frappe.get_all("POS Sync Log",
            filters={"device": device.name},
            fields=["sync_type", "sync_status", "start_time", "end_time", "duration", 
                   "items_synced", "transactions_synced", "conflicts_detected"],
            order_by="start_time desc",
            limit=limit)
        
        return {
            "status": "success",
            "device_name": device.device_name,
            "sync_history": sync_history
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def cleanup_old_sync_logs(days_to_keep=90):
    """Clean up old sync log entries to manage database size"""
    
    try:
        cutoff_date = frappe.utils.add_days(frappe.utils.now(), -days_to_keep)
        
        # Get count of old logs
        old_logs_count = frappe.db.count("POS Sync Log", {
            "start_time": ["<", cutoff_date]
        })
        
        if old_logs_count > 0:
            # Delete old logs (archived status recommended in production)
            frappe.db.sql("""
                DELETE FROM `tabPOS Sync Log` 
                WHERE start_time < %s
            """, (cutoff_date,))
            
            frappe.db.commit()
            
            frappe.log_error(
                f"Cleaned up {old_logs_count} old sync log entries older than {days_to_keep} days",
                "POS Sync Log Cleanup"
            )
        
        return {
            "status": "success",
            "deleted_count": old_logs_count
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Sync log cleanup failed: {str(e)}", "POS Sync Log")
        return {
            "status": "error", 
            "message": str(e)
        }