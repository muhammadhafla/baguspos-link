// Copyright (c) 2025, Muhammad Hafla and contributors
// For license information, please see license.txt

frappe.ui.form.on('POS Pricing Rule', {
    setup: function(frm) {
        // Set up calculations and validations
        frm.add_fetch('item_code', 'item_name', 'item_name');
        frm.add_fetch('customer', 'customer_name', 'customer_name');
        
        // Set up pricing type specific fields
        frm.set_df_property('base_price', 'hidden', frm.doc.pricing_type !== 'Base Price' && 
                           frm.doc.pricing_type !== 'Branch Override' && 
                           frm.doc.pricing_type !== 'Customer Price' &&
                           frm.doc.pricing_type !== 'Manual Override');
                           
        frm.set_df_property('discount_percentage', 'hidden', !['Time-based', 'Quantity Break', 'Spend Discount', 'Manual Override'].includes(frm.doc.pricing_type));
        frm.set_df_property('discount_amount', 'hidden', !['Time-based', 'Quantity Break', 'Spend Discount', 'Manual Override'].includes(frm.doc.pricing_type));
        
        frm.set_df_property('min_quantity', 'hidden', frm.doc.pricing_type !== 'Quantity Break');
        frm.set_df_property('max_quantity', 'hidden', frm.doc.pricing_type !== 'Quantity Break');
        
        frm.set_df_property('min_spend_amount', 'hidden', frm.doc.pricing_type !== 'Spend Discount');
        
        frm.set_df_property('bxgy_buy_qty', 'hidden', frm.doc.pricing_type !== 'BXGY');
        frm.set_df_property('bxgy_get_qty', 'hidden', frm.doc.pricing_type !== 'BXGY');
        
        // Time validation
        if (frm.doc.from_time && frm.doc.to_time) {
            const fromTime = new Date('1970-01-01 ' + frm.doc.from_time);
            const toTime = new Date('1970-01-01 ' + frm.doc.to_time);
            
            if (fromTime >= toTime) {
                frm.set_df_property('to_time', 'reqd', 1);
                frappe.msgprint(__('To Time must be after From Time'));
            }
        }
    },
    
    refresh: function(frm) {
        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Pricing'), function() {
                test_pricing_rule(frm);
            });
            
            frm.add_custom_button(__('Apply to Items'), function() {
                apply_to_items(frm);
            });
        }
        
        // Show priority mapping info
        if (frm.doc.priority_level) {
            const priority_info = get_priority_mapping()[frm.doc.priority_level];
            if (priority_info) {
                frm.set_intro(__('ERPNext Priority: {0}', [priority_info.erpnext_priority]), 'blue');
                frm.set_intro(__('Description: {0}', [priority_info.description]), 'grey');
            }
        }
    },
    
    pricing_type: function(frm) {
        // Show/hide fields based on pricing type
        update_field_visibility(frm);
        
        // Set default values based on pricing type
        set_pricing_type_defaults(frm);
    },
    
    priority_level: function(frm) {
        // Update priority info display
        frm.refresh_intro();
    },
    
    from_time: function(frm) {
        validate_time_range(frm);
    },
    
    to_time: function(frm) {
        validate_time_range(frm);
    },
    
    valid_from: function(frm) {
        validate_date_range(frm);
    },
    
    valid_upto: function(frm) {
        validate_date_range(frm);
    }
});

function update_field_visibility(frm) {
    const pricing_type = frm.doc.pricing_type;
    
    // Reset all field visibility
    frm.set_df_property('base_price', 'hidden', !['Base Price', 'Branch Override', 'Customer Price', 'Manual Override'].includes(pricing_type));
    frm.set_df_property('discount_percentage', 'hidden', !['Time-based', 'Quantity Break', 'Spend Discount', 'Manual Override'].includes(pricing_type));
    frm.set_df_property('discount_amount', 'hidden', !['Time-based', 'Quantity Break', 'Spend Discount', 'Manual Override'].includes(pricing_type));
    frm.set_df_property('min_quantity', 'hidden', pricing_type !== 'Quantity Break');
    frm.set_df_property('max_quantity', 'hidden', pricing_type !== 'Quantity Break');
    frm.set_df_property('min_spend_amount', 'hidden', pricing_type !== 'Spend Discount');
    frm.set_df_property('bxgy_buy_qty', 'hidden', pricing_type !== 'BXGY');
    frm.set_df_property('bxgy_get_qty', 'hidden', pricing_type !== 'BXGY');
    frm.set_df_property('days_of_week', 'hidden', !['Time-based'].includes(pricing_type));
    frm.set_df_property('from_time', 'hidden', !['Time-based'].includes(pricing_type));
    frm.set_df_property('to_time', 'hidden', !['Time-based'].includes(pricing_type));
    
    frm.refresh_fields();
}

