# Disaster Recovery Procedures
==============================

## Overview
ICAP v8.9.5 Enterprise includes comprehensive disaster recovery procedures for business continuity. This guide covers backup strategies, recovery procedures, and incident response.

## Backup Strategy

### Backup Types
1. **Full Backup:** Complete system backup
2. **Incremental Backup:** Changes since last backup
3. **Differential Backup:** Changes since last full backup
4. **Snapshot Backup:** Point-in-time system state

### Backup Schedule
| Type | Frequency | Retention | Location |
|------|-----------|-----------|----------|
| Database Full | Daily | 30 days | Local + Cloud |
| Database Incremental | Hourly | 7 days | Local |
| Configuration | Daily | 90 days | Cloud |
| Application Files | Weekly | 30 days | Cloud |
| Audit Logs | Daily | 365 days | Cloud |

### Database Backup

#### SQLite Backup
```bash
# Manual backup
cp AuditTrail/icap_enterprise.db AuditTrail/backups/icap_$(date +%Y%m%d_%H%M%S).db

# Automated backup script
#!/bin/bash
BACKUP_DIR="AuditTrail/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp AuditTrail/icap_enterprise.db $BACKUP_DIR/icap_$DATE.db

# Keep only last 30 backups
find $BACKUP_DIR -name "icap_*.db" -mtime +30 -delete
```

#### PostgreSQL Backup
```bash
# Full backup
pg_dump -U postgres -h localhost icap_db > backup_$(date +%Y%m%d).sql

# Incremental backup
pg_dump -U postgres -h localhost --schema-only icap_db > schema_$(date +%Y%m%d).sql

# Restore
psql -U postgres -h localhost icap_db < backup_20260620.sql
```

### Configuration Backup
```bash
# Backup environment variables
env > env_backup_$(date +%Y%m%d).txt

# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  .env \
  nginx/nginx.conf \
  k8s/icap-deployment.yaml
```

### Application Files Backup
```bash
# Backup RAG documents
tar -czf rag_backup_$(date +%Y%m%d).tar.gz RAG/

# Backup audit logs
tar -czf audit_backup_$(date +%Y%m%d).tar.gz AuditTrail/

# Backup vision models
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/
```

### Cloud Backup
```bash
# Upload to AWS S3
aws s3 sync AuditTrail/backups/ s3://icap-backups/database/
aws s3 sync config_backup_*.tar.gz s3://icap-backups/config/
aws s3 sync rag_backup_*.tar.gz s3://icap-backups/rag/

# Upload to Azure Blob Storage
az storage blob upload-batch --destination icap-backups --source AuditTrail/backups/
```

## Recovery Procedures

### Database Recovery

#### SQLite Recovery
```bash
# Stop application
docker-compose down

# Restore from backup
cp AuditTrail/backups/icap_20260620_120000.db AuditTrail/icap_enterprise.db

# Verify integrity
sqlite3 AuditTrail/icap_enterprise.db "PRAGMA integrity_check;"

# Restart application
docker-compose up -d
```

#### PostgreSQL Recovery
```bash
# Stop application
docker-compose down

# Restore from backup
psql -U postgres -h localhost icap_db < backup_20260620.sql

# Verify data
psql -U postgres -h localhost icap_db -c "SELECT COUNT(*) FROM measurements;"

# Restart application
docker-compose up -d
```

### Configuration Recovery
```bash
# Restore environment variables
cat env_backup_20260620.txt > .env

# Restore configuration files
tar -xzf config_backup_20260620.tar.gz

# Restart services
docker-compose restart
```

