# ERPNext POS Integration - Configuration Guide

This comprehensive guide covers all configuration options available in the ERPNext POS Integration Bridge App, from basic setup to advanced customization.

## 📋 Table of Contents

- [Environment Configuration](#environment-configuration)
- [Database Configuration](#database-configuration)
- [Pricing Engine Configuration](#pricing-engine-configuration)
- [Device Configuration](#device-configuration)
- [Custom Fields Configuration](#custom-fields-configuration)
- [Integration Settings](#integration-settings)
- [Performance Tuning](#performance-tuning)
- [Security Configuration](#security-configuration)
- [Logging Configuration](#logging-configuration)
- [Environment Variables](#environment-variables)

---

## 🌐 Environment Configuration

### Basic ERPNext Setup

Ensure your ERPNext instance meets the minimum requirements:

```json
{
    "erpnext_version": ">=14.0.0",
    "frappe_version": ">=14.0.0",
    "python_version": ">=3.8",
    "database_version": ">=10.3"
}
```

### Site Configuration (`site_config.json`)

Add POS integration settings to your ERPNext site configuration:

```json
{
    "db_name": "your_site_name",
    "db_password": "your_db_password",
    "pos_integration_settings": {
        "enable_pos_integration": 1,
        "pos_cache_timeout": 3600,
        "pos_bulk_limit": 50,
        "pos_heartbeat_interval": 300,
        "pos_sync_batch_size": 100,
        "pos_enable_caching": 1,
        "pos_cache_size_limit": "50MB",
        "pos_performance_monitoring": 1,
        "pos_debug_mode": 0
    },
    "redis_cache": {
        "redis_cache_timeout": 3600
    }
}
```

### Installation Verification

Verify the installation by checking the installed apps:

```bash
bench --site your-site-name list-apps
```

Should display: `erpnext_pos_integration`

---

## 🗄️ Database Configuration

### Custom Fields Integration

The application adds custom fields to standard ERPNext DocTypes. These are automatically created during installation.

#### Sales Invoice Fields

| Field Name | Type | Purpose |
|------------|------|---------|
| `pos_branch_id` | Data | Original POS branch identifier |
| `pos_device_id` | Data | Source POS device identifier |
| `pos_transaction_id` | Data | Unique POS transaction identifier |
| `pos_receipt_number` | Data | POS-generated receipt number |
| `pos_sync_status` | Select | Sync status (Pending, Synced, Failed, Manual Review) |
| `pos_sync_attempts` | Int | Number of sync attempts |
| `pos_last_sync_attempt` | Datetime | Last sync attempt timestamp |

#### Item Fields

| Field Name | Type | Purpose |
|------------|------|---------|
| `is_pos_item` | Check | Item available for POS transactions (default: 1) |
| `pos_display_order` | Int | Order for display in POS interface |
| `pos_category` | Link | Item group for POS categorization |

#### POS Pricing Rule Fields

| Field Name | Type | Purpose |
|------------|------|---------|
| `erpnext_priority` | Int | Priority mapped to ERPNext pricing rule system (hidden) |

### Database Indexes

For optimal performance, ensure these indexes exist:

```sql
-- POS Device indexes
CREATE INDEX idx_pos_device_branch ON `tabPOS Device`(branch);
CREATE INDEX idx_pos_device_status ON `tabPOS Device`(sync_status);
CREATE INDEX idx_pos_device_heartbeat ON `tabPOS Device`(last_heartbeat);

-- Pricing Rule indexes
CREATE INDEX idx_pricing_rule_priority ON `tabPOS Pricing Rule`(priority_level, erpnext_priority);
CREATE INDEX idx_pricing_rule_active ON `tabPOS Pricing Rule`(is_active, valid_from, valid_upto);
CREATE INDEX idx_pricing_rule_item ON `tabPOS Pricing Rule`(item_code, item_group, brand);

-- Sync Log indexes
CREATE INDEX idx_sync_log_device ON `tabPOS Sync Log`(device_id, creation);
CREATE INDEX idx_sync_log_status ON `tabPOS Sync Log`(sync_status, creation);

-- Sales Invoice indexes (for custom fields)
CREATE INDEX idx_sales_invoice_pos_branch ON `tabSales Invoice`(pos_branch_id);
CREATE INDEX idx_sales_invoice_pos_device ON `tabSales Invoice`(pos_device_id);
CREATE INDEX idx_sales_invoice_pos_status ON `tabSales Invoice`(pos_sync_status);
```

### Database Migration

If you need to manually apply database changes:

```python
# In your custom app or via bench console
import frappe
from erpnext_pos_integration.install.after_install import create_custom_fields

# Apply custom fields
create_custom_fields()

# Refresh DocTypes
frappe.reload_doctype("Sales Invoice")
frappe.reload_doctype("Item")
frappe.reload_doctype("POS Pricing Rule")

frappe.db.commit()
```

---

## ⚙️ Pricing Engine Configuration

### Core Configuration

The pricing engine is configured in `utils/pricing_engine.py`. Key settings:

```python
class PricingEngine:
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes cache TTL
        self._cache_lock = threading.Lock()
        self.max_cache_size = 1000  # Maximum cached items
        self.bulk_calculation_limit = 50  # Maximum items per bulk request
```

### Pricing Rule Priority Levels

The 8-level pricing hierarchy uses the following priority mapping:

| Level | Priority | Description |
|-------|----------|-------------|
| Level 8 | 13 | Manual Override (Highest) |
| Level 7 | 14 | BXGY (Buy X Get Y) |
| Level 6 | 15 | Spend X Discount |
| Level 5 | 16 | Quantity Break Discount |
| Level 4 | 17 | Time-based Promotion |
| Level 3 | 18 | Member/Customer Price |
| Level 2 | 19 | Branch Price Override |
| Level 1 | 20 | Base Item Price (Lowest) |

### Caching Configuration

#### Cache Settings

```python
# Cache configuration in pricing engine
CACHE_SETTINGS = {
    'default_ttl': 300,  # 5 minutes
    'max_size': 1000,    # Maximum cache entries
    'cleanup_interval': 3600,  # Cleanup every hour
    'enable_compression': True
}
```

#### Cache Key Structure

Cache keys follow this format:
```
pricing|{item_code}|{quantity}|{total_amount}|{customer}|{branch_id}|{additional_params}
```

Example:
```
pricing|ITEM-001|2|200.00|CUST-001|MAIN-BRANCH-001|category:electronics
```

### Performance Tuning

#### Calculation Timeouts

```python
# In utils/pricing_engine.py
PERFORMANCE_THRESHOLDS = {
    'single_calculation_warning': 0.5,  # 500ms
    'bulk_calculation_warning': 1.0,    # 1 second
    'cache_lookup_timeout': 0.1,        # 100ms
    'rule_evaluation_timeout': 0.2      # 200ms
}
```

#### Optimization Settings

```python
# For high-volume environments
HIGH_VOLUME_SETTINGS = {
    'cache_ttl': 600,           # 10 minutes
    'preload_rules': True,      # Preload frequently used rules
    'rule_pagination': 50,      # Process rules in batches
    'async_calculation': True   # Enable async for bulk operations
}
```

---

## 📱 Device Configuration

### Device Registration

Devices are registered through the API with the following configuration:

#### Registration Parameters

```json
{
    "branch": "MAIN-BRANCH-001",
    "device_name": "POS-001-Front-Counter",
    "registration_code": "REG-CODE-12345",
    "device_type": "Tablet",
    "os_version": "Android 11",
    "app_version": "1.0.0"
}
```

#### Device Types Supported

- **Tablet**: Touch-based POS devices
- **Desktop**: Traditional desktop POS
- **Mobile**: Smartphone-based POS
- **Kiosk**: Self-service kiosks

### Device Authentication

#### API Credentials Structure

```json
{
    "device_id": "POS-001-001",
    "api_key": "sk_live_abc123def456",
    "api_secret": "sk_secret_xyz789"
}
```

#### Authentication Flow

1. Device registers with branch and registration code
2. System validates registration code and branch
3. Generates unique device credentials
4. Device uses API key/secret for subsequent requests

### Device Status Monitoring

#### Status Types

- **Online**: Device is active and responding
- **Offline**: Device is not responding to heartbeats
- **Syncing**: Device is synchronizing data
- **Error**: Device has errors requiring attention

#### Heartbeat Configuration

```python
# Default heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 300  # 5 minutes

# Health check timeout (seconds)
HEALTH_CHECK_TIMEOUT = 30

# Offline threshold (minutes)
OFFLINE_THRESHOLD = 15
```

---

## 🔧 Custom Fields Configuration

### Field Definitions

Custom fields are defined in `fixtures/custom_field.json` and applied during installation.

#### Field Types and Validation

```python
# Custom field validation examples
CUSTOM_FIELD_VALIDATIONS = {
    'pos_transaction_id': {
        'unique': True,
        'required': False,
        'max_length': 100
    },
    'pos_sync_status': {
        'options': ['Pending', 'Synced', 'Failed', 'Manual Review'],
        'default': 'Pending'
    },
    'is_pos_item': {
        'default': 1,
        'description': 'Item available for POS transactions'
    }
}
```

### Custom Field Management

#### Adding New Custom Fields

```python
# Add custom field via code
def add_custom_field(doctype, fieldname, fieldtype, label, **kwargs):
    custom_field = frappe.get_doc({
        'doctype': 'Custom Field',
        'dt': doctype,
        'fieldname': fieldname,
        'fieldtype': fieldtype,
        'label': label,
        **kwargs
    })
    custom_field.insert()
    return custom_field

# Example usage
add_custom_field(
    doctype='Sales Invoice',
    fieldname='pos_custom_field',
    fieldtype='Data',
    label='POS Custom Field',
    description='Custom field for POS integration'
)
```

#### Removing Custom Fields

```python
# Remove custom field
def remove_custom_field(doctype, fieldname):
    custom_field = frappe.db.exists('Custom Field', {
        'dt': doctype,
        'fieldname': fieldname
    })
    if custom_field:
        frappe.delete_doc('Custom Field', custom_field)
        frappe.db.commit()
```

---

## 🔗 Integration Settings

### ERPNext Integration Points

#### DocType Integration

| DocType | Integration Type | Purpose |
|---------|------------------|---------|
| Sales Invoice | Custom Fields | POS transaction storage |
| Item | Custom Fields | POS item configuration |
| Branch | Native | Branch management |
| Company | Native | Company settings |
| Customer | Custom Fields | Customer pricing |

#### API Integration

```python
# ERPNext API endpoints used
INTEGRATION_ENDPOINTS = {
    'item_master': '/api/resource/Item',
    'customer_master': '/api/resource/Customer',
    'pricing_rule': '/api/resource/Pricing Rule',
    'sales_invoice': '/api/resource/Sales Invoice',
    'branch_master': '/api/resource/Branch'
}
```

### Third-Party Integrations

#### POS System Integration

```python
# POS system integration settings
POS_INTEGRATION_CONFIG = {
    'supported_protocols': ['REST', 'WebSocket', 'MQTT'],
    'authentication_methods': ['API_KEY', 'JWT', 'OAuth2'],
    'data_formats': ['JSON', 'XML'],
    'sync_modes': ['REAL_TIME', 'BATCH', 'HYBRID']
}
```

---

## ⚡ Performance Tuning

### Database Performance

#### Query Optimization

```sql
-- Optimize pricing rule queries
EXPLAIN SELECT * FROM `tabPOS Pricing Rule` 
WHERE is_active = 1 
AND (item_code = 'ITEM-001' OR item_code = '')
ORDER BY erpnext_priority DESC, modified DESC 
LIMIT 10;

-- Optimize device queries
EXPLAIN SELECT * FROM `tabPOS Device` 
WHERE branch = 'MAIN-BRANCH-001' 
AND sync_status = 'Online';
```

#### Connection Pooling

```python
# Database connection settings
DB_CONFIG = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

### Cache Performance

#### Redis Configuration

```python
# Redis cache settings for production
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
    'socket_timeout': 5,
    'connection_pool_kwargs': {
        'max_connections': 50,
        'retry_on_timeout': True
    }
}
```

#### Cache Monitoring

```python
# Cache performance monitoring
CACHE_MONITORING = {
    'enable_metrics': True,
    'metrics_interval': 60,  # seconds
    'alert_thresholds': {
        'hit_rate_warning': 70,  # %
        'memory_usage_warning': 80,  # %
        'eviction_rate_warning': 10  # %
    }
}
```

### API Performance

#### Rate Limiting

```python
# Rate limiting configuration
RATE_LIMITS = {
    'device_registration': '5/minute',
    'price_calculation': '100/minute',
    'health_check': '60/minute',
    'bulk_operation': '10/minute',
    'system_overview': '10/minute'
}
```

#### Response Caching

```python
# API response caching
RESPONSE_CACHE = {
    'health_check': 30,      # seconds
    'pricing_rules': 300,    # 5 minutes
    'device_status': 60,     # 1 minute
    'system_overview': 300   # 5 minutes
}
```

---

## 🔒 Security Configuration

### API Security

#### Authentication Configuration

```python
# API security settings
API_SECURITY = {
    'require_https': True,
    'token_expiry': 3600,        # 1 hour
    'max_login_attempts': 5,
    'lockout_duration': 900,     # 15 minutes
    'api_key_length': 32,
    'api_secret_length': 64
}
```

#### Request Validation

```python
# Request validation settings
REQUEST_VALIDATION = {
    'max_request_size': '10MB',
    'allowed_content_types': ['application/json'],
    'require_user_agent': True,
    'allowed_methods': ['POST'],
    'enable_cors': False
}
```

### Data Security

#### Field-Level Security

```python
# Sensitive field protection
SENSITIVE_FIELDS = {
    'POS Device': ['api_key', 'api_secret', 'device_fingerprint'],
    'Sales Invoice': ['pos_transaction_id'],
    'Customer': ['credit_limit', 'payment_terms']
}
```

#### Encryption Settings

```python
# Data encryption configuration
ENCRYPTION = {
    'api_credentials_encrypted': True,
    'transaction_data_encrypted': True,
    'encryption_algorithm': 'AES-256',
    'key_rotation_interval': 86400  # 24 hours
}
```

---

## 📊 Logging Configuration

### Log Levels

```python
# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(funcName)s() %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/erpnext_pos_integration.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error': {
            'level': 'ERROR',
            'formatter': 'detailed',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'error'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

### Log Categories

```python
# Log categories and levels
LOG_CATEGORIES = {
    'device_registration': 'INFO',
    'pricing_calculation': 'DEBUG',
    'sync_operations': 'INFO',
    'api_requests': 'DEBUG',
    'errors': 'ERROR',
    'performance': 'WARNING',
    'security': 'WARNING'
}
```

### Log Rotation

```python
# Log rotation settings
LOG_ROTATION = {
    'max_file_size': '10MB',
    'backup_count': 5,
    'compression': True,
    'retention_days': 30
}
```

---

## 🌍 Environment Variables

### Core Configuration

```bash
# ERPNext POS Integration Environment Variables

# Basic Settings
export POS_ENABLE_INTEGRATION=1
export POS_CACHE_TIMEOUT=3600
export POS_BULK_LIMIT=50
export POS_HEARTBEAT_INTERVAL=300
export POS_SYNC_BATCH_SIZE=100

# Performance Settings
export POS_ENABLE_CACHING=1
export POS_CACHE_SIZE_LIMIT=50MB
export POS_PERFORMANCE_MONITORING=1
export POS_DEBUG_MODE=0

# Security Settings
export POS_REQUIRE_HTTPS=1
export POS_TOKEN_EXPIRY=3600
export POS_MAX_LOGIN_ATTEMPTS=5
export POS_LOCKOUT_DURATION=900

# Database Settings
export POS_DB_POOL_SIZE=20
export POS_DB_MAX_OVERFLOW=30
export POS_DB_POOL_TIMEOUT=30

# Redis Settings
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=
export REDIS_SOCKET_TIMEOUT=5

# Logging Settings
export POS_LOG_LEVEL=INFO
export POS_LOG_MAX_SIZE=10MB
export POS_LOG_BACKUP_COUNT=5
export POS_LOG_RETENTION_DAYS=30

# Rate Limiting
export POS_RATE_LIMIT_DEVICE_REG=5/minute
export POS_RATE_LIMIT_PRICING=100/minute
export POS_RATE_LIMIT_HEALTH=60/minute
export POS_RATE_LIMIT_BULK=10/minute

# Advanced Settings
export POS_ENABLE_METRICS=1
export POS_METRICS_INTERVAL=60
export POS_ENABLE_ASYNC=1
export POS_ASYNC_WORKERS=4
```

### Production Environment

```bash
# Production-specific environment variables

# Security (Production)
export POS_REQUIRE_HTTPS=1
export POS_FORCE_SSL=1
export POS_API_KEY_ROTATION=1
export POS_AUDIT_LOGGING=1

# Performance (Production)
export POS_ENABLE_CACHING=1
export POS_CACHE_COMPRESSION=1
export POS_CONNECTION_POOLING=1
export POS_QUERY_OPTIMIZATION=1

# Monitoring (Production)
export POS_ENABLE_METRICS=1
export POS_METRICS_ENDPOINT=/api/metrics
export POS_HEALTH_CHECK_ENDPOINT=/api/health
export POS_ALERT_WEBHOOK_URL=https://alerts.yourcompany.com/webhook

# Backup (Production)
export POS_BACKUP_ENABLED=1
export POS_BACKUP_INTERVAL=3600
export POS_BACKUP_RETENTION=7
export POS_BACKUP_ENCRYPTION=1
```

### Development Environment

```bash
# Development-specific environment variables

# Debug Settings
export POS_DEBUG_MODE=1
export POS_LOG_LEVEL=DEBUG
export POS_VERBOSE_ERRORS=1
export POS_SHOW_SQL_QUERIES=1

# Testing Settings
export POS_TEST_MODE=1
export POS_MOCK_EXTERNAL_APIS=1
export POS_SKIP_AUTHENTICATION=1

# Development Tools
export POS_ENABLE_PROFILER=1
export POS_DEV_TOOLS_PORT=8080
export POS_SWAGGER_DOCS=1
```

---

## 🔧 Configuration Validation

### Configuration Check Script

```python
#!/usr/bin/env python3
"""
Configuration validation script for ERPNext POS Integration
"""

import frappe
import json
import sys

def validate_configuration():
    """Validate POS integration configuration"""
    
    issues = []
    
    # Check site configuration
    site_config = frappe.get_site_config()
    pos_config = site_config.get('pos_integration_settings', {})
    
    if not pos_config.get('enable_pos_integration'):
        issues.append("POS integration is not enabled in site config")
    
    # Check database connectivity
    try:
        frappe.db.sql("SELECT 1")
    except Exception as e:
        issues.append(f"Database connectivity issue: {str(e)}")
    
    # Check required DocTypes
    required_doctypes = ['POS Device', 'POS Pricing Rule', 'POS Sync Log']
    for doctype in required_doctypes:
        if not frappe.db.exists('DocType', doctype):
            issues.append(f"Required DocType not found: {doctype}")
    
    # Check custom fields
    required_fields = [
        ('Sales Invoice', 'pos_branch_id'),
        ('Item', 'is_pos_item'),
        ('POS Pricing Rule', 'erpnext_priority')
    ]
    
    for doctype, fieldname in required_fields:
        if not frappe.db.exists('Custom Field', {'dt': doctype, 'fieldname': fieldname}):
            issues.append(f"Required custom field not found: {doctype}.{fieldname}")
    
    # Check pricing rules
    active_rules = frappe.db.count('POS Pricing Rule', {'is_active': 1})
    if active_rules == 0:
        issues.append("No active pricing rules found")
    
    # Check branches
    if frappe.db.exists('DocType', 'Branch'):
        branch_count = frappe.db.count('Branch', {'is_group': 0})
        if branch_count == 0:
            issues.append("No branches configured")
    
    # Generate report
    if issues:
        print("❌ Configuration Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Configuration validation passed")
        return True

if __name__ == "__main__":
    frappe.init(site=sys.argv[1])
    frappe.connect()
    
    if validate_configuration():
        sys.exit(0)
    else:
        sys.exit(1)
```

### Configuration Report

Generate a comprehensive configuration report:

```python
def generate_config_report():
    """Generate detailed configuration report"""
    
    report = {
        'timestamp': frappe.utils.now(),
        'site_config': frappe.get_site_config(),
        'database_status': check_database_status(),
        'doc_types': get_doctype_status(),
        'custom_fields': get_custom_field_status(),
        'pricing_rules': get_pricing_rule_status(),
        'performance_metrics': get_performance_metrics(),
        'security_status': get_security_status()
    }
    
    return report
```

---

## 📞 Support and Troubleshooting

### Common Configuration Issues

#### Installation Issues

**Problem**: Custom fields not appearing
```bash
# Solution: Manual field creation
bench --site your-site-name console
frappe.reload_doctype("Sales Invoice")
frappe.reload_doctype("Item")
```

**Problem**: Database connection errors
```bash
# Solution: Check database configuration
bench --site your-site-name doctor
```

#### Performance Issues

**Problem**: Slow price calculations
```python
# Solution: Enable caching and optimize rules
site_config['pos_integration_settings']['pos_enable_caching'] = 1
site_config['pos_integration_settings']['pos_cache_timeout'] = 600
```

**Problem**: High memory usage
```python
# Solution: Adjust cache settings
site_config['pos_integration_settings']['pos_cache_size_limit'] = '25MB'
```

### Configuration Backup

```bash
# Backup configuration
bench --site your-site-name backup --with-files
bench --site your-site-name execute erpnext_pos_integration.utils.config_backup.backup_config
```

### Configuration Restore

```bash
# Restore configuration
bench --site your-site-name restore backup-file.sql
bench --site your-site-name execute erpnext_pos_integration.utils.config_backup.restore_config
```

---

## 📋 Configuration Checklist

### Pre-Production Checklist

- [ ] ERPNext instance meets minimum requirements
- [ ] Site configuration updated with POS settings
- [ ] Database custom fields applied successfully
- [ ] Required indexes created for performance
- [ ] Pricing rules configured and tested
- [ ] Device registration tested
- [ ] API endpoints verified
- [ ] Security settings configured
- [ ] Logging configured appropriately
- [ ] Performance monitoring enabled
- [ ] Backup procedures in place
- [ ] Documentation updated

### Post-Installation Checklist

- [ ] Configuration validation script passed
- [ ] Test device registration successful
- [ ] Test price calculations working
- [ ] Health check endpoints responding
- [ ] Custom fields visible in forms
- [ ] Sync operations functioning
- [ ] Performance metrics within targets
- [ ] Error logging working correctly
- [ ] Rate limiting configured
- [ ] Security scan passed

---

**Last Updated**: 2025-12-15  
**Version**: 1.0.0  
**Configuration Version**: v1.0