function set_pricing_type_defaults(frm) {
    const pricing_type = frm.doc.pricing_type;
    
    // Clear fields that shouldn't have values for this pricing type
    if (pricing_type === 'Base Price') {
        frm.set_value('discount_percentage', '');
        frm.set_value('discount_amount', '');
        frm.set_value('min_quantity', '');
        frm.set_value('max_quantity', '');
        frm.set_value('min_spend_amount', '');
        frm.set_value('bxgy_buy_qty', '');
        frm.set_value('bxgy_get_qty', '');
    } else if (pricing_type === 'BXGY') {
        frm.set_value('base_price', '');
        frm.set_value('discount_percentage', '');
        frm.set_value('discount_amount', '');
    } else if (pricing_type === 'Quantity Break') {
        frm.set_value('base_price', '');
        frm.set_value('bxgy_buy_qty', '');
        frm.set_value('bxgy_get_qty', '');
    } else if (pricing_type === 'Spend Discount') {
        frm.set_value('base_price', '');
        frm.set_value('min_quantity', '');
        frm.set_value('max_quantity', '');
        frm.set_value('bxgy_buy_qty', '');
        frm.set_value('bxgy_get_qty', '');
    }
}

function validate_time_range(frm) {
    if (frm.doc.from_time && frm.doc.to_time) {
        const fromTime = new Date('1970-01-01 ' + frm.doc.from_time);
        const toTime = new Date('1970-01-01 ' + frm.doc.to_time);
        
        if (fromTime >= toTime) {
            frappe.msgprint({
                title: __('Invalid Time Range'),
                message: __('To Time must be after From Time'),
                indicator: 'red'
            });
            frm.set_value('to_time', '');
        }
    }
}

function validate_date_range(frm) {
    if (frm.doc.valid_from && frm.doc.valid_upto) {
        if (new Date(frm.doc.valid_from) >= new Date(frm.doc.valid_upto)) {
            frappe.msgprint({
                title: __('Invalid Date Range'),
                message: __('Valid Upto must be after Valid From'),
                indicator: 'red'
            });
            frm.set_value('valid_upto', '');
        }
    }
}

function get_priority_mapping() {
    return {
        '1': { erpnext_priority: 20, description: 'Base Item Price' },
        '2': { erpnext_priority: 19, description: 'Branch Price Override' },
        '3': { erpnext_priority: 18, description: 'Member/Customer Price' },
        '4': { erpnext_priority: 17, description: 'Time-based Promotion' },
        '5': { erpnext_priority: 16, description: 'Quantity Break Discount' },
        '6': { erpnext_priority: 15, description: 'Spend X Discount' },
        '7': { erpnext_priority: 14, description: 'Buy X Get Y (BXGY)' },
        '8': { erpnext_priority: 13, description: 'Manual Override' }
    };
}

function test_pricing_rule(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Test Pricing Rule'),
        fields: [
            {
                fieldname: 'base_price',
                fieldtype: 'Currency',
                label: __('Base Price'),
                reqd: 1
            },
            {
                fieldname: 'quantity',
                fieldtype: 'Float',
                label: __('Quantity'),
                default: 1
            },
            {
                fieldname: 'total_amount',
                fieldtype: 'Currency',
                label: __('Total Amount')
            },
            {
                fieldname: 'item_code',
                fieldtype: 'Link',
                label: __('Item Code'),
                options: 'Item'
            },
            {
                fieldname: 'branch_id',
                fieldtype: 'Data',
                label: __('Branch ID')
            },
            {
                fieldname: 'customer',
                fieldtype: 'Link',
                label: __('Customer'),
                options: 'Customer'
            }
        ],
        primary_action: function() {
            const values = dialog.get_values();
            frappe.call({
                method: 'erpnext_pos_integration.doctype.pos_pricing_rule.pos_pricing_rule.calculate_final_price',
                args: {
                    item_code: values.item_code,
                    base_price: values.base_price,
                    branch_id: values.branch_id,
                    customer: values.customer,
                    quantity: values.quantity,
                    total_amount: values.total_amount
                },
                callback: function(r) {
                    if (r.message) {
                        const result = r.message;
                        frappe.msgprint({
                            title: __('Pricing Test Result'),
                            message: `
                                <b>Original Price:</b> ${format_currency(result.original_price)}<br>
                                <b>Final Price:</b> ${format_currency(result.final_price)}<br>
                                <b>Discount:</b> ${format_currency(result.discount_amount)} (${result.discount_percentage}%)<br>
                                <b>Rule Applied:</b> ${result.rule_applied || 'None'}
                            `,
                            indicator: result.final_price < result.original_price ? 'green' : 'blue'
                        });
                    }
                }
            });
        }
    });
    
    dialog.show();
}

function apply_to_items(frm) {
    frappe.prompt([
        {
            fieldname: 'item_group',
            fieldtype: 'Link',
            label: __('Item Group'),
            options: 'Item Group'
        },
        {
            fieldname: 'brand',
            fieldtype: 'Link',
            label: __('Brand'),
            options: 'Brand'
        }
    ], function(values) {
        frappe.call({
            method: 'erpnext_pos_integration.doctype.pos_pricing_rule.pos_pricing_rule.apply_pricing_rule_to_items',
            args: {
                pricing_rule: frm.doc.name,
                item_group: values.item_group,
                brand: values.brand
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Pricing rule applied to {0} items', [r.message]));
                }
            }
        });
    }, __('Apply to Items'), __('Apply'));
}

// Utility function to format currency
function format_currency(amount) {
    return '₹' + (amount || 0).toFixed(2);
}