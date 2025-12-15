// Enhanced Pricing Rule Management Interface for POS Pricing Rule

frappe.ui.form.on('POS Pricing Rule', {
    refresh: function(frm) {
        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Rule'), function() {
                testPricingRule(frm);
            });
            
            frm.add_custom_button(__('Preview Calculations'), function() {
                previewCalculations(frm);
            });
            
            frm.add_custom_button(__('View Performance'), function() {
                viewRulePerformance(frm);
            });
        }
        
        // Add priority indicator
        updatePriorityIndicator(frm);
        
        // Setup rule validation
        setupRuleValidation(frm);
    },
    
    rule_type: function(frm) {
        updateRuleTypeFields(frm);
    },
    
    priority: function(frm) {
        updatePriorityIndicator(frm);
    },
    
    disabled: function(frm) {
        updateDisabledIndicator(frm);
    },
    
    onload: function(frm) {
        // Load performance metrics
        loadPerformanceMetrics(frm);
    },
    
    validate: function(frm) {
        validatePricingRule(frm);
    }
});

function testPricingRule(frm) {
    const test_data = {
        item_code: frm.doc.test_item_code || '',
        customer: frm.doc.test_customer || '',
        quantity: frm.doc.test_quantity || 1,
        rule_name: frm.doc.name
    };
    
    frappe.call({
        method: 'api.pricing_api.test_pricing_rule',
        args: test_data,
        callback: function(r) {
            if (r.message && r.message.success) {
                const result = r.message.result;
                frappe.msgprint({
                    title: __('Pricing Rule Test'),
                    message: __('Original Price: ') + result.original_price + 
                             '<br>' + __('Final Price: ') + result.final_price +
                             '<br>' + __('Discount: ') + result.discount_applied +
                             '<br>' + __('Rule Applied: ') + result.rule_applied,
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: 'Test failed: ' + (r.message ? r.message.error : 'Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function previewCalculations(frm) {
    frappe.call({
        method: 'api.pricing_api.preview_calculations',
        args: {
            rule_name: frm.doc.name,
            limit: 10
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                const calculations = r.message.calculations;
                let html = '<table class="table table-striped"><thead><tr>' +
                    '<th>Item Code</th><th>Customer</th><th>Original Price</th>' +
                    '<th>Final Price</th><th>Discount</th><th>Date</th></tr></thead><tbody>';
                
                calculations.forEach(calc => {
                    html += '<tr><td>' + calc.item_code + '</td>' +
                           '<td>' + (calc.customer || 'N/A') + '</td>' +
                           '<td>' + calc.original_price + '</td>' +
                           '<td>' + calc.final_price + '</td>' +
                           '<td>' + calc.discount_applied + '</td>' +
                           '<td>' + frappe.datetime.str_to_user(calc.creation) + '</td></tr>';
                });
                
                html += '</tbody></table>';
                
                frappe.msgprint({
                    title: __('Recent Calculations'),
                    message: html,
                    wide: true
                });
            }
        }
    });
}

function viewRulePerformance(frm) {
    frappe.call({
        method: 'api.pricing_api.get_rule_performance',
        args: {
            rule_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                const perf = r.message.performance;
                const html = '<div class="row">' +
                    '<div class="col-md-6"><h5>Performance Metrics</h5>' +
                    '<p>Total Calculations: ' + perf.total_calculations + '</p>' +
                    '<p>Success Rate: ' + perf.success_rate.toFixed(2) + '%</p>' +
                    '<p>Average Discount: ' + perf.avg_discount.toFixed(2) + '</p></div>' +
                    '<div class="col-md-6"><h5>Recent Activity</h5>' +
                    '<p>Last Calculation: ' + (perf.last_calculation ? 
                        frappe.datetime.str_to_user(perf.last_calculation) : 'Never') + '</p>' +
                    '<p>Total Revenue Impact: ' + perf.revenue_impact.toFixed(2) + '</p></div>' +
                    '</div>';
                
                frappe.msgprint({
                    title: __('Rule Performance'),
                    message: html
                });
            }
        }
    });
}

function updatePriorityIndicator(frm) {
    const priority = frm.doc.priority;
    let indicator_color = 'blue';
    
    if (priority <= 1) {
        indicator_color = 'red';
    } else if (priority <= 3) {
        indicator_color = 'orange';
    } else if (priority <= 5) {
        indicator_color = 'green';
    } else {
        indicator_color = 'blue';
    }
    
    // Update priority field appearance
    frm.fields_dict.priority.$wrapper.find('.control-input').css({
        'border-color': indicator_color,
        'box-shadow': '0 0 5px ' + indicator_color + '40'
    });
}

function updateRuleTypeFields(frm) {
    const rule_type = frm.doc.rule_type;
    
    // Show/hide fields based on rule type
    frm.fields_dict.discount_percentage.$wrapper.toggle(rule_type === 'Discount');
    frm.fields_dict.fixed_price.$wrapper.toggle(rule_type === 'Fixed Price');
    frm.fields_dict.price_override.$wrapper.toggle(rule_type === 'Price Override');
}

function updateDisabledIndicator(frm) {
    const disabled = frm.doc.disabled;
    const color = disabled ? 'red' : 'green';
    
    frm.fields_dict.rule_name.$wrapper.find('.control-label').css({
        'color': color
    });
}

function loadPerformanceMetrics(frm) {
    frappe.call({
        method: 'api.pricing_api.get_rule_performance',
        args: {
            rule_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                const perf = r.message.performance;
                
                // Add performance summary to the form
                frm.fields_dict.rule_name.$wrapper.find('.help-box').remove();
                frm.fields_dict.rule_name.$wrapper.append(
                    '<div class="help-box"><small>' +
                    'Total Calculations: ' + perf.total_calculations + ' | ' +
                    'Success Rate: ' + perf.success_rate.toFixed(1) + '% | ' +
                    'Revenue Impact: ' + perf.revenue_impact.toFixed(2) +
                    '</small></div>'
                );
            }
        }
    });
}

function setupRuleValidation(frm) {
    // Add custom validation for pricing rules
    if (frm.doc.rule_type === 'Discount' && frm.doc.discount_percentage > 100) {
        frappe.msgprint(__('Discount percentage cannot exceed 100%'));
        frm.set_value('discount_percentage', 100);
    }
    
    if (frm.doc.rule_type === 'Fixed Price' && frm.doc.fixed_price < 0) {
        frappe.msgprint(__('Fixed price cannot be negative'));
        frm.set_value('fixed_price', 0);
    }
}

function validatePricingRule(frm) {
    let errors = [];
    
    // Validate date range
    if (frm.doc.valid_from && frm.doc.valid_to && 
        frm.doc.valid_from >= frm.doc.valid_to) {
        errors.push(__('Valid From date must be before Valid To date'));
    }
    
    // Validate priority
    if (frm.doc.priority < 1 || frm.doc.priority > 10) {
        errors.push(__('Priority must be between 1 and 10'));
    }
    
    if (errors.length > 0) {
        frappe.throw(errors.join('<br>'));
    }
}