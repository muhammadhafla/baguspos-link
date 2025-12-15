// Enhanced Device Management Interface for POS Device

frappe.ui.form.on('POS Device', {
    refresh: function(frm) {
        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Connection'), function() {
                testDeviceConnection(frm);
            });
            
            frm.add_custom_button(__('Sync Device'), function() {
                syncDeviceData(frm);
            });
            
            frm.add_custom_button(__('View Logs'), function() {
                viewDeviceLogs(frm);
            });
        }
        
        // Add status indicator
        updateStatusIndicator(frm);
        
        // Setup auto-sync if device is active
        if (frm.doc.status === 'Active') {
            setupAutoSync(frm);
        }
    },
    
    status: function(frm) {
        updateStatusIndicator(frm);
    },
    
    device_type: function(frm) {
        // Update available fields based on device type
        updateDeviceTypeFields(frm);
    },
    
    onload: function(frm) {
        // Load device health information
        loadDeviceHealthInfo(frm);
    }
});

function testDeviceConnection(frm) {
    frappe.call({
        method: 'api.device_api.test_device_connection',
        args: {
            device_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: 'Device connection successful',
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.show_alert({
                    message: r.message ? r.message.error : 'Connection test failed',
                    indicator: 'red'
                });
            }
        }
    });
}

function syncDeviceData(frm) {
    frappe.call({
        method: 'api.device_api.sync_device_data',
        args: {
            device_name: frm.doc.name,
            sync_type: 'Full Sync'
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: 'Device sync initiated successfully',
                    indicator: 'blue'
                });
            } else {
                frappe.show_alert({
                    message: 'Device sync failed: ' + (r.message ? r.message.error : 'Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function viewDeviceLogs(frm) {
    frappe.route_options = {
        'device_name': frm.doc.name
    };
    frappe.set_route('List', 'POS Sync Log');
}

function updateStatusIndicator(frm) {
    const status = frm.doc.status;
    let indicator_color = 'orange';
    
    switch(status) {
        case 'Active':
            indicator_color = 'green';
            break;
        case 'Inactive':
            indicator_color = 'red';
            break;
        case 'Maintenance':
            indicator_color = 'orange';
            break;
        default:
            indicator_color = 'gray';
    }
    
    // Update the status field appearance
    frm.fields_dict.status.$wrapper.find('.control-input').css({
        'border-color': indicator_color,
        'box-shadow': '0 0 5px ' + indicator_color + '40'
    });
}

function updateDeviceTypeFields(frm) {
    const device_type = frm.doc.device_type;
    
    // Show/hide fields based on device type
    frm.fields_dict.api_endpoint.$wrapper.toggle(device_type === 'API');
    frm.fields_dict.com_port.$wrapper.toggle(device_type === 'Serial');
    frm.fields_dict.network_config.$wrapper.toggle(device_type === 'Network');
}

function loadDeviceHealthInfo(frm) {
    frappe.call({
        method: 'desk_page.pos_integration_dashboard.pos_integration_dashboard.get_device_health_summary',
        callback: function(r) {
            if (r.message) {
                const device = r.message.find(d => d.name === frm.doc.name);
                if (device) {
                    // Update health status display
                    frm.fields_dict.device_name.$wrapper.find('.help-box').remove();
                    frm.fields_dict.device_name.$wrapper.append(
                        '<div class="help-box"><small>' +
                        '<span class="badge badge-' + device.health_color + '">' +
                        device.health_status + '</span> - Last sync: ' +
                        (device.last_sync ? frappe.datetime.str_to_user(device.last_sync) : 'Never') +
                        '</small></div>'
                    );
                }
            }
        }
    });
}

function setupAutoSync(frm) {
    // Set up automatic sync every 5 minutes for active devices
    if (!frm.doc.auto_sync_interval) {
        frm.doc.auto_sync_interval = 5; // minutes
        frm.set_value('auto_sync_interval', 5);
    }
}