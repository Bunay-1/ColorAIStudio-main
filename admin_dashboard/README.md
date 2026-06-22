# ICAP Enterprise Admin Dashboard

Modern React-based admin dashboard for ICAP Enterprise management.

## Features

- **Dashboard**: Overview with system statistics, charts, and activity monitoring
- **User Management**: Create, edit, and delete users with role-based access control
- **Tenant Management**: Multi-tenant organization management with resource quotas
- **Audit Logs**: Comprehensive audit trail viewing with filtering and export
- **System Health**: Real-time system monitoring and service status
- **Settings**: Configure system settings across multiple categories

## Tech Stack

- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **TailwindCSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Recharts**: Charting library
- **Lucide React**: Icon library
- **Axios**: HTTP client

## Installation

```bash
cd admin_dashboard
npm install
```

## Development

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Build

```bash
npm run build
```

## Configuration

The dashboard connects to the ICAP API at `http://localhost:8000`. To change this:

1. Edit `vite.config.js`
2. Update the `proxy.target` value

## Authentication

The dashboard uses JWT authentication with the ICAP API:
1. Login with admin credentials
2. Token stored in localStorage
3. Token included in API requests via Authorization header

## Components

### App.jsx
Main application component with routing and layout

### Dashboard.jsx
Overview dashboard with statistics and charts

### UserManagement.jsx
User CRUD operations with role management

### TenantManagement.jsx
Tenant management with resource quotas

### AuditLogs.jsx
Audit log viewing with filtering and export

### SystemHealth.jsx
System monitoring and service status

### Settings.jsx
System configuration management

## API Integration

The dashboard integrates with the following ICAP API endpoints:
- `/auth/login` - Authentication
- `/auth/users` - User management
- `/auth/tenants` - Tenant management
- `/auth/audit/logs` - Audit logs
- `/health` - System health

## Deployment

### Production Build

```bash
npm run build
```

The built files will be in the `dist` directory.

### Serve with Nginx

```nginx
server {
    listen 80;
    server_name admin.icap-enterprise.com;
    
    root /path/to/admin_dashboard/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker Deployment

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Security

- JWT token authentication
- Role-based access control
- Secure API communication
- XSS protection via React
- CSRF protection via API

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

Enterprise License - See main project license

## Support

For issues and support:
- Email: support@icap-enterprise.com
- Documentation: https://docs.icap-enterprise.com
