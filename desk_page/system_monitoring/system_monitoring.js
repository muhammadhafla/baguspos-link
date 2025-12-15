frappe.pages['system-monitoring'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'System Monitoring',
        single_column: true
    });

    // Render the monitoring dashboard
    page.main.html(`
        <div class="monitoring-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="page-header">
                        <h2><i class="fa fa-line-chart"></i> System Monitoring Dashboard</h2>
                        <p class="text-muted">Real-time system health and performance monitoring</p>
                    </div>
                </div>
            </div>

            <!-- Real-time Metrics -->
            <div class="row" id="realtime-metrics">
                <div class="col-md-3">
                    <div class="card text-white bg-info">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-clock-o"></i> Current Hour
                            </div>
                            <h4 id="current-hour-ops">0</h4>
                            <small>Operations</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-success">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-check-circle"></i> Success Rate
                            </div>
                            <h4 id="success-rate">0%</h4>
                            <small>This Hour</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-warning">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-refresh"></i> Pending Jobs
                            </div>
                            <h4 id="pending-jobs">0</h4>
                            <small>In Queue</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-primary">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-desktop"></i> Active Devices
                            </div>
                            <h4 id="active-devices">0</h4>
                            <small>Currently Online</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Health Alerts -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-exclamation-triangle"></i> System Health Alerts</h5>
                        </div>
                        <div class="card-body">
                            <div id="health-alerts">
                                <div class="text-center">
                                    <i class="fa fa-spinner fa-spin"></i> Loading alerts...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Performance Charts -->
            <div class="row mt-4">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-bar-chart"></i> Performance Trends (Last 7 Days)</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="performance-chart" height="200"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-pie-chart"></i> Device Performance</h5>
                        </div>
                        <div class="card-body">
                            <div id="device-performance">
                                <div class="text-center">
                                    <i class="fa fa-spinner fa-spin"></i> Loading...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Statistics -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-table"></i> System Statistics</h5>
                            <div class="card-tools">
                                <button type="button" class="btn btn-sm btn-primary" onclick="exportStatistics()">
                                    <i class="fa fa-download"></i> Export
                                </button>
                                <button type="button" class="btn btn-sm btn-info" onclick="refreshStatistics()">
                                    <i class="fa fa-refresh"></i> Refresh
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped" id="system-stats-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Total Operations</th>
                                            <th>Success Rate</th>
                                            <th>Avg Response Time</th>
                                            <th>Failed Operations</th>
                                        </tr>
                                    </thead>
                                    <tbody id="system-stats-tbody">
                                        <tr>
                                            <td colspan="5" class="text-center">
                                                <i class="fa fa-spinner fa-spin"></i> Loading...
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-cogs"></i> System Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-warning" onclick="runSystemMaintenance()">
                                    <i class="fa fa-wrench"></i> Run Maintenance
                                </button>
                                <button type="button" class="btn btn-info" onclick="clearSyncQueue()">
                                    <i class="fa fa-trash"></i> Clear Sync Queue
                                </button>
                                <button type="button" class="btn btn-success" onclick="optimizeDatabase()">
                                    <i class="fa fa-database"></i> Optimize Database
                                </button>
                                <button type="button" class="btn btn-primary" onclick="generateReport()">
                                    <i class="fa fa-file-pdf-o"></i> Generate Report
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);

    // Initialize dashboard
    loadRealTimeMetrics();
    loadMonitoringDashboard();
    loadSystemStatistics();
    
    // Auto-refresh every 30 seconds
    setInterval(function() {
        loadRealTimeMetrics();
        loadMonitoringDashboard();
    }, 30000);
    
    // Less frequent refresh for statistics (5 minutes)
    setInterval(function() {
        loadSystemStatistics();
    }, 300000);
};

function loadRealTimeMetrics() {
    frappe.call({
        method: 'desk_page.system_monitoring.system_monitoring.get_real_time_metrics',
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                const stats = data.current_hour_stats;
                const successRate = stats.total_operations > 0 ? 
                    ((stats.successful_operations / stats.total_operations) * 100).toFixed(1) : 0;
                
                $('#current-hour-ops').text(stats.total_operations || 0);
                $('#success-rate').text(successRate + '%');
                $('#pending-jobs').text(data.pending_jobs || 0);
                $('#active-devices').text(data.active_devices || 0);
            }
        }
    });
}

function loadMonitoringDashboard() {
    frappe.call({
        method: 'desk_page.system_monitoring.system_monitoring.get_monitoring_dashboard',
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                
                // Load health alerts
                loadHealthAlerts(data.health_alerts);
                
                // Load device performance
                loadDevicePerformance(data.device_performance);
            }
        }
    });
}

function loadHealthAlerts(healthData) {
    if (healthData && healthData.alerts) {
        const alerts = healthData.alerts;
        let html = '';
        
        if (alerts.length === 0) {
            html = '<div class="alert alert-success"><i class="fa fa-check-circle"></i> All systems operating normally</div>';
        } else {
            alerts.forEach(function(alert) {
                const alertClass = 'alert-' + (alert.severity === 'critical' ? 'danger' : alert.severity);
                html += '<div class="alert ' + alertClass + '">' +
                    '<i class="fa fa-exclamation-triangle"></i> ' + alert.message + 
                    ' <small class="text-muted">(' + new Date(alert.timestamp).toLocaleString() + ')</small>' +
                    '</div>';
            });
        }
        
        $('#health-alerts').html(html);
    }
}

function loadDevicePerformance(deviceData) {
    if (deviceData && deviceData.performance_data) {
        const performance = deviceData.performance_data;
        let html = '';
        
        performance.slice(0, 5).forEach(function(device) {
            const successRate = device.total_syncs > 0 ? 
                ((device.successful_syncs / device.total_syncs) * 100).toFixed(1) : 0;
            
            html += '<div class="mb-2">' +
                '<strong>' + device.device_name + '</strong><br>' +
                '<small>Success Rate: ' + successRate + '% | ' +
                'Avg Response: ' + (device.avg_response_time ? device.avg_response_time.toFixed(0) + 'ms' : 'N/A') + '</small>' +
                '</div>';
        });
        
        if (html === '') {
            html = '<div class="text-muted">No device performance data available</div>';
        }
        
        $('#device-performance').html(html);
    }
}

function loadSystemStatistics() {
    frappe.call({
        method: 'desk_page.system_monitoring.system_monitoring.get_system_statistics',
        callback: function(r) {
            if (r.message && r.message.daily_stats) {
                const stats = r.message.daily_stats;
                let html = '';
                
                stats.forEach(function(stat) {
                    const successRate = stat.total_syncs > 0 ? 
                        ((stat.successful_syncs / stat.total_syncs) * 100).toFixed(1) : 0;
                    
                    html += '<tr>' +
                        '<td>' + frappe.datetime.str_to_user(stat.sync_date) + '</td>' +
                        '<td>' + stat.total_syncs + '</td>' +
                        '<td><span class="badge badge-success">' + successRate + '%</span></td>' +
                        '<td>' + (stat.avg_response_time ? stat.avg_response_time.toFixed(0) + 'ms' : 'N/A') + '</td>' +
                        '<td><span class="badge badge-danger">' + stat.failed_syncs + '</span></td>' +
                        '</tr>';
                });
                
                $('#system-stats-tbody').html(html);
            }
        }
    });
}

// Quick action functions
function runSystemMaintenance() {
    frappe.confirm('Are you sure you want to run system maintenance? This may take a few minutes.', function() {
        frappe.call({
            method: 'api.admin_api.trigger_system_maintenance',
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                    loadSystemStatistics();
                } else {
                    frappe.show_alert({
                        message: 'Maintenance failed: ' + (r.message ? r.message.error : 'Unknown error'),
                        indicator: 'red'
                    });
                }
            }
        });
    });
}

function clearSyncQueue() {
    frappe.confirm('Are you sure you want to clear all pending sync jobs?', function() {
        frappe.call({
            method: 'api.admin_api.clear_sync_queue',
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: 'Sync queue cleared successfully',
                        indicator: 'green'
                    });
                    loadRealTimeMetrics();
                }
            }
        });
    });
}

function optimizeDatabase() {
    frappe.confirm('This will optimize database performance. Continue?', function() {
        frappe.call({
            method: 'api.admin_api.optimize_database',
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: 'Database optimization completed',
                        indicator: 'green'
                    });
                }
            }
        });
    });
}

function generateReport() {
    frappe.call({
        method: 'desk_page.system_monitoring.system_monitoring.generate_monitoring_report',
        callback: function(r) {
            if (r.message && r.message.success) {
                // Open the generated report
                window.open(r.message.report_url, '_blank');
            }
        }
    });
}

function exportStatistics() {
    frappe.call({
        method: 'desk_page.system_monitoring.system_monitoring.export_statistics',
        callback: function(r) {
            if (r.message && r.message.success) {
                window.open(r.message.download_url, '_blank');
            }
        }
    });
}

function refreshStatistics() {
    loadSystemStatistics();
    frappe.show_alert({
        message: 'Statistics refreshed',
        indicator: 'blue'
    });
}