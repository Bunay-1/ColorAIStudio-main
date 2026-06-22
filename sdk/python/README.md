# ICAP Enterprise Python Client SDK

Python SDK for interacting with ICAP Enterprise API.

## Installation

```bash
pip install requests
```

## Usage

```python
from icap_client import ICAPClient, ICAPConfig

# Configure client
config = ICAPConfig(
    base_url="http://localhost:8000",
    username="admin",
    password="your_password",
    tenant_id="default"
)

# Initialize client
client = ICAPClient(config)

# Color Analysis
result = client.analyze_color([50, 0, 0], method="delta_e_2000")
print(result)

# Vision Analysis
defects = client.detect_defects("path/to/image.jpg")
print(defects)

# RAG Query
results = client.query_rag("What is the color tolerance?")
print(results)

# Notifications
notification = client.create_notification({
    "title": "Test Notification",
    "message": "This is a test",
    "channel": "websocket",
    "priority": "info"
})
print(notification)

# Analytics
metrics = client.get_metrics("color_analysis", period="24h")
print(metrics)

# Webhooks
webhook = client.create_webhook({
    "url": "https://your-webhook-url.com",
    "events": ["user.created", "alert.triggered"],
    "secret": "your-secret"
})
print(webhook)

# Export Data
exported = client.export_data("users", format="json")
print(exported)

# Close client
client.close()
```

## Features

- Authentication (API key, username/password)
- Color analysis
- Vision analysis
- RAG system
- Notifications and alerts
- Analytics and reporting
- Webhooks
- Compliance reporting
- Data export/import
- Multi-factor authentication
- Cache management

## API Reference

See `icap_client.py` for full API reference.
