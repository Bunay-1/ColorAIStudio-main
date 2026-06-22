# Monitoring and Alerting Configuration
=====================================

## Overview
ICAP v8.9.5 Enterprise includes comprehensive monitoring and alerting capabilities for production deployment. This guide covers setup and configuration of monitoring systems.

## System Monitoring

### Health Check Endpoints
ICAP provides a comprehensive health check endpoint:
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-06-20T10:30:00Z",
  "version": "8.9.5",
  "components": {
    "database": "healthy",
    "qdrant": "healthy",
    "ollama": "healthy",
    "rag_system": "healthy",
    "vision_engine": "healthy",
    "color_engine": "healthy"
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "disk_percent": 35.1
  }
}
```

ICAP also exposes a readiness probe:
```bash
curl http://localhost:8000/readyz
```

The readiness endpoint is optimized for Kubernetes and load balancer probes, and it verifies the database connection plus critical dependency availability.

### Prometheus Metrics
ICAP exposes Prometheus metrics at `/metrics`:
```bash
curl http://localhost:8000/metrics
```

Available metrics:
- `icap_requests_total` - Total API requests
- `icap_request_duration_seconds` - Request duration
- `icap_active_sessions` - Active user sessions
- `icap_database_connections` - Database connection pool usage
- `icap_cache_hits` - Cache hit rate
- `icap_errors_total` - Total errors

### System Metrics Monitoring
```python
from utils.performance_optimizer import PerformanceMonitor

