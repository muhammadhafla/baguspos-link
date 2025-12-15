frappe.pages['pos-integration-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'POS Integration Dashboard',
        single_column: true
    });

    // Render the dashboard
    page.main.html(`
        <div class="dashboard-container">
            <div class="row">
                <div class="col-md-12">
                    <div class="page-header">
                        <h2><i class="fa fa-tachometer"></i> POS Integration Dashboard</h2>
                        <p class="text-muted">Monitor your POS devices, pricing rules, and sync status</p>
                    </div>
                </div>
            </div>

            <!-- Statistics Cards -->
            <div class="row" id="stats-cards">
                <div class="col-md-3">
                    <div class="card text-white bg-primary">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-desktop"></i> Total Devices
                            </div>
                            <h3 id="total-devices">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-success">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-check-circle"></i> Active Devices
                            </div>
                            <h3 id="active-devices">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-info">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-tags"></i> Pricing Rules
                            </div>
                            <h3 id="total-pricing-rules">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-warning">
                        <div class="card-body">
                            <div class="card-title">
                                <i class="fa fa-refresh"></i> Today's Syncs
                            </div>
                            <h3 id="today-syncs">0</h3>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Device Health Status -->
            <div class="row mt-4">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-heartbeat"></i> Device Health Status</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped" id="device-health-table">
                                    <thead>
                                        <tr>
                                            <th>Device Name</th>
                                            <th>Type</th>
                                            <th>Location</th>
                                            <th>Status</th>
                                            <th>Health</th>
                                            <th>Last Sync</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="device-health-tbody">
                                        <tr>
                                            <td colspan="7" class="text-center">
                                                <i class="fa fa-spinner fa-spin"></i> Loading...
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-bar-chart"></i> Sync Performance</h5>
                        </div>
                        <div class="card-body">
                            <div id="sync-performance">
                                <div class="text-center">
                                    <i class="fa fa-spinner fa-spin"></i> Loading...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fa fa-clock-o"></i> Recent Sync Activity</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped" id="recent-logs-table">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Device</th>
                                            <th>Sync Type</th>
                                            <th>Status</th>
                                            <th>Details</th>
                                        </tr>
                                    </thead>
                                    <tbody id="recent-logs-tbody">
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
                            <h5><i class="fa fa-bolt"></i> Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-primary" onclick="addNewDevice()">
                                    <i class="fa fa-plus"></i> Add Device
                                </button>
                                <button type="button" class="btn btn-success" onclick="addPricingRule()">
                                    <i class="fa fa-plus"></i> Add Pricing Rule
                                </button>
                                <button type="button" class="btn btn-info" onclick="syncAllDevices()">
                                    <i class="fa fa-refresh"></i> Sync All Devices
                                </button>
                                <button type="button" class="btn btn-warning" onclick="viewReports()">
                                    <i class="fa fa-bar-chart"></i> View Reports
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);

    // Load dashboard data
    loadDashboardData();
    loadDeviceHealth();
    loadSyncPerformance();
    loadRecentLogs();

    // Auto-refresh every 30 seconds
    setInterval(function() {
        loadDashboardData();
        loadDeviceHealth();
        loadSyncPerformance();
        loadRecentLogs();
    }, 30000);
};

function loadDashboardData() {
    frappe.call({
        method: 'desk_page.pos_integration_dashboard.pos_integration_dashboard.get_dashboard_data',
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                
                // Update statistics cards
                $('#total-devices').text(data.device_stats.total);
                $('#active-devices').text(data.device_stats.active);
                $('#total-pricing-rules').text(data.pricing_stats.total);
                $('#today-syncs').text(data.sync_stats.total_syncs || 0);
            }
        }
    });
}

function loadDeviceHealth() {
    frappe.call({
        method: 'desk_page.pos_integration_dashboard.pos_integration_dashboard.get_device_health_summary',
        callback: function(r) {
            if (r.message) {
                const devices = r.message;
                let html = '';
                
                devices.forEach(function(device) {
                    const healthClass = 'badge badge-' + device.health_color;
                    const statusClass = device.status === 'Active' ? 'badge badge-success' : 'badge badge-secondary';
                    
                    html += '<tr>' +
                        '<td><strong>' + device.device_name + '</strong></td>' +
                        '<td>' + (device.device_type || 'N/A') + '</td>' +
                        '<td>' + (device.location || 'N/A') + '</td>' +
                        '<td><span class="' + statusClass + '">' + device.status + '</span></td>' +
                        '<td><span class="' + healthClass + '">' + device.health_status + '</span></td>' +
                        '<td>' + (device.last_sync ? frappe.datetime.str_to_user(device.last_sync) : 'Never') + '</td>' +
                        '<td><button class="btn btn-sm btn-outline-primary" onclick="editDevice(\'' + device.name + '\')">' +
                        '<i class="fa fa-edit"></i></button></td>' +
                        '</tr>';
                });
                
                if (html === '') {
                    html = '<tr><td colspan="7" class="text-center text-muted">No devices found</td></tr>';
                }
                
                $('#device-health-tbody').html(html);
            }
        }
    });
}

function loadSyncPerformance() {
    frappe.call({
        method: 'desk_page.pos_integration_dashboard.pos_integration_dashboard.get_pricing_performance',
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                const successRate = data.success_rate || 0;
                const total = data.total_calculations || 0;
                
                // Use string concatenation to avoid template literal issues in CSS
                var html = '<div class="text-center">' +
                    '<div class="progress mb-3">' +
                    '<div class="progress-bar bg-success" role="progressbar" ' +
                    'style="width: ' + successRate + '%" aria-valuenow="' + successRate + '" ' +
                    'aria-valuemin="0" aria-valuemax="100">' +
                    successRate.toFixed(1) + '%' +
                    '</div>' +
                    '</div>' +
                    '<p><strong>Success Rate:</strong> ' + successRate.toFixed(1) + '%</p>' +
                    '<p><strong>Total Calculations:</strong> ' + total + '</p>' +
                    '</div>';
                
                $('#sync-performance').html(html);
            }
        }
    });
}

function loadRecentLogs() {
    frappe.call({
        method: 'desk_page.pos_integration_dashboard.pos_integration_dashboard.get_dashboard_data',
        callback: function(r) {
            if (r.message && r.message.recent_logs) {
                const logs = r.message.recent_logs;
                let html = '';
                
                logs.forEach(function(log) {
                    const statusClass = log.status === 'Success' ? 'badge badge-success' : 'badge badge-danger';
                    
                    html += '<tr>' +
                        '<td>' + frappe.datetime.str_to_user(log.creation) + '</td>' +
                        '<td>' + (log.device_name || 'System') + '</td>' +
                        '<td>' + log.sync_type + '</td>' +
                        '<td><span class="' + statusClass + '">' + log.status + '</span></td>' +
                        '<td><button class="btn btn-sm btn-outline-info" onclick="viewLogDetails(\'' + log.name + '\')">' +
                        '<i class="fa fa-eye"></i> View</button></td>' +
                        '</tr>';
                });
                
                if (html === '') {
                    html = '<tr><td colspan="5" class="text-center text-muted">No recent activity</td></tr>';
                }
                
                $('#recent-logs-tbody').html(html);
            }
        }
    });
}

// Quick action functions
function addNewDevice() {
    frappe.set_route('Form', 'POS Device', 'new');
}

function addPricingRule() {
    frappe.set_route('Form', 'POS Pricing Rule', 'new');
}

function syncAllDevices() {
    frappe.confirm('Are you sure you want to sync all devices?', function() {
        frappe.call({
            method: 'api.device_api.sync_all_devices',
            callback: function(r) {
                if (r.message) {
                    frappe.show_alert({
                        message: 'Sync initiated for all devices',
                        indicator: 'green'
                    });
                }
            }
        });
    });
}

function viewReports() {
    frappe.set_route('query-report', 'POS Integration Summary');
}

function editDevice(deviceName) {
    frappe.set_route('Form', 'POS Device', deviceName);
}

function viewLogDetails(logName) {
    frappe.set_route('Form', 'POS Sync Log', logName);
}