### Application Recovery
```bash
# Restore RAG documents
tar -xzf rag_backup_20260620.tar.gz -C /

# Re-index RAG system
curl -X POST http://localhost:8000/rag/reindex \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Disaster Scenarios

### Scenario 1: Database Corruption
**Symptoms:**
- Application errors accessing database
- Data inconsistency
- Slow query performance

**Recovery Steps:**
1. Stop application
2. Identify corruption point
3. Restore from last known good backup
4. Verify data integrity
5. Restart application
6. Monitor for issues

### Scenario 2: Server Failure
**Symptoms:**
- Server not responding
- Application unreachable
- Network connectivity issues

**Recovery Steps:**
1. Assess server status
2. If hardware failure, replace hardware
3. Restore from backup on new server
4. Update DNS if needed
5. Verify application functionality
6. Monitor performance

### Scenario 3: Data Loss
**Symptoms:**
- Missing records
- Incomplete data
- Accidental deletion

**Recovery Steps:**
1. Identify extent of data loss
2. Determine point of failure
3. Restore from appropriate backup
4. Reapply changes since backup
5. Verify data integrity
6. Document incident

### Scenario 4: Security Breach
**Symptoms:**
- Unauthorized access
- Suspicious activity
- Data exfiltration

**Recovery Steps:**
1. Isolate affected systems
2. Change all credentials
3. Review audit logs
4. Patch vulnerabilities
5. Restore from clean backup
6. Implement additional security measures

### Scenario 5: Application Crash
**Symptoms:**
- Application not starting
- Frequent crashes
- Error logs

**Recovery Steps:**
1. Review error logs
2. Identify root cause
3. Apply fixes
4. Restart application
5. Monitor stability
6. Update documentation

## Incident Response

### Incident Classification
| Severity | Response Time | Recovery Time |
|----------|---------------|---------------|
| Critical | 15 min | 4 hours |
| High | 1 hour | 8 hours |
| Medium | 4 hours | 24 hours |
| Low | 24 hours | 72 hours |

### Incident Response Team
- **Incident Commander:** Overall coordination
- **Technical Lead:** Technical resolution
- **Security Lead:** Security assessment
- **Communications:** Stakeholder communication
- **Documentation:** Incident documentation

### Incident Response Process
1. **Detection:** Identify incident
2. **Assessment:** Evaluate impact and severity
3. **Containment:** Limit damage
4. **Eradication:** Remove threat
5. **Recovery:** Restore services
6. **Lessons Learned:** Document and improve

### Communication Plan
- **Internal:** Team notification within 15 minutes
- **Stakeholders:** Status updates every hour
- **Customers:** Communication based on impact
- **Public:** If required by regulations

## High Availability Setup

### Load Balancing
```yaml
# nginx.conf
upstream icap_backend {
    least_conn;
    server icap-1:8000 weight=5;
    server icap-2:8000 weight=5;
    server icap-3:8000 weight=5;
}

