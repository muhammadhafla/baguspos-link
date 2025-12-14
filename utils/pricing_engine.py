# Copyright (c) 2025, ERPNext and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, add_hours, getdate, flt, cint
from datetime import datetime, timedelta
import json
import time
import threading
from functools import lru_cache

class PricingEngine:
    """
    Core 8-level pricing engine for ERPNext POS Integration
    
    Implements the 8-level hierarchy:
    Level 8: Manual Override (Priority 13) - Highest Priority
    Level 7: BXGY (Priority 14)
    Level 6: Spend X Discount (Priority 15)
    Level 5: Quantity Break Discount (Priority 16)
    Level 4: Time-based Promotion (Priority 17)
    Level 3: Member/Customer Price (Priority 18)
    Level 2: Branch Price Override (Priority 19)
    Level 1: Base Item Price (Priority 20) - Lowest Priority
    """
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes cache TTL
        self._cache_lock = threading.Lock()
        
    @lru_cache(maxsize=1000)
    def get_cached_pricing_rules(self, cache_key):
        """Get pricing rules from cache"""
        with self._cache_lock:
            try:
                cache_entry = frappe.cache().get(cache_key)
                if cache_entry:
                    cache_data = json.loads(cache_entry)
                    if datetime.now() < datetime.fromisoformat(cache_data['expires_at']):
                        return cache_data['rules']
            except:
                pass
        return None
    
    def set_cached_pricing_rules(self, cache_key, rules, ttl=None):
        """Set pricing rules in cache"""
        if ttl is None:
            ttl = self.cache_ttl
            
        with self._cache_lock:
            try:
                expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
                cache_data = {
                    'rules': rules,
                    'expires_at': expires_at,
                    'created_at': datetime.now().isoformat()
                }
                frappe.cache().set(cache_key, json.dumps(cache_data))
            except Exception as e:
                frappe.log_error(f"Cache write error: {str(e)}", "Pricing Engine Cache")
    
    def calculate_price(self, item_code, base_price, quantity=1, total_amount=0, 
                       customer=None, branch_id=None, device_id=None, **kwargs):
        """
        Calculate final price using 8-level hierarchy pricing engine
        
        Args:
            item_code (str): Item code to calculate price for
            base_price (float): Base item price
            quantity (int): Quantity being purchased
            total_amount (float): Total transaction amount
            customer (str): Customer ID (optional)
            branch_id (str): Branch ID (optional)
            device_id (str): Device ID for context (optional)
            **kwargs: Additional context parameters
        
        Returns:
            dict: Complete pricing breakdown with rule applied
        """
        start_time = time.time()
        
        try:
            # Generate cache key based on context
            cache_key = self._generate_cache_key(item_code, quantity, total_amount, 
                                               customer, branch_id, **kwargs)
            
            # Get applicable pricing rules with caching
            applicable_rules = self.get_applicable_pricing_rules(
                item_code, quantity, total_amount, customer, branch_id, cache_key
            )
            
            if not applicable_rules:
                return self._build_price_response(
                    base_price, base_price, 0, 0, None, "No pricing rules applicable"
                )
            
            # Apply highest priority rule
            best_rule = self._get_highest_priority_rule(applicable_rules)
            price_result = self._apply_pricing_rule(
                best_rule, base_price, quantity, total_amount, **kwargs
            )
            
            # Log performance if slow
            execution_time = time.time() - start_time
            if execution_time > 0.5:  # Log if > 500ms
                frappe.log_error(
                    f"Price calculation slow: {execution_time:.2f}s for item {item_code}",
                    "Pricing Engine Performance"
                )
            
            return price_result
            
        except Exception as e:
            frappe.log_error(f"Price calculation error for {item_code}: {str(e)}", "Pricing Engine Error")
            return self._build_price_response(
                base_price, base_price, 0, 0, None, f"Calculation error: {str(e)}"
            )
    
    def calculate_bulk_prices(self, items_data, customer=None, branch_id=None, device_id=None):
        """
        Calculate prices for multiple items efficiently
        
        Args:
            items_data (list): List of dicts with item_code, quantity, base_price
            customer (str): Customer ID (optional)
            branch_id (str): Branch ID (optional)
            device_id (str): Device ID (optional)
        
        Returns:
            dict: Bulk calculation results with item-by-item breakdown
        """
        start_time = time.time()
        results = {
            'items': [],
            'total_original': 0,
            'total_final': 0,
            'total_discount': 0,
            'calculation_time': 0,
            'rules_applied': set()
        }
        
        total_transaction_amount = sum(
            item.get('base_price', 0) * item.get('quantity', 1) 
            for item in items_data
        )
        
        try:
            for item_data in items_data:
                item_result = self.calculate_price(
                    item_code=item_data['item_code'],
                    base_price=item_data['base_price'],
                    quantity=item_data.get('quantity', 1),
                    total_amount=total_transaction_amount,
                    customer=customer,
                    branch_id=branch_id,
                    device_id=device_id
                )
                
                results['items'].append({
                    'item_code': item_data['item_code'],
                    'quantity': item_data.get('quantity', 1),
                    **item_result
                })
                
                results['total_original'] += item_result['original_price']
                results['total_final'] += item_result['final_price']
                results['total_discount'] += item_result['discount_amount']
                if item_result.get('rule_applied'):
                    results['rules_applied'].add(item_result['rule_applied'])
            
            results['calculation_time'] = time.time() - start_time
            results['rules_applied'] = list(results['rules_applied'])
            
            return results
            
        except Exception as e:
            frappe.log_error(f"Bulk pricing calculation error: {str(e)}", "Pricing Engine Error")
            return {
                'items': [],
                'total_original': 0,
                'total_final': 0,
                'total_discount': 0,
                'calculation_time': time.time() - start_time,
                'error': str(e)
            }
    
    def get_applicable_pricing_rules(self, item_code, quantity, total_amount, 
                                   customer, branch_id, cache_key=None):
        """
        Get all applicable pricing rules for given context with caching
        """
        # Try to get from cache first
        if cache_key:
            cached_rules = self.get_cached_pricing_rules(cache_key)
            if cached_rules:
                return self._convert_to_doc_objects(cached_rules)
        
        # Build query filters for performance
    
    def _apply_pricing_rule(self, rule, base_price, quantity, total_amount, **kwargs):
        """Apply specific pricing rule and calculate final price"""
        if not rule:
            return self._build_price_response(base_price, base_price, 0, 0, None)
        
        try:
            # Use the existing calculate_price method from POS Pricing Rule
            price_breakdown = rule.calculate_price(base_price, quantity, total_amount)
            
            # Add additional metadata
            price_breakdown.update({
                'rule_level': rule.priority_level,
                'pricing_type': rule.pricing_type,
                'rule_name': rule.rule_name,
                'rule_id': rule.name
            })
            
            return self._build_price_response(
                price_breakdown['original_price'],
                price_breakdown['final_price'],
                price_breakdown['discount_amount'],
                price_breakdown['discount_percentage'],
                rule.name,
                rule.rule_name,
                rule.pricing_type,
                rule.priority_level,
                price_breakdown
            )
            
        except Exception as e:
            frappe.log_error(f"Error applying pricing rule {rule.name}: {str(e)}", "Pricing Engine")
            return self._build_price_response(base_price, base_price, 0, 0, rule.name, 
                                           f"Rule application error: {str(e)}")
    
    def _build_price_response(self, original_price, final_price, discount_amount, 
                            discount_percentage, rule_applied, rule_name=None, 
                            pricing_type=None, priority_level=None, extra_data=None):
        """Build standardized price response"""
        response = {
            'original_price': flt(original_price),
            'final_price': flt(final_price),
            'discount_amount': flt(discount_amount),
            'discount_percentage': flt(discount_percentage),
            'rule_applied': rule_applied,
            'timestamp': now()
        }
        
        if rule_name:
            response['rule_name'] = rule_name
        if pricing_type:
            response['pricing_type'] = pricing_type
        if priority_level:
            response['priority_level'] = cint(priority_level)
        
        if extra_data:
            response.update(extra_data)
        
        return response
    
    def _generate_cache_key(self, item_code, quantity, total_amount, customer, branch_id, **kwargs):
        """Generate cache key for pricing context"""
        key_parts = [
            'pricing',
            item_code,
            quantity,
            total_amount,
            customer or 'none',
            branch_id or 'none'
        ]
        
        # Add additional context parameters
        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")
        
        return '|'.join(map(str, key_parts))
    
    def _get_item_info(self, item_code):
        """Get item information for context"""
        if not item_code:
            return {}
        
        try:
            return frappe.get_value(
                'Item',
                item_code,
                ['item_group', 'brand', 'stock_uom', 'item_name'],
                as_dict=True
            ) or {}
        except:
            return {}
    
    def _convert_to_doc_objects(self, rules_data):
        """Convert cached rule data back to doc objects"""
        try:
            return [frappe.get_doc('POS Pricing Rule', rule['name']) for rule in rules_data]
        except:
            return []
    
    def validate_pricing_configuration(self):
        """
        Validate pricing engine configuration and return status
        """
        issues = []
        
        try:
            # Check if POS Pricing Rule doctype exists
            if not frappe.db.exists('DocType', 'POS Pricing Rule'):
                issues.append("POS Pricing Rule DocType not found")
            
            # Check for active pricing rules
            active_rules_count = frappe.db.count('POS Pricing Rule', {'is_active': 1})
            if active_rules_count == 0:
                issues.append("No active pricing rules found")
            
            # Check for priority level distribution
            priority_distribution = frappe.db.sql("""
                SELECT priority_level, COUNT(*) as count
                FROM `tabPOS Pricing Rule`
                WHERE is_active = 1
                GROUP BY priority_level
                ORDER BY priority_level
            """)
            
            if not priority_distribution:
                issues.append("No pricing rules with priority levels found")
            
            # Check for branch configuration
            if frappe.db.exists('DocType', 'Branch'):
                branch_count = frappe.db.count('Branch', {'is_group': 0})
                if branch_count == 0:
                    issues.append("No branch configuration found")
            
            return {
                'status': 'error' if issues else 'success',
                'issues': issues,
                'statistics': {
                    'active_rules': active_rules_count,
                    'priority_distribution': dict(priority_distribution),
                    'branches': branch_count if 'branch_count' in locals() else 0
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'issues': [f"Configuration validation error: {str(e)}"]
            }

# Utility functions for easy access
@frappe.whitelist()
def calculate_item_price(item_code, base_price, quantity=1, total_amount=0, 
                        customer=None, branch_id=None, device_id=None):
    """
    Calculate price for a single item using pricing engine
    """
    engine = PricingEngine()
    return engine.calculate_price(
        item_code=item_code,
        base_price=base_price,
        quantity=quantity,
        total_amount=total_amount,
        customer=customer,
        branch_id=branch_id,
        device_id=device_id
    )

@frappe.whitelist()
def calculate_bulk_item_prices(items_data, customer=None, branch_id=None, device_id=None):
    """
    Calculate prices for multiple items
    """
    engine = PricingEngine()
    
    # Parse items_data if it's a string
    if isinstance(items_data, str):
        try:
            items_data = json.loads(items_data)
        except:
            frappe.throw(_("Invalid items data format"))
    
    if not isinstance(items_data, list):
        frappe.throw(_("Items data must be a list"))
    
    return engine.calculate_bulk_prices(
        items_data=items_data,
        customer=customer,
        branch_id=branch_id,
        device_id=device_id
    )

@frappe.whitelist()
def get_pricing_engine_status():
    """
    Get pricing engine health and configuration status
    """
    engine = PricingEngine()
    return engine.validate_pricing_configuration()

@frappe.whitelist()
def clear_pricing_cache():
    """
    Clear pricing engine cache
    """
    try:
        cache = frappe.cache()
        keys = cache.get_keys('pricing|')
        for key in keys:
            cache.delete(key)
        
        return {
            'status': 'success',
            'message': f"Cleared {len(keys)} cache entries"
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Cache clear error: {str(e)}"
        }
        filters = {
            'is_active': 1,
            'item_code': ['in', [item_code, '']],  # Include rules with no specific item
        }
        
        # Add item group and brand filters if needed
        item_info = self._get_item_info(item_code)
        if item_info:
            if item_info.get('item_group'):
                filters['item_group'] = ['in', [item_info['item_group'], '']]
            if item_info.get('brand'):
                filters['brand'] = ['in', [item_info['brand'], '']]
        
        # Get pricing rules ordered by priority (highest first)
        rules = frappe.get_all(
            'POS Pricing Rule',
            filters=filters,
            fields=['*'],
            order_by='erpnext_priority desc, modified desc',
            limit=50  # Limit to prevent performance issues
        )
        
        applicable_rules = []
        transaction_context = {
            'item_code': item_code,
            'branch_id': branch_id,
            'customer': customer,
            'quantity': quantity,
            'total_amount': total_amount,
            'item_info': item_info,
            'current_time': now(),
            'current_date': getdate()
        }
        
        for rule_data in rules:
            try:
                rule_doc = frappe.get_doc('POS Pricing Rule', rule_data.name)
                if rule_doc.is_applicable(transaction_context):
                    applicable_rules.append(rule_doc)
                    # Cache the applicable rules
                    if cache_key and len(applicable_rules) <= 10:  # Cache only if not too many
                        cache_data = [rule_doc.as_dict() for rule_doc in applicable_rules]
                        self.set_cached_pricing_rules(cache_key, cache_data)
            except Exception as e:
                frappe.log_error(f"Error processing rule {rule_data.name}: {str(e)}", "Pricing Engine")
                continue
        
        return applicable_rules
    
    def _get_highest_priority_rule(self, applicable_rules):
        """Get the highest priority rule from applicable rules"""
        if not applicable_rules:
            return None
        
        # Rules are already ordered by priority desc, so first is highest
        return applicable_rules[0]