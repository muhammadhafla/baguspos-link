# ERPNext POS Integration - API Documentation

This document provides comprehensive documentation for all REST API endpoints available in the ERPNext POS Integration Bridge App.

## 📋 Table of Contents

- [Authentication](#authentication)
- [Base URL](#base-url)
- [Device Management APIs](#device-management-apis)
- [Pricing APIs](#pricing-apis)
- [System APIs](#system-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [SDK Examples](#sdk-examples)

---

## 🔐 Authentication

All API endpoints require device authentication using API key and device credentials.

### Authentication Method

Devices must include authentication credentials in each request:

```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
}
```

### Getting API Credentials

API credentials are generated during device registration. See the [Device Registration](#register-device) endpoint for details.

---

## 🌐 Base URL

```
https://your-erpnext-instance.com
```

All API endpoints are available at:
```
https://your-erpnext-instance.com/api/method/erpnext_pos_integration.api.{module}.{endpoint}
```

---

## 📱 Device Management APIs

### Register Device

Register a new POS device and generate API credentials.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.device_api.register_device`

**Request Body**:
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

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branch` | string | Yes | Branch ID where device will be registered |
| `device_name` | string | Yes | Human-readable device name |
| `registration_code` | string | Yes | Registration code for device setup |
| `device_type` | string | No | Type of device (Tablet, Desktop, Mobile, Kiosk) |
| `os_version` | string | No | Operating system version |
| `app_version` | string | No | Application version |

**Success Response (200)**:
```json
{
    "status": "success",
    "message": "Device registered successfully",
    "data": {
        "device_id": "POS-001-001",
        "api_key": "sk_live_abc123def456",
        "api_secret": "sk_secret_xyz789",
        "device_name": "POS-001-Front-Counter"
    }
}
```

**Error Response (400)**:
```json
{
    "status": "error",
    "message": "Device with this name already exists"
}
```

**Use Cases**:
- Initial device setup
- Device replacement
- New branch device registration

---

### Health Check

Check system health for POS device and update heartbeat.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.device_api.health_check`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
}
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_id` | string | Yes | Unique device identifier |
| `api_key` | string | Yes | Device API key for authentication |

**Success Response (200)**:
```json
{
    "status": "success",
    "authenticated": true,
    "device": {
        "device_id": "POS-001-001",
        "device_name": "POS-001-Front-Counter",
        "branch": "MAIN-BRANCH-001",
        "last_heartbeat": "2025-12-15T10:08:00.000Z"
    },
    "health": {
        "database": true,
        "api_performance": 45,
        "last_sync": "2025-12-15T09:58:00.000Z",
        "pending_operations": 0,
        "system_resources": {
            "status": "healthy",
            "memory_usage": "normal",
            "cpu_usage": "normal"
        },
        "overall_status": "healthy"
    },
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Health Check Details**:

| Metric | Description | Healthy Threshold |
|--------|-------------|-------------------|
| `database` | Database connectivity status | `true` |
| `api_performance` | API response time in ms | `< 1000ms` |
| `last_sync` | Last successful sync timestamp | Within 24h |
| `pending_operations` | Number of pending sync operations | `< 10` |
| `system_resources` | Server resource status | `"healthy"` |

**Use Cases**:
- Device startup verification
- Periodic health monitoring
- System diagnostics

---

### Update Device Heartbeat

Update device heartbeat to mark it as online.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.device_api.update_device_heartbeat`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
}
```

**Success Response (200)**:
```json
{
    "status": "success",
    "message": "Heartbeat updated successfully",
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Use Cases**:
- Lightweight online status update
- Connection keep-alive
- Mobile app background monitoring

---

### Get Device Status

Get current status of a POS device.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.device_api.get_device_status`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
}
```

**Success Response (200)**:
```json
{
    "status": "success",
    "device": {
        "device_id": "POS-001-001",
        "device_name": "POS-001-Front-Counter",
        "branch": "MAIN-BRANCH-001",
        "sync_status": "Online",
        "last_heartbeat": "2025-12-15T10:08:00.000Z",
        "last_sync_at": "2025-12-15T09:58:00.000Z",
        "is_registered": true
    },
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Use Cases**:
- Device status monitoring
- Admin dashboard data
- Troubleshooting device issues

---

## 💰 Pricing APIs

### Calculate Price

Calculate final price using 8-level pricing engine.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.pricing_api.calculate_price`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here",
    "item_code": "ITEM-001",
    "base_price": 100.00,
    "quantity": 2,
    "total_amount": 200.00,
    "customer": "CUST-001",
    "branch_id": "MAIN-BRANCH-001"
}
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_id` | string | Yes | POS device identifier |
| `api_key` | string | Yes | Device API key for authentication |
| `item_code` | string | Yes | Item code to calculate price for |
| `base_price` | float | Yes | Base item price |
| `quantity` | integer | No | Quantity being purchased (default: 1) |
| `total_amount` | float | No | Total transaction amount (default: 0) |
| `customer` | string | No | Customer ID for customer-specific pricing |
| `branch_id` | string | No | Branch ID (uses device branch if not provided) |

**Success Response (200)**:
```json
{
    "status": "success",
    "authenticated": true,
    "device_id": "POS-001-001",
    "device_name": "POS-001-Front-Counter",
    "branch_id": "MAIN-BRANCH-001",
    "item_code": "ITEM-001",
    "calculation_time_ms": 45.23,
    "price_data": {
        "base_price": 100.00,
        "final_price": 85.00,
        "discount_amount": 15.00,
        "discount_percentage": 15.0,
        "rule_applied": "CUSTOMER_VOLUME_DISCOUNT",
        "applied_rules": [
            {
                "rule_name": "Customer Volume Discount",
                "discount_type": "percentage",
                "discount_value": 15.0,
                "priority": 5
            }
        ],
        "price_breakdown": {
            "subtotal": 200.00,
            "discount": -30.00,
            "tax": 17.00,
            "total": 187.00
        }
    },
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Price Data Structure**:

| Field | Type | Description |
|-------|------|-------------|
| `base_price` | float | Original item price |
| `final_price` | float | Calculated final price |
| `discount_amount` | float | Total discount amount |
| `discount_percentage` | float | Total discount percentage |
| `rule_applied` | string | Name of the applied pricing rule |
| `applied_rules` | array | Array of applied pricing rules |
| `price_breakdown` | object | Detailed price breakdown |

**Performance Warning**:
If calculation time exceeds 500ms, a `performance_warning` field will be included.

**Use Cases**:
- Real-time price calculations during sales
- Quote generation
- Price verification

---

### Get Pricing Rules

Retrieve applicable pricing rules for given context.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.pricing_api.get_pricing_rules`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here",
    "item_code": "ITEM-001",
    "branch_id": "MAIN-BRANCH-001",
    "customer": "CUST-001"
}
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_id` | string | Yes | POS device identifier |
| `api_key` | string | Yes | Device API key for authentication |
| `item_code` | string | No | Item code to get rules for |
| `branch_id` | string | No | Branch ID (uses device branch if not provided) |
| `customer` | string | No | Customer ID for customer-specific rules |

**Success Response (200)**:
```json
{
    "status": "success",
    "authenticated": true,
    "device_id": "POS-001-001",
    "device_name": "POS-001-Front-Counter",
    "branch_id": "MAIN-BRANCH-001",
    "item_code": "ITEM-001",
    "customer": "CUST-001",
    "rules_count": 3,
    "rules": [
        {
            "name": "PRICING-RULE-001",
            "rule_name": "Customer Volume Discount",
            "pricing_type": "discount_percentage",
            "priority_level": 5,
            "erpnext_priority": 100,
            "is_active": true,
            "valid_from": "2025-01-01",
            "valid_upto": "2025-12-31",
            "item_code": "ITEM-001",
            "item_group": null,
            "brand": null,
            "customer": "CUST-001",
            "customer_group": null,
            "territory": null,
            "base_price": null,
            "discount_percentage": 15.0,
            "discount_amount": null,
            "min_quantity": 10,
            "max_quantity": null,
            "min_spend_amount": null,
            "bxgy_buy_qty": null,
            "bxgy_get_qty": null
        }
    ],
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Use Cases**:
- Debug pricing calculations
- Show available promotions
- Admin interface for rule management

---

### Validate Pricing

Validate pricing engine configuration and device context.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.pricing_api.validate_pricing`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
}
```

**Success Response (200)**:
```json
{
    "status": "success",
    "authenticated": true,
    "device_id": "POS-001-001",
    "device_name": "POS-001-Front-Counter",
    "device_status": "active",
    "branch_id": "MAIN-BRANCH-001",
    "pricing_engine": {
        "status": "success",
        "issues": [],
        "statistics": {
            "total_rules": 25,
            "active_rules": 20,
            "cache_hit_rate": 85.5
        },
        "test_calculation": {
            "base_price": 100.0,
            "final_price": 90.0,
            "rule_applied": "TEST_RULE",
            "calculation_time_ms": 12.5
        }
    },
    "overall_status": "healthy",
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Use Cases**:
- System health checks
- Configuration validation
- Troubleshooting pricing issues

---

### Calculate Bulk Prices

Calculate prices for multiple items efficiently.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.pricing_api.calculate_bulk_prices`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here",
    "items_data": [
        {
            "item_code": "ITEM-001",
            "base_price": 100.00,
            "quantity": 2
        },
        {
            "item_code": "ITEM-002",
            "base_price": 50.00,
            "quantity": 1
        }
    ],
    "customer": "CUST-001",
    "branch_id": "MAIN-BRANCH-001"
}
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_id` | string | Yes | POS device identifier |
| `api_key` | string | Yes | Device API key for authentication |
| `items_data` | array | Yes | Array of item objects (max 50 items) |
| `customer` | string | No | Customer ID |
| `branch_id` | string | No | Branch ID |

**Item Object Structure**:
```json
{
    "item_code": "string",
    "base_price": "float",
    "quantity": "integer"
}
```

**Success Response (200)**:
```json
{
    "status": "success",
    "authenticated": true,
    "device_id": "POS-001-001",
    "device_name": "POS-001-Front-Counter",
    "branch_id": "MAIN-BRANCH-001",
    "customer": "CUST-001",
    "items_processed": 2,
    "bulk_calculation": {
        "total_calculation_time": 0.045,
        "items": [
            {
                "item_code": "ITEM-001",
                "base_price": 100.00,
                "quantity": 2,
                "final_price": 85.00,
                "discount_amount": 30.00,
                "rule_applied": "CUSTOMER_VOLUME_DISCOUNT"
            },
            {
                "item_code": "ITEM-002",
                "base_price": 50.00,
                "quantity": 1,
                "final_price": 50.00,
                "discount_amount": 0.00,
                "rule_applied": null
            }
        ],
        "total_savings": 30.00,
        "average_calculation_time": 22.5
    },
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Limits**:
- Maximum 50 items per request
- Response time should be under 1 second for optimal performance

**Use Cases**:
- Shopping cart calculations
- Batch pricing operations
- Invoice generation

---

### Clear Pricing Cache

Clear pricing engine cache for device.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.pricing_api.clear_pricing_cache`

**Request Body**:
```json
{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
}
```

**Success Response (200)**:
```json
{
    "status": "success",
    "authenticated": true,
    "device_id": "POS-001-001",
    "cache_clear_result": {
        "cache_type": "pricing_engine",
        "entries_cleared": 156,
        "cache_size_before": "2.4MB",
        "cache_size_after": "0MB"
    },
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Use Cases**:
- Force rule updates
- Cache debugging
- Performance troubleshooting

---

## 🖥️ System APIs

### Get System Overview

Get system overview for admin dashboard.

**Endpoint**: `POST /api/method/erpnext_pos_integration.api.device_api.get_system_overview`

**Request Body**: No authentication required

**Success Response (200)**:
```json
{
    "status": "success",
    "overview": {
        "devices": {
            "total": 25,
            "online": 20,
            "offline": 3,
            "error": 2,
            "last_24h_registrations": 2
        },
        "sync": {
            "total_operations": 1547,
            "successful": 1520,
            "failed": 27,
            "success_rate": 98.3,
            "average_sync_time": 2.3
        },
        "pricing": {
            "total_calculations": 8756,
            "cache_hit_rate": 87.2,
            "average_calculation_time": 34.5,
            "rules_applied": 2847
        },
        "performance": {
            "api_response_time": 45.2,
            "database_query_time": 12.1,
            "system_load": "normal"
        }
    },
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

**Use Cases**:
- Admin dashboard metrics
- System monitoring
- Performance tracking

---

## ⚠️ Error Handling

### Standard Error Response Format

All errors follow a consistent format:

```json
{
    "status": "error",
    "message": "Human-readable error message",
    "error_code": "SPECIFIC_ERROR_CODE",
    "authenticated": true,
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Invalid device credentials |
| `MISSING_PARAMETERS` | 400 | Required parameters missing |
| `DEVICE_NOT_FOUND` | 404 | Device not registered |
| `BRANCH_NOT_FOUND` | 404 | Branch does not exist |
| `PRICING_ENGINE_ERROR` | 500 | Internal pricing calculation error |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_ITEM_CODE` | 400 | Item code not found |
| `CONFIGURATION_ERROR` | 500 | System configuration issue |

### Error Categories

**Authentication Errors (401)**:
- Invalid API key
- Expired credentials
- Device not registered

**Validation Errors (400)**:
- Missing required parameters
- Invalid parameter types
- Parameter value out of range

**Resource Errors (404)**:
- Device not found
- Branch not found
- Item code not found

**Server Errors (500)**:
- Database connection issues
- Pricing engine errors
- System configuration problems

---

## 🚦 Rate Limiting

### Rate Limits

- **Device Registration**: 5 requests per minute per IP
- **Price Calculations**: 100 requests per minute per device
- **Health Checks**: 60 requests per minute per device
- **Bulk Operations**: 10 requests per minute per device
- **System Overview**: 10 requests per minute per IP

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234567
```

### Rate Limit Exceeded Response (429)

```json
{
    "status": "error",
    "message": "Rate limit exceeded. Please try again later.",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "retry_after": 60,
    "timestamp": "2025-12-15T10:08:00.000Z"
}
```

---

## 💻 SDK Examples

### Python SDK Example

```python
import requests
import json

class POSIntegrationClient:
    def __init__(self, base_url, device_id, api_key):
        self.base_url = base_url
        self.device_id = device_id
        self.api_key = api_key
        self.session = requests.Session()
    
    def register_device(self, branch, device_name, registration_code, **kwargs):
        """Register a new device"""
        url = f"{self.base_url}/api/method/erpnext_pos_integration.api.device_api.register_device"
        data = {
            "branch": branch,
            "device_name": device_name,
            "registration_code": registration_code,
            **kwargs
        }
        response = self.session.post(url, json=data)
        return response.json()
    
    def calculate_price(self, item_code, base_price, quantity=1, **kwargs):
        """Calculate price for an item"""
        url = f"{self.base_url}/api/method/erpnext_pos_integration.api.pricing_api.calculate_price"
        data = {
            "device_id": self.device_id,
            "api_key": self.api_key,
            "item_code": item_code,
            "base_price": base_price,
            "quantity": quantity,
            **kwargs
        }
        response = self.session.post(url, json=data)
        return response.json()
    
    def health_check(self):
        """Perform health check"""
        url = f"{self.base_url}/api/method/erpnext_pos_integration.api.device_api.health_check"
        data = {
            "device_id": self.device_id,
            "api_key": self.api_key
        }
        response = self.session.post(url, json=data)
        return response.json()

# Usage example
client = POSIntegrationClient(
    base_url="https://your-erpnext-instance.com",
    device_id="POS-001-001",
    api_key="your-api-key-here"
)

# Calculate price
result = client.calculate_price(
    item_code="ITEM-001",
    base_price=100.00,
    quantity=2,
    customer="CUST-001"
)

print(f"Final price: ${result['price_data']['final_price']}")
```

### JavaScript SDK Example

```javascript
class POSIntegrationClient {
    constructor(baseUrl, deviceId, apiKey) {
        this.baseUrl = baseUrl;
        this.deviceId = deviceId;
        this.apiKey = apiKey;
    }
    
    async registerDevice(branch, deviceName, registrationCode, options = {}) {
        const url = `${this.baseUrl}/api/method/erpnext_pos_integration.api.device_api.register_device`;
        const data = {
            branch,
            device_name: deviceName,
            registration_code: registrationCode,
            ...options
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    }
    
    async calculatePrice(itemCode, basePrice, quantity = 1, options = {}) {
        const url = `${this.baseUrl}/api/method/erpnext_pos_integration.api.pricing_api.calculate_price`;
        const data = {
            device_id: this.deviceId,
            api_key: this.apiKey,
            item_code: itemCode,
            base_price: basePrice,
            quantity,
            ...options
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    }
    
    async bulkCalculate(items, options = {}) {
        const url = `${this.baseUrl}/api/method/erpnext_pos_integration.api.pricing_api.calculate_bulk_prices`;
        const data = {
            device_id: this.deviceId,
            api_key: this.apiKey,
            items_data: items,
            ...options
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    }
}

// Usage example
const client = new POSIntegrationClient(
    'https://your-erpnext-instance.com',
    'POS-001-001',
    'your-api-key-here'
);

// Calculate bulk prices
const cartItems = [
    { item_code: 'ITEM-001', base_price: 100.00, quantity: 2 },
    { item_code: 'ITEM-002', base_price: 50.00, quantity: 1 }
];

const result = await client.bulkCalculate(cartItems, {
    customer: 'CUST-001'
});

console.log('Total savings:', result.bulk_calculation.total_savings);
```

### cURL Examples

```bash
# Device Registration
curl -X POST https://your-erpnext-instance.com/api/method/erpnext_pos_integration.api.device_api.register_device \
  -H "Content-Type: application/json" \
  -d '{
    "branch": "MAIN-BRANCH-001",
    "device_name": "POS-001-Front-Counter",
    "registration_code": "REG-CODE-12345",
    "device_type": "Tablet"
  }'

# Price Calculation
curl -X POST https://your-erpnext-instance.com/api/method/erpnext_pos_integration.api.pricing_api.calculate_price \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here",
    "item_code": "ITEM-001",
    "base_price": 100.00,
    "quantity": 2,
    "customer": "CUST-001"
  }'

# Health Check
curl -X POST https://your-erpnext-instance.com/api/method/erpnext_pos_integration.api.device_api.health_check \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
  }'

# Bulk Price Calculation
curl -X POST https://your-erpnext-instance.com/api/method/erpnext_pos_integration.api.pricing_api.calculate_bulk_prices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here",
    "items_data": [
      {"item_code": "ITEM-001", "base_price": 100.00, "quantity": 2},
      {"item_code": "ITEM-002", "base_price": 50.00, "quantity": 1}
    ]
  }'
```

---

## 📞 Support

For API support and questions:

- **Documentation**: [Full Documentation](../README.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/erpnext-pos-integration/issues)
- **Email**: api-support@your-org.com

---

**Last Updated**: 2025-12-15  
**Version**: 1.0.0  
**API Version**: v1.0