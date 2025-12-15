import frappe
from frappe import _
from datetime import datetime, timedelta

@frappe.whitelist()
def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    
    # Get system overview
    from api.admin_api import get_system_overview
    system_overview = get_system_overview()
    
    # Get device performance metrics
    from api.admin_api import get_device_performance_metrics
    device_performance = get_device_performance_metrics()
    
    # Get pricing performance
    from api.admin_api import get_pricing_performance_metrics
    pricing_performance = get_pricing_performance_metrics()
    
    # Get system health alerts
    from api.admin_api import get_system_health_alerts
    health_alerts = get_system_health_alerts()
    
    # Get sync queue status
    from api.admin_api import get_sync_queue_status
    sync_queue = get_sync_queue_status()
    
    return {
        'system_overview': system_overview,
        'device_performance': device_performance,
        'pricing_performance': pricing_performance,
        'health_alerts': health_alerts,
        'sync_queue': sync_queue,
        'timestamp': datetime.now().isoformat()
    }

@frappe.whitelist()
def get_real_time_metrics():
    """Get real-time metrics for live monitoring"""
    
    # Current hour statistics
    now = datetime.now()
    start_of_hour = now.replace(minute=0, second=0, microsecond=0)
    
    current_hour_stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_operations,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_operations,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_operations,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_response_time
        FROM `tabPOS Sync Log`
        WHERE creation >= %s
    """, start_of_hour.strftime('%Y-%m-%d %H:%M:%S'), as_dict=True)[0]
    
    # Active devices count
    active_devices = frappe.db.count('POS Device', {'status': 'Active'})
    
    # Current pending sync jobs
    pending_jobs = frappe.db.count('POS Sync Log', {'status': 'Pending'})
    
    # Last 15 minutes activity
    fifteen_min_ago = now - timedelta(minutes=15)
    recent_activity = frappe.db.count('POS Sync Log', {'creation': ['>=', fifteen_min_ago]})
    
    return {
        'current_hour_stats': current_hour_stats,
        'active_devices': active_devices,
        'pending_jobs': pending_jobs,
        'recent_activity': recent_activity,
        'timestamp': now.isoformat()
    }

@frappe.whitelist()
def get_system_statistics():
    """Get detailed system statistics"""
    
    # Daily statistics for last 30 days
    daily_stats = frappe.db.sql("""
        SELECT 
            DATE(creation) as sync_date,
            COUNT(*) as total_syncs,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_syncs,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_response_time
        FROM `tabPOS Sync Log`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(creation)
        ORDER BY sync_date DESC
    """, as_dict=True)
    
    # Device uptime statistics
    device_uptime = frappe.db.sql("""
        SELECT 
            pd.device_name,
            pd.status,
            COUNT(sl.name) as total_syncs_30_days,
            SUM(CASE WHEN sl.status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
            (SUM(CASE WHEN sl.status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(sl.name)) as uptime_percentage,
            MAX(sl.creation) as last_activity
        FROM `tabPOS Device` pd
        LEFT JOIN `tabPOS Sync Log` sl ON sl.device_name = pd.name 
            AND sl.creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY pd.name, pd.device_name, pd.status
        ORDER BY uptime_percentage DESC
    """, as_dict=True)
    
    # Pricing rule effectiveness
    rule_effectiveness = frappe.db.sql("""
        SELECT 
            pr.rule_name,
            pr.rule_type,
            pr.disabled,
            COUNT(sl.name) as usage_count,
            SUM(CASE WHEN sl.status = 'Success' THEN sl.discount_applied ELSE 0 END) as total_discount_given,
            AVG(CASE WHEN sl.status = 'Success' THEN sl.discount_applied ELSE NULL END) as avg_discount
        FROM `tabPOS Pricing Rule` pr
        LEFT JOIN `tabPOS Sync Log` sl ON sl.pricing_rule = pr.name 
            AND sl.creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY pr.name, pr.rule_name, pr.rule_type, pr.disabled
        ORDER BY usage_count DESC
    """, as_dict=True)
    
    return {
        'daily_stats': daily_stats,
        'device_uptime': device_uptime,
        'rule_effectiveness': rule_effectiveness,
        'timestamp': datetime.now().isoformat()
    }

@frappe.whitelist()
def get_alert_history():
    """Get historical alert data"""
    
    # Get recent failed syncs
    recent_failures = frappe.get_all('POS Sync Log',
        fields=['name', 'device_name', 'sync_type', 'status', 'error_message', 'creation'],
        filters={'status': 'Failed'},
        order_by='creation desc',
        limit=50
    )
    
    # Get devices with issues
    problematic_devices = frappe.db.sql("""
        SELECT 
            pd.device_name,
            pd.status,
            COUNT(sl.name) as failure_count_7_days,
            MAX(sl.creation) as last_failure
        FROM `tabPOS Device` pd
        LEFT JOIN `tabPOS Sync Log` sl ON sl.device_name = pd.name 
            AND sl.status = 'Failed'
            AND sl.creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY pd.name, pd.device_name, pd.status
        HAVING failure_count_7_days > 0
        ORDER BY failure_count_7_days DESC
    """, as_dict=True)
    
    return {
        'recent_failures': recent_failures,
        'problematic_devices': problematic_devices,
        'timestamp': datetime.now().isoformat()
    }

@frappe.whitelist()
def get_performance_trends():
    """Get performance trend analysis"""
    
    # Weekly performance trends
    weekly_trends = frappe.db.sql("""
        SELECT 
            YEARWEEK(creation, 1) as week_year,
            WEEK(creation, 1) as week_number,
            COUNT(*) as total_operations,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_operations,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_response_time
        FROM `tabPOS Sync Log`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL 12 WEEK)
        GROUP BY YEARWEEK(creation, 1), WEEK(creation, 1)
        ORDER BY week_year DESC
    """, as_dict=True)
    
    # Device performance comparison
    device_comparison = frappe.db.sql("""
        SELECT 
            device_name,
            COUNT(*) as total_operations,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_operations,
            (SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as success_rate,
            AVG(CASE WHEN status = 'Success' THEN TIMESTAMPDIFF(SECOND, creation, completion_time) ELSE NULL END) as avg_response_time
        FROM `tabPOS Sync Log`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY device_name
        ORDER BY success_rate DESC
    """, as_dict=True)
    
    return {
        'weekly_trends': weekly_trends,
        'device_comparison': device_comparison,
        'timestamp': datetime.now().isoformat()
    }