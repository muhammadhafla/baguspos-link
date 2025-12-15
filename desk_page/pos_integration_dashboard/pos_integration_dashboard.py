import frappe
from frappe import _

@frappe.whitelist()
def get_dashboard_data():
    """Get dashboard data for POS Integration Bridge App"""
    
    # Get device statistics
    total_devices = frappe.db.count('POS Device')
    active_devices = frappe.db.count('POS Device', {'status': 'Active'})
    inactive_devices = frappe.db.count('POS Device', {'status': 'Inactive'})
    
    # Get pricing rule statistics
    total_pricing_rules = frappe.db.count('POS Pricing Rule')
    active_pricing_rules = frappe.db.count('POS Pricing Rule', {'disabled': 0})
    
    # Get recent sync logs
    recent_logs = frappe.get_all('POS Sync Log', 
        fields=['name', 'device_name', 'sync_type', 'status', 'creation'],
        order_by='creation desc',
        limit=10
    )
    
    # Get today's sync statistics
    today = frappe.utils.today()
    sync_stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_syncs,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_syncs
        FROM `tabPOS Sync Log`
        WHERE DATE(creation) = %s
    """, today, as_dict=True)[0]
    
    return {
        'device_stats': {
            'total': total_devices,
            'active': active_devices,
            'inactive': inactive_devices
        },
        'pricing_stats': {
            'total': total_pricing_rules,
            'active': active_pricing_rules
        },
        'sync_stats': sync_stats,
        'recent_logs': recent_logs
    }

@frappe.whitelist()
def get_device_health_summary():
    """Get device health summary for dashboard"""
    
    devices = frappe.get_all('POS Device', 
        fields=['name', 'device_name', 'device_type', 'location', 'status', 'last_sync'],
        order_by='creation desc'
    )
    
    health_summary = []
    for device in devices:
        # Calculate device health status
        last_sync = device.last_sync
        status = device.status
        
        if status == 'Inactive':
            health_status = 'Offline'
            health_color = 'red'
        elif not last_sync:
            health_status = 'No Sync Data'
            health_color = 'orange'
        else:
            import datetime
            last_sync_date = frappe.utils.getdate(last_sync)
            days_since_sync = (frappe.utils.today_date() - last_sync_date).days
            
            if days_since_sync <= 1:
                health_status = 'Healthy'
                health_color = 'green'
            elif days_since_sync <= 7:
                health_status = 'Warning'
                health_color = 'orange'
            else:
                health_status = 'Critical'
                health_color = 'red'
        
        device['health_status'] = health_status
        device['health_color'] = health_color
        health_summary.append(device)
    
    return health_summary

@frappe.whitelist()
def get_pricing_performance():
    """Get pricing engine performance metrics"""
    
    # Get pricing calculation statistics
    recent_calculations = frappe.get_all('POS Sync Log',
        fields=['name', 'sync_type', 'status', 'creation'],
        filters={'sync_type': 'Pricing Calculation'},
        order_by='creation desc',
        limit=50
    )
    
    success_rate = 0
    if recent_calculations:
        successful = len([log for log in recent_calculations if log.status == 'Success'])
        success_rate = (successful / len(recent_calculations)) * 100
    
    return {
        'recent_calculations': recent_calculations,
        'success_rate': round(success_rate, 2),
        'total_calculations': len(recent_calculations)
    }