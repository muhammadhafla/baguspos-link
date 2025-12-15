# ERPNext POS Integration Bridge App

A production-ready bridge application for seamless POS integration with ERPNext, enabling offline-first operations with sophisticated pricing calculations and device management.

[![ERPNext](https://img.shields.io/badge/ERPNext-v14+-blue.svg)](https://erpnext.com)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

This application provides a robust integration layer between custom POS systems and ERPNext, featuring:

- **🔐 Secure Device Management**: Register and manage POS devices with API-based authentication
- **💰 Advanced Pricing Engine**: 8-level pricing system with complex rule evaluation
- **⚡ Offline-First Operations**: Continue operations even when disconnected from ERPNext
- **📊 Real-time Synchronization**: Seamless data sync between POS devices and ERPNext
- **🛡️ Production Ready**: Comprehensive installation, uninstallation, and migration support

## 🚀 Quick Start

### Prerequisites

- ERPNext v14.0 or higher
- Python 3.8+
- Frappe Framework v14.0+
- Administrator access to your ERPNext instance

### Installation

1. **Clone the repository**
   ```bash
   cd /path/to/your/apps
   git clone https://github.com/your-org/erpnext-pos-integration.git
   cd erpnext-pos-integration
   ```

2. **Install the application**
   ```bash
   bench get-app erpnext_pos_integration
   bench --site your-site-name install-app erpnext_pos_integration
   ```

3. **Verify installation**
   ```bash
   bench --site your-site-name list-apps
   ```

You should see `erpnext_pos_integration` in the installed apps list.

### Post-Installation Setup

1. **Create your first pricing rule**
   - Go to: POS Integration > Pricing Rules > New
   - Configure your pricing conditions and actions
   - Set priority levels for rule precedence

2. **Register your first POS device**
   - Use the device registration API
   - Configure device settings and branch assignment
   - Generate API credentials for secure communication

## 📚 Core Features

### Device Management
- **Device Registration**: Secure device onboarding with registration codes
- **API Authentication**: API key/secret based authentication system
- **Health Monitoring**: Real-time device health checks and heartbeat monitoring
- **Status Tracking**: Online/offline status with sync state monitoring

### Pricing Engine
- **8-Level Pricing**: Comprehensive pricing rule evaluation system
- **Bulk Calculations**: Efficient pricing for multiple items simultaneously
- **Complex Conditions**: Support for customer, branch, item, quantity-based rules
- **Performance Optimized**: Sub-500ms response times for price calculations

### Synchronization
- **Offline Support**: Continue operations when disconnected
- **Data Sync**: Automatic synchronization when connection is restored
- **Error Handling**: Robust error recovery and retry mechanisms
- **Audit Trail**: Complete logging of sync operations

## 🔧 Configuration

### Basic Configuration

1. **Configure Branch Settings**
   ```
   Setup > Stock > Branch
   ```

2. **Set up Pricing Rules**
   ```
   POS Integration > Pricing Rules > New
   ```

3. **Register POS Devices**
   - Use the device registration API
   - Configure device-specific settings

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POS_CACHE_TIMEOUT` | Pricing cache timeout (seconds) | 3600 |
| `POS_BULK_LIMIT` | Maximum items per bulk request | 50 |
| `POS_HEARTBEAT_INTERVAL` | Device heartbeat interval (seconds) | 300 |
| `POS_SYNC_BATCH_SIZE` | Sync batch size for large datasets | 100 |

## 🔌 API Reference

### Device Management APIs

#### Register Device
```python
POST /api/method/erpnext_pos_integration.api.device_api.register_device

{
    "branch": "MAIN-BRANCH-001",
    "device_name": "POS-001-Front-Counter",
    "registration_code": "REG-CODE-12345",
    "device_type": "Tablet",
    "os_version": "Android 11",
    "app_version": "1.0.0"
}
```

#### Health Check
```python
POST /api/method/erpnext_pos_integration.api.device_api.health_check

{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here"
}
```

### Pricing APIs

#### Calculate Price
```python
POST /api/method/erpnext_pos_integration.api.pricing_api.calculate_price

{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here",
    "item_code": "ITEM-001",
    "base_price": 100.00,
    "quantity": 2,
    "customer": "CUST-001",
    "branch_id": "MAIN-BRANCH-001"
}
```

#### Bulk Price Calculation
```python
POST /api/method/erpnext_pos_integration.api.pricing_api.calculate_bulk_prices

{
    "device_id": "POS-001-001",
    "api_key": "your-api-key-here",
    "items_data": [
        {"item_code": "ITEM-001", "base_price": 100.00, "quantity": 2},
        {"item_code": "ITEM-002", "base_price": 50.00, "quantity": 1}
    ],
    "customer": "CUST-001"
}
```

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   POS Device    │    │  ERPNext Core    │    │ Pricing Engine  │
│                 │    │                  │    │                 │
│ • Frontend App  │◄──►│ • DocTypes       │◄──►│ • Rule Engine   │
│ • Local Storage │    │ • API Layer      │    │ • Cache Layer   │
│ • Sync Logic    │    │ • Authentication │    │ • Validation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐              │
         └──────────────►│   Database       │◄─────────────┘
                        │                  │
                        │ • ERPNext DB     │
                        │ • Sync Logs      │
                        │ • Audit Trail    │
                        └──────────────────┘
```

### Data Flow

1. **Device Registration**: POS device registers with ERPNext → API credentials generated
2. **Price Request**: Device requests pricing → Authentication → Rule evaluation → Response
3. **Sync Operations**: Local changes sync to ERPNext → Conflict resolution → Confirmation

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
bench --site your-site-name test erpnext_pos_integration

# Run specific test module
bench --site your-site-name test erpnext_pos_integration.tests.test_pricing_engine

# Run with coverage
bench --site your-site-name test --coverage erpnext_pos_integration
```

### Test Structure
```
tests/
├── test_pos_device.py       # Device management tests
├── test_pos_pricing_rule.py # Pricing rule tests
└── test_pricing_engine.py   # Pricing engine tests
```

## 🚀 Deployment

### Production Deployment Checklist

- [ ] ERPNext instance configured and tested
- [ ] App installed with `install-app` command
- [ ] Pricing rules configured and tested
- [ ] POS devices registered and tested
- [ ] API endpoints verified
- [ ] Performance benchmarks met
- [ ] Backup procedures in place
- [ ] Monitoring configured

### Performance Tuning

1. **Database Optimization**
   ```sql
   -- Add indexes for better performance
   CREATE INDEX idx_pos_device_branch ON `tabPOS Device`(branch);
   CREATE INDEX idx_pricing_rule_priority ON `tabPOS Pricing Rule`(priority_level, erpnext_priority);
   ```

2. **Cache Configuration**
   ```python
   # In site_config.json
   {
     "pos_cache_timeout": 1800,
     "pos_enable_caching": true
   }
   ```

## 🔧 Troubleshooting

### Common Issues

#### Device Registration Fails
- Verify branch exists in ERPNext
- Check registration code is valid
- Ensure device name is unique

#### Price Calculation Errors
- Validate pricing rules configuration
- Check item code exists in ERPNext
- Verify device has proper permissions

#### Sync Issues
- Check network connectivity
- Review sync logs in ERPNext
- Verify device authentication

### Debug Mode

Enable debug logging:
```python
# In hooks.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Use the system overview API for diagnostics:
```python
POST /api/method/erpnext_pos_integration.api.device_api.get_system_overview
```

## 📊 Monitoring

### Key Metrics

- **Device Status**: Online/offline counts
- **API Response Times**: Average and P95 response times
- **Pricing Calculations**: Success rate and performance
- **Sync Operations**: Sync success rate and lag times
- **Error Rates**: API error rates by endpoint

### Logging

Logs are stored in:
- **Application Logs**: `logs/erpnext_pos_integration.log`
- **Error Logs**: `logs/error.log`
- **Sync Logs**: Database table `POS Sync Log`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 erpnext_pos_integration/
```

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/erpnext-pos-integration/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/erpnext-pos-integration/discussions)
- **Email**: support@your-org.com

## 🙏 Acknowledgments

- ERPNext Community for the robust framework
- Frappe Technologies for the excellent development platform
- All contributors and testers

---

**Built with ❤️ for the ERPNext Community**