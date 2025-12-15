import frappe
from frappe import _
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def get_system_overview():
    """Get system overview for admin dashboard"""
    
    # Get system statistics
    total_devices = frappe.db.count('POS Device')
    active_devices = frappe.db.count('POS Device', {'status': 'Active'})
    total_pricing_rules = frappe.db.count('POS Pricing Rule')
    active_pricing_rules = frappe.db.count('POS Pricing Rule', {'disabled': 0})
    
    # Get sync statistics for last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    sync_stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_syncs,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_syncs,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_sync_time
        FROM `tabPOS Sync Log`
        WHERE creation >= %s
    """, yesterday.strftime('%Y-%m-%d %H:%M:%S'), as_dict=True)[0]
    
    # Get error statistics
    error_logs = frappe.get_all('POS Sync Log',
        filters={'status': 'Failed'},
        fields=['error_message', 'sync_type', 'creation'],
        order_by='creation desc',
        limit=10
    )
    
    return {
        'device_stats': {
            'total': total_devices,
            'active': active_devices,
            'inactive': total_devices - active_devices
        },
        'pricing_stats': {
            'total': total_pricing_rules,
            'active': active_pricing_rules,
            'disabled': total_pricing_rules - active_pricing_rules
        },
        'sync_stats': sync_stats,
        'error_logs': error_logs
    }

@frappe.whitelist()
def get_device_performance_metrics(device_name=None):
    """Get performance metrics for devices"""
    
    where_clause = ""
    if device_name:
        where_clause = "WHERE device_name = %s"
        params = (device_name,)
    else:
        params = ()
    
    # Get device performance data
    performance_data = frappe.db.sql(f"""
        SELECT 
            device_name,
            COUNT(*) as total_syncs,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_syncs,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_response_time,
            MAX(creation) as last_sync
        FROM `tabPOS Sync Log`
        {where_clause}
        GROUP BY device_name
        ORDER BY total_syncs DESC
    """, params, as_dict=True)
    
    return {
        'performance_data': performance_data,
        'timestamp': datetime.now().isoformat()
    }

@frappe.whitelist()
def get_pricing_performance_metrics():
    """Get pricing engine performance metrics"""
    
    # Get pricing calculation statistics
    pricing_stats = frappe.db.sql("""
        SELECT 
            sync_type,
            COUNT(*) as total_calculations,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_calculations,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_calculation_time,
            MAX(creation) as last_calculation
        FROM `tabPOS Sync Log`
        WHERE sync_type LIKE %s
        GROUP BY sync_type
    """, ('%Pricing%',), as_dict=True)
    
    # Get rule performance
    rule_performance = frappe.db.sql("""
        SELECT 
            pr.rule_name,
            pr.rule_type,
            COUNT(sl.name) as total_calculations,
            SUM(CASE WHEN sl.status = 'Success' THEN 1 ELSE 0 END) as successful_calculations,
            AVG(CASE WHEN sl.status = 'Success' THEN 
                CASE 
                    WHEN pr.rule_type = 'Discount' THEN sl.original_price * (pr.discount_percentage / 100)
                    WHEN pr.rule_type = 'Fixed Price' THEN sl.original_price - pr.fixed_price
                    ELSE 0 
                END
                ELSE NULL 
            END) as avg_discount_applied
        FROM `tabPOS Pricing Rule` pr
        LEFT JOIN `tabPOS Sync Log` sl ON sl.pricing_rule = pr.name
        WHERE pr.disabled = 0
        GROUP BY pr.name, pr.rule_name, pr.rule_type
        ORDER BY total_calculations DESC
    """, as_dict=True)
    
    return {
        'pricing_stats': pricing_stats,
        'rule_performance': rule_performance,
        'timestamp': datetime.now().isoformat()
    }

@frappe.whitelist()
def get_system_health_alerts():
    """Get system health alerts"""
    
    alerts = []
    
    # Check for devices not synced in 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    inactive_devices = frappe.get_all('POS Device',
        filters={'status': 'Active', 'last_sync': ['<', yesterday]},
        fields=['name', 'device_name', 'last_sync']
    )
    
    for device in inactive_devices:
        days_since_sync = (datetime.now() - device.last_sync).days
        alerts.append({
            'type': 'device_inactive',
            'severity': 'warning' if days_since_sync <= 7 else 'critical',
            'message': f"Device {device.device_name} has not synced for {days_since_sync} days",
            'device_name': device.device_name,
            'timestamp': datetime.now().isoformat()
        })
    
    # Check for high error rates
    error_rate = frappe.db.sql("""
        SELECT 
            device_name,
            COUNT(*) as total_syncs,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_syncs,
            (SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as error_rate
        FROM `tabPOS Sync Log`
        WHERE creation >= %s
        GROUP BY device_name
        HAVING error_rate > 20
    """, yesterday.strftime('%Y-%m-%d %H:%M:%S'), as_dict=True)
    
    for device in error_rate:
        alerts.append({
            'type': 'high_error_rate',
            'severity': 'warning',
            'message': f"Device {device.device_name} has {device.error_rate:.1f}% error rate",
            'device_name': device.device_name,
            'error_rate': device.error_rate,
            'timestamp': datetime.now().isoformat()
        })
    
    # Check for disabled pricing rules with recent usage
    recent_pricing = frappe.db.sql("""
        SELECT DISTINCT pr.name, pr.rule_name, sl.creation
        FROM `tabPOS Pricing Rule` pr
        INNER JOIN `tabPOS Sync Log` sl ON sl.pricing_rule = pr.name
        WHERE pr.disabled = 1 
        AND sl.creation >= %s
        AND sl.status = 'Success'
    """, yesterday.strftime('%Y-%m-%d %H:%M:%S'), as_dict=True)
    
    for rule in recent_pricing:
        alerts.append({
            'type': 'disabled_rule_used',
            'severity': 'info',
            'message': f"Disabled pricing rule {rule.rule_name} was recently used",
            'rule_name': rule.rule_name,
            'timestamp': datetime.now().isoformat()
        })
    
    return {
        'alerts': alerts,
        'total_alerts': len(alerts),
        'timestamp': datetime.now().isoformat()
    }

@frappe.whitelist()
def get_sync_queue_status():
    """Get current sync queue status"""
    
    # Get pending sync jobs
    pending_syncs = frappe.db.sql("""
        SELECT 
            device_name,
            sync_type,
            COUNT(*) as pending_count,
            MIN(creation) as oldest_request
        FROM `tabPOS Sync Log`
        WHERE status = 'Pending'
        GROUP BY device_name, sync_type
        ORDER BY oldest_request
    """, as_dict=True)
    
    # Get sync performance by hour
    hourly_stats = frappe.db.sql("""
        SELECT 
            HOUR(creation) as sync_hour,
            COUNT(*) as total_syncs,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_time
        FROM `tabPOS Sync Log`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        GROUP BY HOUR(creation)
        ORDER BY sync_hour
    """, as_dict=True)
    
    return {
        'pending_syncs': pending_syncs,
        'hourly_stats': hourly_stats,
        'timestamp': datetime.now().isoformat()
    }

@frappe.whitelist()
def trigger_system_maintenance():
    """Trigger system maintenance tasks"""
    
    try:
        # Clean up old sync logs (keep last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        deleted_logs = frappe.db.sql("""
            DELETE FROM `tabPOS Sync Log`
            WHERE creation < %s
        """, cutoff_date.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Recalculate device statistics
        frappe.db.sql("""
            UPDATE `tabPOS Device` 
            SET total_syncs = (
                SELECT COUNT(*) 
                FROM `tabPOS Sync Log` 
                WHERE device_name = `tabPOS Device`.name
            ),
            last_sync = (
                SELECT MAX(creation) 
                FROM `tabPOS Sync Log` 
                WHERE device_name = `tabPOS Device`.name
            )
        """)
        
        frappe.db.commit()
        
        return {
            'success': True,
            'message': f'System maintenance completed. Cleaned up {deleted_logs[0] if deleted_logs else 0} old records.',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        frappe.db.rollback()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }