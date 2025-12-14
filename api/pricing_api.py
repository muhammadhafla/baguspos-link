# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, flt
from erpnext_pos_integration.utils.pricing_engine import PricingEngine
from erpnext_pos_integration.doctype.pos_device.pos_device import validate_device_credentials
import json
import time

@frappe.whitelist()
def calculate_price(device_id, api_key, item_code, base_price, quantity=1, 
                   total_amount=0, customer=None, branch_id=None):
    """
    Calculate final price using 8-level pricing engine
    
    Args:
        device_id (str): POS device identifier
        api_key (str): Device API key for authentication
        item_code (str): Item code to calculate price for
        base_price (float): Base item price
        quantity (int): Quantity being purchased
        total_amount (float): Total transaction amount
        customer (str): Customer ID (optional)
        branch_id (str): Branch ID (optional)
    
    Returns:
        dict: Price calculation result with authentication status
    """
    
    try:
        # Input validation
        if not all([device_id, api_key, item_code, base_price]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key, item_code, base_price"),
                "authenticated": False
            }
        
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {
                "status": "error",
                "message": _("Invalid device credentials"),
                "authenticated": False
            }
        
        # Validate input types
        try:
            base_price = flt(base_price)
            quantity = flt(quantity)
            total_amount = flt(total_amount)
        except (ValueError, TypeError):
            return {
                "status": "error",
                "message": _("Invalid numeric parameters"),
                "authenticated": True
            }
        
        # Get device context
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            return {
                "status": "error",
                "message": _("Device not found"),
                "authenticated": True
            }
        
        # Use branch from device if not provided
        if not branch_id and device.branch:
            branch_id = device.branch
        
        # Initialize pricing engine
        pricing_engine = PricingEngine()
        
        # Calculate price
        start_time = time.time()
        price_result = pricing_engine.calculate_price(
            item_code=item_code,
            base_price=base_price,
            quantity=quantity,
            total_amount=total_amount,
            customer=customer,
            branch_id=branch_id,
            device_id=device_id
        )
        calculation_time = time.time() - start_time
        
        # Build response
        response = {
            "status": "success",
            "authenticated": True,
            "device_id": device_id,
            "device_name": device.device_name,
            "branch_id": branch_id,
            "item_code": item_code,
            "calculation_time_ms": round(calculation_time * 1000, 2),
            "price_data": price_result,
            "timestamp": now()
        }
        
        # Add performance warning if calculation is slow
        if calculation_time > 0.5:
            response["performance_warning"] = "Price calculation slower than expected"
        
        # Log successful calculation
        frappe.log_error(
            f"Price calculated successfully for device {device_id}, item {item_code}: "
            f"${price_result['final_price']} (rule: {price_result.get('rule_applied', 'none')})",
            "POS Pricing Calculation"
        )
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Price calculation API error for device {device_id}: {str(e)}", "POS Pricing API")
        return {
            "status": "error",
            "message": _("Internal server error during price calculation"),
            "authenticated": False if "Invalid device credentials" not in str(e) else True
        }


@frappe.whitelist()
def get_pricing_rules(device_id, api_key, item_code=None, branch_id=None, customer=None):
    """
    Retrieve applicable pricing rules for given context
    
    Args:
        device_id (str): POS device identifier
        api_key (str): Device API key for authentication
        item_code (str): Item code to get rules for (optional)
        branch_id (str): Branch ID (optional)
        customer (str): Customer ID (optional)
    
    Returns:
        dict: List of applicable pricing rules
    """
    
    try:
        # Input validation
        if not all([device_id, api_key]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key"),
                "authenticated": False
            }
        
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {
                "status": "error",
                "message": _("Invalid device credentials"),
                "authenticated": False
            }
        
        # Get device context
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            return {
                "status": "error",
                "message": _("Device not found"),
                "authenticated": True
            }
        
        # Use branch from device if not provided
        if not branch_id and device.branch:
            branch_id = device.branch
        
        # Get pricing rules using the existing function
        from erpnext_pos_integration.doctype.pos_pricing_rule.pos_pricing_rule import get_applicable_pricing_rules
        
        rules = get_applicable_pricing_rules(
            item_code=item_code,
            branch_id=branch_id,
            customer=customer,
            quantity=1,  # Default quantity
            total_amount=0  # Default total
        )
        
        # Format rules for response
        formatted_rules = []
        for rule in rules:
            formatted_rules.append({
                "name": rule.name,
                "rule_name": rule.rule_name,
                "pricing_type": rule.pricing_type,
                "priority_level": rule.priority_level,
                "erpnext_priority": rule.erpnext_priority,
                "is_active": rule.is_active,
                "valid_from": rule.valid_from,
                "valid_upto": rule.valid_upto,
                "item_code": rule.item_code,
                "item_group": rule.item_group,
                "brand": rule.brand,
                "customer": rule.customer,
                "customer_group": rule.customer_group,
                "territory": rule.territory,
                "base_price": rule.base_price,
                "discount_percentage": rule.discount_percentage,
                "discount_amount": rule.discount_amount,
                "min_quantity": rule.min_quantity,
                "max_quantity": rule.max_quantity,
                "min_spend_amount": rule.min_spend_amount,
                "bxgy_buy_qty": rule.bxgy_buy_qty,
                "bxgy_get_qty": rule.bxgy_get_qty
            })
        
        return {
            "status": "success",
            "authenticated": True,
            "device_id": device_id,
            "device_name": device.device_name,
            "branch_id": branch_id,
            "item_code": item_code,
            "customer": customer,
            "rules_count": len(formatted_rules),
            "rules": formatted_rules,
            "timestamp": now()
        }
        
    except Exception as e:
        frappe.log_error(f"Get pricing rules API error for device {device_id}: {str(e)}", "POS Pricing Rules API")
        return {
            "status": "error",
            "message": _("Internal server error while fetching pricing rules"),
            "authenticated": False if "Invalid device credentials" not in str(e) else True
        }


@frappe.whitelist()
def validate_pricing(device_id, api_key):
    """
    Validate pricing engine configuration and device context
    
    Args:
        device_id (str): POS device identifier
        api_key (str): Device API key for authentication
    
    Returns:
        dict: Validation status and configuration info
    """
    
    try:
        # Input validation
        if not all([device_id, api_key]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key"),
                "authenticated": False
            }
        
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {
                "status": "error",
                "message": _("Invalid device credentials"),
                "authenticated": False
            }
        
        # Get device context
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            return {
                "status": "error",
                "message": _("Device not found"),
                "authenticated": True
            }
        
        # Validate pricing engine configuration
        pricing_engine = PricingEngine()
        engine_status = pricing_engine.validate_pricing_configuration()
        
        # Test price calculation with sample data
        test_result = None
        if engine_status['status'] != 'error':
            try:
                test_result = pricing_engine.calculate_price(
                    item_code="TEST-ITEM",
                    base_price=100.0,
                    quantity=1,
                    total_amount=100.0,
                    customer=None,
                    branch_id=device.branch
                )
            except Exception as test_error:
                test_result = {"error": str(test_error)}
        
        # Build comprehensive validation response
        validation_status = {
            "status": "success",
            "authenticated": True,
            "device_id": device_id,
            "device_name": device.device_name,
            "device_status": "active" if device.is_registered else "inactive",
            "branch_id": device.branch,
            "pricing_engine": {
                "status": engine_status['status'],
                "issues": engine_status.get('issues', []),
                "statistics": engine_status.get('statistics', {}),
                "test_calculation": test_result
            },
            "timestamp": now()
        }
        
        # Add overall health status
        if engine_status['status'] == 'success' and test_result and 'error' not in test_result:
            validation_status["overall_status"] = "healthy"
        elif engine_status.get('issues'):
            validation_status["overall_status"] = "configuration_issues"
        else:
            validation_status["overall_status"] = "degraded"
        
        return validation_status
        
    except Exception as e:
        frappe.log_error(f"Pricing validation API error for device {device_id}: {str(e)}", "POS Pricing Validation API")
        return {
            "status": "error",
            "message": _("Internal server error during pricing validation"),
            "authenticated": False if "Invalid device credentials" not in str(e) else True
        }