# Get system metrics
metrics = PerformanceMonitor.get_system_metrics()
print(f"CPU: {metrics['cpu_percent']}%")
print(f"Memory: {metrics['memory_percent']}%")
print(f"Disk: {metrics['disk_percent']}%")
```

## Prometheus Configuration

### Prometheus Setup
Create `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'icap'
    static_configs:
      - targets: ['icap-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'postgres_exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Docker Compose with Prometheus
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
```

## Grafana Dashboards

### Import Dashboard
1. Open Grafana: `http://localhost:3000`
2. Login with admin/admin
3. Navigate to Dashboards → Import
4. Use dashboard ID or upload JSON

### Key Metrics to Monitor
- **API Performance:** Request rate, response time, error rate
- **System Resources:** CPU, memory, disk, network
- **Database:** Connection pool, query performance, cache hit rate
- **Business Metrics:** Measurements per hour, defect rate, quality score
- **Security:** Failed login attempts, rate limit violations, suspicious activity

### Alert Rules
Create `alert_rules.yml`:
```yaml
groups:
  - name: icap_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(icap_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, icap_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "P95 response time is {{ $value }}s"

      - alert: HighCPUUsage
        expr: cpu_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      - alert: HighMemoryUsage
        expr: memory_percent > 85
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"

      - alert: LowCacheHitRate
        expr: rate(icap_cache_hits[5m]) / rate(icap_cache_requests[5m]) < 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}%"
```

## Alerting Configuration

### Slack Integration
Configure Slack webhook in Prometheus:
```yaml
alertmanager:
  slack_configs:
    - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
      channel: '#icap-alerts'
      username: 'Prometheus'
      icon_emoji: ':warning:'
```

### Email Integration
Configure SMTP in Alertmanager:
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@icap-enterprise.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-password'

receivers:
  - name: 'email-receiver'
    email_configs:
      - to: 'admin@icap-enterprise.com'
        from: 'alerts@icap-enterprise.com'
        headers:
          Subject: '[ICAP Alert] {{ .GroupLabels.alertname }}'
```

### SMS Integration (Twilio)
Create alert notification script:
```python
from twilio.rest import Client

def send_sms_alert(message: str, phone_number: str):
    client = Client(
        account_sid=os.environ.get('TWILIO_ACCOUNT_SID'),
        auth_token=os.environ.get('TWILIO_AUTH_TOKEN')
    )
    
    message = client.messages.create(
        body=f"[ICAP ALERT] {message}",
        from_='+1234567890',
        to=phone_number
    )
```

## Application Monitoring

### Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_counter = Counter('icap_requests_total', 'Total API requests', ['method', 'endpoint'])
request_duration = Histogram('icap_request_duration_seconds', 'Request duration')
active_sessions = Gauge('icap_active_sessions', 'Active user sessions')
database_connections = Gauge('icap_database_connections', 'Database connections')

# Use metrics in endpoints
@router.get("/measurements")
async def get_measurements():
    request_counter.labels(method='GET', endpoint='/measurements').inc()
    
    with request_duration.time():
        result = fetch_measurements()
    
    return result
```

### Structured Logging
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_json,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Use structured logging
logger = structlog.get_logger()
logger.info("user_action", user_id="john", action="login", tenant_id="company_a")
```

### Distributed Tracing
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure tracing
FastAPIInstrumentor.instrument_app(app)

# Add custom spans
tracer = trace.get_tracer(__name__)

@router.get("/measurements")
async def get_measurements():
    with tracer.start_as_current_span("fetch_measurements"):
        result = fetch_measurements()
    return result
```

## Log Aggregation

### ELK Stack Setup
```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

### Logstash Configuration
```conf
input {
  file {
    path => "/var/log/icap/*.log"
    start_position => "beginning"
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "icap-logs-%{+YYYY.MM.dd}"
  }
}
```

## Alert Thresholds

### Recommended Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | > 1% | > 5% |
| Response Time (P95) | > 500ms | > 1s |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Disk Usage | > 85% | > 95% |
| Database Connections | > 80% | > 95% |
| Cache Hit Rate | < 70% | < 50% |

### Business Metrics
| Metric | Warning | Critical |
|--------|---------|----------|
| Defect Rate | > 5% | > 10% |
| Quality Score | < 90 | < 80 |
| API Availability | < 99% | < 95% |
| Failed Logins | > 10/hour | > 50/hour |

## Alert Escalation

### Escalation Policy
```yaml
escalation_policy:
  - level: 1
    severity: info
    notification: slack
    channel: '#icap-info'
    delay: 0m
  
  - level: 2
    severity: warning
    notification: slack
    channel: '#icap-alerts'
    delay: 5m
    escalate_after: 30m
  
  - level: 3
    severity: critical
    notification: [slack, email, sms]
    channels: ['#icap-critical', 'admin@icap.com']
    delay: 0m
    escalate_after: 10m
```

### On-Call Rotation
```python
# Configure on-call schedule
on_call_schedule = {
    "Monday": "admin@icap.com",
    "Tuesday": "ops@icap.com",
    "Wednesday": "admin@icap.com",
    "Thursday": "ops@icap.com",
    "Friday": "admin@icap.com",
    "Saturday": "oncall@icap.com",
    "Sunday": "oncall@icap.com"
}

def get_on_call_contact(day: str):
    return on_call_schedule.get(day, "admin@icap.com")
```

## Dashboard Templates

### System Overview Dashboard
- CPU, Memory, Disk usage
- Network I/O
- Active connections
- Request rate
- Error rate

### API Performance Dashboard
- Request rate by endpoint
- Response time percentiles (P50, P95, P99)
- Error rate by endpoint
- Active sessions
- Rate limit violations

### Business Metrics Dashboard
- Measurements per hour
- Defect rate trend
- Quality score distribution
- Tenant activity
- User activity

### Security Dashboard
- Failed login attempts
- Rate limit violations
- Suspicious activity
- Token blacklist size
- Session activity

## Troubleshooting

### Alerts Not Firing
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Alertmanager configuration
curl http://localhost:9093/api/v1/status

# Check Prometheus rules
curl http://localhost:9090/api/v1/rules
```

### Metrics Not Available
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Check if Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Check application logs
docker logs icap-api
```

### High False Positive Rate
1. Adjust alert thresholds
2. Add hysteresis to alerts
3. Increase alert duration
4. Use composite conditions

## Best Practices

### 1. Alert Design
- Set appropriate thresholds
- Avoid alert fatigue
- Use meaningful alert names
- Include actionable information
- Set appropriate escalation levels

### 2. Dashboard Design
- Group related metrics
- Use consistent time ranges
- Include context and annotations
- Use color coding for status
- Make dashboards actionable

### 3. Monitoring Coverage
- Monitor all critical components
- Include business metrics
- Monitor security events
- Track system resources
- Monitor user experience

### 4. Alert Response
- Define runbooks for common alerts
- Assign on-call responsibilities
- Document escalation procedures
- Regular review and update alerts
- Conduct post-mortems for incidents

## Support
For monitoring and alerting issues:
- **Documentation:** See [Monitoring Guide](Docs/MONITORING_ALERTING.md)
- **Prometheus:** https://prometheus.io/docs/
- **Grafana:** https://grafana.com/docs/
- **Support:** monitoring@icap-enterprise.com
