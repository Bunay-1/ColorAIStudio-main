# ICAP Enterprise JavaScript Client SDK

JavaScript SDK for interacting with ICAP Enterprise API.

## Installation

### Browser

```html
<script src="icap-client.js"></script>
```

### Node.js

```bash
npm install
```

```javascript
const { ICAPClient, ICAPConfig } = require('./icap-client.js');
```

## Usage

### Browser

```javascript
// Configure client
const config = new ICAPConfig('http://localhost:8000', {
    username: 'admin',
    password: 'your_password',
    tenantId: 'default'
});

// Initialize client
const client = new ICAPClient(config);

// Color Analysis
client.analyzeColor([50, 0, 0], 'delta_e_2000')
    .then(result => console.log(result))
    .catch(error => console.error(error));

// Vision Analysis
const imageFile = document.getElementById('imageInput').files[0];
client.detectDefects(imageFile)
    .then(defects => console.log(defects))
    .catch(error => console.error(error));

// RAG Query
client.queryRAG('What is the color tolerance?', 5)
    .then(results => console.log(results))
    .catch(error => console.error(error));

// Notifications
client.createNotification({
    title: 'Test Notification',
    message: 'This is a test',
    channel: 'websocket',
    priority: 'info'
})
    .then(notification => console.log(notification))
    .catch(error => console.error(error));

// Analytics
client.getMetrics('color_analysis', '24h')
    .then(metrics => console.log(metrics))
    .catch(error => console.error(error));

// Webhooks
client.createWebhook({
    url: 'https://your-webhook-url.com',
    events: ['user.created', 'alert.triggered'],
    secret: 'your-secret'
})
    .then(webhook => console.log(webhook))
    .catch(error => console.error(error));

// Export Data
client.exportData('users', 'json')
    .then(exported => console.log(exported))
    .catch(error => console.error(error));
```

### Node.js

```javascript
const { ICAPClient, ICAPConfig } = require('./icap-client.js');

// Configure client
const config = new ICAPConfig('http://localhost:8000', {
    username: 'admin',
    password: 'your_password',
    tenantId: 'default'
});

// Initialize client
const client = new ICAPClient(config);

// Async/await usage
async function main() {
    try {
        // Color Analysis
        const result = await client.analyzeColor([50, 0, 0], 'delta_e_2000');
        console.log(result);

        // Vision Analysis
        const fs = require('fs');
        const imageFile = fs.createReadStream('path/to/image.jpg');
        const defects = await client.detectDefects(imageFile);
        console.log(defects);

        // RAG Query
        const results = await client.queryRAG('What is the color tolerance?', 5);
        console.log(results);

        // Notifications
        const notification = await client.createNotification({
            title: 'Test Notification',
            message: 'This is a test',
            channel: 'websocket',
            priority: 'info'
        });
        console.log(notification);

        // Analytics
        const metrics = await client.getMetrics('color_analysis', '24h');
        console.log(metrics);

        // Webhooks
        const webhook = await client.createWebhook({
            url: 'https://your-webhook-url.com',
            events: ['user.created', 'alert.triggered'],
            secret: 'your-secret'
        });
        console.log(webhook);

        // Export Data
        const exported = await client.exportData('users', 'json');
        console.log(exported);
    } catch (error) {
        console.error('Error:', error);
    }
}

main();
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

See `icap-client.js` for full API reference.