server {
    listen 80;
    location / {
        proxy_pass http://icap_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Database Replication
```yaml
# docker-compose.yml
services:
  postgres-primary:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=master
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD=password
  
  postgres-replica:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_HOST=postgres-primary
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD=password
```

### Multi-Region Deployment
```yaml
# Deploy to multiple regions
regions:
  - us-east-1
  - eu-west-1
  - ap-southeast-1

# Use DNS for failover
dns:
  type: round-robin
  health_check: true
  failover: automatic
```

## Testing Recovery Procedures

### Backup Verification
```bash
# Test backup integrity
sqlite3 AuditTrail/backups/icap_20260620.db "PRAGMA integrity_check;"

# Test restore to staging
cp AuditTrail/backups/icap_20260620.db /staging/icap_enterprise.db
```

### Disaster Recovery Drill
1. Schedule quarterly drills
2. Simulate different disaster scenarios
3. Practice recovery procedures
4. Document lessons learned
5. Update procedures based on findings

### Recovery Time Objective (RTO)
- **Database:** 1 hour
- **Application:** 2 hours
- **Configuration:** 30 minutes
- **Full System:** 4 hours

### Recovery Point Objective (RPO)
- **Database:** 1 hour
- **Configuration:** 24 hours
- **Audit Logs:** 24 hours
- **Application Files:** 7 days

## Monitoring and Alerting

### Backup Monitoring
```python
# Monitor backup success
def check_backup_status():
    latest_backup = get_latest_backup()
    if not latest_backup:
        send_alert("Backup failed - no recent backup found")
    elif latest_backup.age > 25 hours:
        send_alert("Backup overdue - last backup is old")
```

### Recovery Metrics
- **Backup Success Rate:** > 99%
- **Recovery Success Rate:** > 95%
- **RTO Compliance:** < 4 hours
- **RPO Compliance:** < 1 hour

### Alert Configuration
```yaml
alerts:
  - name: Backup Failed
    condition: backup_status == "failed"
    severity: critical
    notification: [slack, email, sms]
  
  - name: Backup Overdue
    condition: backup_age > 25 hours
    severity: high
    notification: [slack, email]
  
  - name: Recovery Failed
    condition: recovery_status == "failed"
    severity: critical
    notification: [slack, email, sms]
```

## Documentation

### Incident Report Template
```markdown
# Incident Report

## Summary
- **Date:** [Date]
- **Time:** [Time]
- **Severity:** [Severity]
- **Duration:** [Duration]

## Impact
- **Affected Systems:** [Systems]
- **User Impact:** [Impact]
- **Data Loss:** [Data loss if any]

## Timeline
- [Time]: [Event]
- [Time]: [Event]

## Root Cause
[Root cause analysis]

## Resolution
[Resolution steps]

## Lessons Learned
[Lessons learned and improvements]
```

### Runbook Template
```markdown
# [Procedure Name] Runbook

## Purpose
[Purpose of procedure]

## Prerequisites
- [Prerequisite 1]
- [Prerequisite 2]

## Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Verification
[How to verify success]

## Rollback
[How to rollback if needed]

## References
- [Related documentation]
- [Contact information]
```

## Best Practices

### Backup Best Practices
1. **3-2-1 Rule:** 3 copies, 2 different media, 1 offsite
2. **Regular Testing:** Test backups regularly
3. **Encryption:** Encrypt sensitive backups
4. **Versioning:** Keep multiple backup versions
5. **Automation:** Automate backup processes

### Recovery Best Practices
1. **Documentation:** Document all procedures
2. **Testing:** Regularly test recovery procedures
3. **Communication:** Clear communication during incidents
4. **Post-Mortem:** Learn from incidents
5. **Continuous Improvement:** Update procedures regularly

### High Availability Best Practices
1. **Redundancy:** Eliminate single points of failure
2. **Monitoring:** Comprehensive monitoring and alerting
3. **Load Balancing:** Distribute load across instances
4. **Failover:** Automatic failover mechanisms
5. **Testing:** Regular failover testing

## Support

### Emergency Contacts
- **On-Call Engineer:** +1-555-ONCALL
- **Incident Commander:** +1-555-INCIDENT
- **Security Team:** +1-555-SECURITY
- **Management:** +1-555-MANAGEMENT

### Documentation
- **Backup Strategy:** See [Backup Strategy](Docs/BACKUP_STRATEGY.md)
- **Performance Tuning:** See [Performance Tuning](Docs/PERFORMANCE_TUNING.md)
- **Monitoring:** See [Monitoring Guide](Docs/MONITORING_ALERTING.md)

### Support Channels
- **Email:** support@icap-enterprise.com
- **Slack:** #icap-support
- **Phone:** +1-555-SUPPORT
- **Emergency:** +1-555-EMERGENCY

## Compliance

### ISO 9001 Requirements
- Documented procedures
- Regular testing
- Continuous improvement
- Management review

### GDPR Requirements
- Data protection measures
- Breach notification
- Data retention policies
- Right to be forgotten

### Industry Regulations
- Audit trail maintenance
- Data integrity verification
- Regular compliance audits
- Documentation of procedures