@frappe.whitelist()
def calculate_bulk_prices(device_id, api_key, items_data, customer=None, branch_id=None):
    """
    Calculate prices for multiple items efficiently
    
    Args:
        device_id (str): POS device identifier
        api_key (str): Device API key for authentication
        items_data (str/list): Items data as JSON string or list
        customer (str): Customer ID (optional)
        branch_id (str): Branch ID (optional)
    
    Returns:
        dict: Bulk pricing calculation results
    """
    
    try:
        # Input validation
        if not all([device_id, api_key, items_data]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key, items_data"),
                "authenticated": False
            }
        
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {
                "status": "error",
                "message": _("Invalid device credentials"),
                "authenticated": False
            }
        
        # Parse items_data
        if isinstance(items_data, str):
            try:
                items_data = json.loads(items_data)
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": _("Invalid items_data JSON format"),
                    "authenticated": True
                }
        
        if not isinstance(items_data, list):
            return {
                "status": "error",
                "message": _("items_data must be a list"),
                "authenticated": True
            }
        
        # Validate items_data structure
        if len(items_data) == 0:
            return {
                "status": "error",
                "message": _("items_data cannot be empty"),
                "authenticated": True
            }
        
        if len(items_data) > 50:  # Limit to prevent performance issues
            return {
                "status": "error",
                "message": _("Too many items. Maximum 50 items allowed per request"),
                "authenticated": True
            }
        
        # Validate each item in the list
        for i, item in enumerate(items_data):
            if not isinstance(item, dict):
                return {
                    "status": "error",
                    "message": f"Item {i+1} must be a dictionary",
                    "authenticated": True
                }
            
            if 'item_code' not in item or 'base_price' not in item:
                return {
                    "status": "error",
                    "message": f"Item {i+1} must contain 'item_code' and 'base_price'",
                    "authenticated": True
                }
            
            # Convert numeric fields
            try:
                item['base_price'] = flt(item['base_price'])
                item['quantity'] = flt(item.get('quantity', 1))
            except (ValueError, TypeError):
                return {
                    "status": "error",
                    "message": f"Invalid numeric values in item {i+1}",
                    "authenticated": True
                }
        
        # Get device context
        device = frappe.get_doc("POS Device", {"device_id": device_id})
        if not device:
            return {
                "status": "error",
                "message": _("Device not found"),
                "authenticated": True
            }
        
        # Use branch from device if not provided
        if not branch_id and device.branch:
            branch_id = device.branch
        
        # Calculate bulk prices
        pricing_engine = PricingEngine()
        bulk_results = pricing_engine.calculate_bulk_prices(
            items_data=items_data,
            customer=customer,
            branch_id=branch_id,
            device_id=device_id
        )
        
        # Build response
        response = {
            "status": "success",
            "authenticated": True,
            "device_id": device_id,
            "device_name": device.device_name,
            "branch_id": branch_id,
            "customer": customer,
            "items_processed": len(items_data),
            "bulk_calculation": bulk_results,
            "timestamp": now()
        }
        
        # Add performance warnings
        calculation_time = bulk_results.get('calculation_time', 0)
        if calculation_time > 1.0:  # Log if > 1 second
            response["performance_warning"] = "Bulk price calculation slower than expected"
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Bulk pricing API error for device {device_id}: {str(e)}", "POS Bulk Pricing API")
        return {
            "status": "error",
            "message": _("Internal server error during bulk price calculation"),
            "authenticated": False if "Invalid device credentials" not in str(e) else True
        }


@frappe.whitelist()
def clear_pricing_cache(device_id, api_key):
    """
    Clear pricing engine cache for device
    
    Args:
        device_id (str): POS device identifier
        api_key (str): Device API key for authentication
    
    Returns:
        dict: Cache clear result
    """
    
    try:
        # Input validation
        if not all([device_id, api_key]):
            return {
                "status": "error",
                "message": _("Missing required parameters: device_id, api_key"),
                "authenticated": False
            }
        
        # Validate device credentials
        if not validate_device_credentials(device_id, api_key):
            return {
                "status": "error",
                "message": _("Invalid device credentials"),
                "authenticated": False
            }
        
        # Clear pricing cache using the utility function
        from erpnext_pos_integration.utils.pricing_engine import clear_pricing_cache as clear_cache
        cache_result = clear_cache()
        
        return {
            "status": "success",
            "authenticated": True,
            "device_id": device_id,
            "cache_clear_result": cache_result,
            "timestamp": now()
        }
        
    except Exception as e:
        frappe.log_error(f"Clear cache API error for device {device_id}: {str(e)}", "POS Cache Clear API")
        return {
            "status": "error",
            "message": _("Internal server error during cache clear"),
            "authenticated": False if "Invalid device credentials" not in str(e) else True
        }