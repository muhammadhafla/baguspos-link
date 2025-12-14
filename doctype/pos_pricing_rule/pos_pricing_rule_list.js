// Copyright (c) 2025, Muhammad Hafla and contributors
// For license information, please see license.txt

frappe.listview_settings['POS Pricing Rule'] = {
    add_fields: ["pricing_type", "priority_level", "is_active"],
    get_indicator: function(doc) {
        const status_map = {
            "Active": "green",
            "Inactive": "red"
        };
        return [__(doc.is_active ? "Active" : "Inactive"), status_map[doc.is_active ? "Active" : "Inactive"], "is_active,=," + (doc.is_active ? 1 : 0)];
    },

    formatters: {
        pricing_type(value, doc) {
            const type_colors = {
                "Base Price": "blue",
                "Branch Override": "purple", 
                "Customer Price": "orange",
                "Time-based": "green",
                "Quantity Break": "yellow",
                "Spend Discount": "pink",
                "BXGY": "red",
                "Manual Override": "gray"
            };
            
            return `<span class="indicator-pill ${type_colors[value] || "gray"}">
                        ${value}
                    </span>`;
        },
        
        priority_level(value, doc) {
            const priority_colors = {
                "1": "darkgreen",
                "2": "green", 
                "3": "olive",
                "4": "orange",
                "5": "red",
                "6": "purple",
                "7": "pink",
                "8": "gray"
            };
            
            const priority_labels = {
                "1": "Base Price",
                "2": "Branch Override",
                "3": "Customer Price", 
                "4": "Time-based",
                "5": "Quantity Break",
                "6": "Spend Discount",
                "7": "BXGY",
                "8": "Manual Override"
            };
            
            return `<span class="indicator-pill ${priority_colors[value] || "gray"}">
                        Level ${value} - ${priority_labels[value] || "Unknown"}
                    </span>`;
        }
    },

    onload(listview) {
        // Add custom action buttons
        listview.page.add_action_button(__("Export Rules"), function() {
            export_pricing_rules();
        });
        
        listview.page.add_action_button(__("Import Rules"), function() {
            import_pricing_rules();
        });
        
        listview.page.add_action_button(__("Test All Rules"), function() {
            test_all_pricing_rules();
        });
        
        // Add filter for active/inactive rules
        listview.page.add_filter_button(__("Active Rules"), function() {
            listview.filter_area.add([
                ['POS Pricing Rule', 'is_active', '=', 1]
            ]);
        });
        
        listview.page.add_filter_button(__("Inactive Rules"), function() {
            listview.filter_area.add([
                ['POS Pricing Rule', 'is_active', '=', 0]
            ]);
        });
        
        // Add priority level filter
        listview.page.add_filter_button(__("Priority Filter"), function() {
            show_priority_filter_dialog(listview);
        });
    },

    get_preset_filters() {
        return [
            {
                filter_name: __("Active Pricing Rules"),
                filters: [["POS Pricing Rule", "is_active", "=", 1]]
            },
            {
                filter_name: __("Time-based Promotions"), 
                filters: [["POS Pricing Rule", "pricing_type", "=", "Time-based"]]
            },
            {
                filter_name: __("Quantity Break Discounts"),
                filters: [["POS Pricing Rule", "pricing_type", "=", "Quantity Break"]]
            },
            {
                filter_name: __("BXGY Promotions"),
                filters: [["POS Pricing Rule", "pricing_type", "=", "BXGY"]]
            }
        ];
    }
};

function export_pricing_rules() {
    frappe.call({
        method: 'erpnext_pos_integration.doctype.pos_pricing_rule.pos_pricing_rule.export_pricing_rules',
        callback: function(r) {
            if (r.message) {
                const csv_content = r.message;
                const blob = new Blob([csv_content], { type: 'text/csv' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'pos_pricing_rules.csv';
                link.click();
                
                frappe.show_alert({
                    message: __('Pricing rules exported successfully'),
                    indicator: 'green'
                });
            }
        }
    });
}

function import_pricing_rules() {
    const dialog = new frappe.ui.Dialog({
        title: __('Import Pricing Rules'),
        fields: [
            {
                fieldname: 'csv_file',
                fieldtype: 'Attach',
                label: __('CSV File'),
                reqd: 1
            },
            {
                fieldname: 'overwrite_existing',
                fieldtype: 'Check',
                label: __('Overwrite Existing Rules'),
                default: 0
            }
        ],
        primary_action: function() {
            const values = dialog.get_values();
            const file = frappe.model.get_new_doc('File');
            file.file_url = values.csv_file;
            file.file_name = values.csv_file.split('/').pop();
            
            frappe.call({
                method: 'erpnext_pos_integration.doctype.pos_pricing_rule.pos_pricing_rule.import_pricing_rules',
                args: {
                    file_url: values.csv_file,
                    overwrite_existing: values.overwrite_existing
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Imported {0} pricing rules', [r.message]),
                            indicator: 'green'
                        });
                        dialog.hide();
                        // Refresh listview
                        frappe.set_route('List', 'POS Pricing Rule');
                    }
                }
            });
        }
    });
    
    dialog.show();
}

function test_all_pricing_rules() {
    frappe.call({
        method: 'erpnext_pos_integration.doctype.pos_pricing_rule.pos_pricing_rule.test_all_pricing_rules',
        callback: function(r) {
            if (r.message) {
                const result = r.message;
                frappe.msgprint({
                    title: __('Test Results'),
                    message: `
                        <b>Total Rules:</b> ${result.total_rules}<br>
                        <b>Active Rules:</b> ${result.active_rules}<br>
                        <b>Valid Rules:</b> ${result.valid_rules}<br>
                        <b>Invalid Rules:</b> ${result.invalid_rules}<br>
                        <b>Errors:</b><br>
                        ${result.errors.join('<br>') || 'None'}
                    `,
                    indicator: result.invalid_rules === 0 ? 'green' : 'red'
                });
            }
        }
    });
}

function show_priority_filter_dialog(listview) {
    const dialog = new frappe.ui.Dialog({
        title: __('Filter by Priority Level'),
        fields: [
            {
                fieldname: 'priority_levels',
                fieldtype: 'Table MultiSelect',
                label: __('Priority Levels'),
                options: 'POS Priority Level'
            }
        ],
        primary_action: function() {
            const values = dialog.get_values();
            if (values.priority_levels && values.priority_levels.length > 0) {
                const priority_filters = values.priority_levels.map(p => 
                    ['POS Pricing Rule', 'priority_level', '=', p.priority_level]
                );
                listview.filter_area.add(priority_filters);
            }
            dialog.hide();
        }
    });
    
    // Load priority levels
    frappe.model.with_doctype('POS Priority Level', function() {
        const priority_levels = [
            { priority_level: '1', level_name: 'Base Item Price' },
            { priority_level: '2', level_name: 'Branch Price Override' },
            { priority_level: '3', level_name: 'Member/Customer Price' },
            { priority_level: '4', level_name: 'Time-based Promotion' },
            { priority_level: '5', level_name: 'Quantity Break Discount' },
            { priority_level: '6', level_name: 'Spend X Discount' },
            { priority_level: '7', level_name: 'Buy X Get Y (BXGY)' },
            { priority_level: '8', level_name: 'Manual Override' }
        ];
        
        dialog.fields_dict.priority_levels.df.options = priority_levels;
        dialog.refresh();
    });
    
    dialog.show();
}