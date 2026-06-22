# ICAP Backup Strategy

## Overview

This document outlines the comprehensive backup and recovery strategy for the Industrial Color AI Platform (ICAP) to ensure data integrity, business continuity, and disaster recovery capabilities.

## Table of Contents
- [Backup Scope](#backup-scope)
- [Backup Frequency](#backup-frequency)
- [Backup Locations](#backup-locations)
- [Backup Procedures](#backup-procedures)
- [Recovery Procedures](#recovery-procedures)
- [Retention Policy](#retention-policy)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Testing Backups](#testing-backups)

## Backup Scope

### Critical Data Components

1. **Database** (PostgreSQL/SQLite)
   - Measurements and audit trail data
   - Client configurations
   - Model registry
   - Historical color analysis data

2. **Vector Database** (Qdrant)
   - Document embeddings
   - RAG indexed content
   - Knowledge graph data

3. **Document Storage** (RAG/)
   - Source documents (PDF, DOCX, etc.)
   - Processed chunks
   - Indexer state files

4. **Model Artifacts**
   - Trained models
   - Fine-tuned weights
   - Model configurations

5. **Configuration Files**
   - Environment variables (.env)
   - Configuration files
   - SSL certificates

6. **Application Logs**
   - Application logs
   - Audit logs
   - Error logs

## Backup Frequency

### Automated Backups

| Data Type | Frequency | Retention |
|-----------|-----------|-----------|
| Database | Daily (2:00 AM) | 30 days |
| Qdrant Snapshots | Daily (3:00 AM) | 30 days |
| RAG Documents | Daily (4:00 AM) | 30 days |
| Application Logs | Daily (5:00 AM) | 7 days |
| Configuration | Weekly (Sunday) | 90 days |

### Manual Backups

- **Before major updates** - Full system backup
- **Before model training** - Model artifacts backup
- **After configuration changes** - Configuration backup

## Backup Locations

### Primary Storage

- **Local Storage**: `/backups/` on production server
- **NFS/SAN**: Network-attached storage for redundancy

### Off-site Storage

- **Cloud Storage**: AWS S3, Azure Blob, or Google Cloud Storage
- **Remote Server**: Secondary data center location
- **Tape Backup**: Long-term archival (optional)

### Backup Storage Structure

```
/backups/
├── database/
│   ├── daily/
│   │   ├── icap_db_20260620.sql
│   │   └── ...
│   └── weekly/
│       └── icap_db_week_25.sql
├── qdrant/
│   ├── snapshots/
│   │   └── snapshot_20260620/
│   └── collections/
├── rag/
│   ├── documents/
│   └── state/
├── models/
│   └── artifacts/
├── config/
│   └── .env
└── logs/
    └── archived/
```

## Backup Procedures

### Database Backup

#### PostgreSQL

```bash
#!/bin/bash
# backup_postgres.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database/daily"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker exec icap-postgres pg_dump -U icap_user icap | gzip > $BACKUP_DIR/icap_db_$DATE.sql.gz

# Remove old backups
find $BACKUP_DIR -name "icap_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Verify backup
if [ $? -eq 0 ]; then
    echo "Database backup completed successfully: icap_db_$DATE.sql.gz"
else
    echo "Database backup failed!"
    exit 1
fi
```

#### SQLite

```bash
#!/bin/bash
# backup_sqlite.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database/daily"
SOURCE_DB="AuditTrail/icap_enterprise.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
cp $SOURCE_DB $BACKUP_DIR/icap_db_$DATE.db
gzip $BACKUP_DIR/icap_db_$DATE.db

# Remove old backups
find $BACKUP_DIR -name "icap_db_*.db.gz" -mtime +30 -delete

echo "SQLite backup completed: icap_db_$DATE.db.gz"
```

### Qdrant Backup

```bash
#!/bin/bash
# backup_qdrant.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/qdrant/snapshots"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create snapshot
docker exec icap-qdrant qdrant snapshot create

# Copy snapshot to backup location
SNAPSHOT_ID=$(docker exec icap-qdrant ls /qdrant/storage/snapshots | tail -1)
docker cp icap-qdrant:/qdrant/storage/snapshots/$SNAPSHOT_ID $BACKUP_DIR/snapshot_$DATE

# Compress
tar -czf $BACKUP_DIR/snapshot_$DATE.tar.gz $BACKUP_DIR/snapshot_$DATE
rm -rf $BACKUP_DIR/snapshot_$DATE

echo "Qdrant backup completed: snapshot_$DATE.tar.gz"
```

### RAG Documents Backup

```bash
#!/bin/bash
# backup_rag.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/rag/documents"
SOURCE_DIR="RAG"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
tar -czf $BACKUP_DIR/rag_documents_$DATE.tar.gz $SOURCE_DIR

# Remove old backups
find $BACKUP_DIR -name "rag_documents_*.tar.gz" -mtime +30 -delete

echo "RAG documents backup completed: rag_documents_$DATE.tar.gz"
```

### Configuration Backup

```bash
#!/bin/bash
# backup_config.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/config"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup environment file
cp .env $BACKUP_DIR/.env_$DATE

# Backup nginx configuration
cp nginx/nginx.conf $BACKUP_DIR/nginx_$DATE.conf

# Backup SSL certificates
if [ -d nginx/ssl ]; then
    tar -czf $BACKUP_DIR/ssl_$DATE.tar.gz nginx/ssl
fi

echo "Configuration backup completed"
```

### Automated Backup Script

Create `automated_backup.sh`:

```bash
#!/bin/bash
# automated_backup.sh - Master backup script

LOG_FILE="/var/log/icap_backup.log"
DATE=$(date +%Y%m%d_%H%M%S)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "Starting automated backup process"

# Run individual backup scripts
for script in /scripts/backup_*.sh; do
    log "Running $script"
    if $script; then
        log "SUCCESS: $script"
    else
        log "FAILED: $script"
        # Send alert
        curl -X POST $SLACK_WEBHOOK_URL -d "{\"text\": \"Backup failed: $script\"}"
    fi
done

log "Automated backup process completed"
```

### Cron Configuration

```bash
# Add to crontab
0 2 * * * /scripts/backup_postgres.sh
0 3 * * * /scripts/backup_qdrant.sh
0 4 * * * /scripts/backup_rag.sh
0 5 * * * /scripts/backup_logs.sh
0 6 * * 0 /scripts/backup_config.sh
```

## Recovery Procedures

### Database Recovery

#### PostgreSQL

```bash
# Restore from backup
gunzip < /backups/database/daily/icap_db_20260620.sql.gz | docker exec -i icap-postgres psql -U icap_user icap
```

#### SQLite

```bash
# Restore from backup
gunzip -c /backups/database/daily/icap_db_20260620.db.gz > AuditTrail/icap_enterprise.db
```

### Qdrant Recovery

```bash
# Restore snapshot
docker cp /backups/qdrant/snapshots/snapshot_20260620.tar.gz icap-qdrant:/tmp/
docker exec icap-qdrant tar -xzf /tmp/snapshot_20260620.tar.gz -C /qdrant/storage/
docker restart icap-qdrant
```

### RAG Documents Recovery

```bash
# Restore documents
tar -xzf /backups/rag/documents/rag_documents_20260620.tar.gz -C ./
```

### Full System Recovery

1. **Stop all services**
```bash
docker-compose -f docker-compose.prod.yml down
```

2. **Restore database**
```bash
# Follow database recovery procedure
```

3. **Restore Qdrant**
```bash
# Follow Qdrant recovery procedure
```

4. **Restore RAG documents**
```bash
# Follow RAG recovery procedure
```

5. **Restore configuration**
```bash
cp /backups/config/.env_20260620 .env
```

6. **Start services**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

7. **Verify health**
```bash
curl http://localhost:8000/health
```

## Retention Policy

### Backup Retention

| Backup Type | Daily | Weekly | Monthly | Yearly |
|-------------|-------|--------|---------|--------|
| Database | 30 days | 12 weeks | 12 months | 5 years |
| Qdrant | 30 days | 12 weeks | 12 months | 5 years |
| RAG Documents | 30 days | 12 weeks | 12 months | 5 years |
| Logs | 7 days | 4 weeks | 12 months | 1 year |
| Configuration | 90 days | 52 weeks | 12 months | 5 years |

### Archive Strategy

- **Monthly backups**: Move to cold storage (tape or cloud archive)
- **Yearly backups**: Keep for compliance and historical analysis
- **Compliance**: Retain for required period based on regulations

## Monitoring and Alerts

### Backup Monitoring

Monitor backup success/failure:

```python
# backup_monitor.py
import requests
import logging

def check_backup_status():
    """Check if recent backups completed successfully."""
    backup_dir = "/backups/database/daily"
    latest_backup = max([f for f in os.listdir(backup_dir) if f.startswith('icap_db_')])
    
    # Check if backup is from today
    today = datetime.now().strftime("%Y%m%d")
    if today in latest_backup:
        logging.info("Backup completed successfully")
        return True
    else:
        logging.error("Backup not found for today")
        # Send alert
        send_alert("Database backup failed for today")
        return False
```

### Alert Configuration

Configure alerts for:
- Backup failures
- Backup size anomalies
- Storage space warnings
- Recovery test failures

### Storage Monitoring

Monitor backup storage usage:

```bash
# Check backup storage
du -sh /backups/*

# Alert if > 80% full
if [ $(df /backups | awk 'NR==2 {print $5}' | sed 's/%//') -gt 80 ]; then
    send_alert "Backup storage at $(df /backups | awk 'NR==2 {print $5}') capacity"
fi
```

## Testing Backups

### Monthly Recovery Tests

Perform monthly recovery tests:

1. **Select random backup** from previous month
2. **Restore to test environment**
3. **Verify data integrity**
4. **Test application functionality**
5. **Document results**

### Test Checklist

- [ ] Database can be restored
- [ ] Data integrity verified
- [ ] Application starts successfully
- [ ] API endpoints respond correctly
- [ ] RAG system functions properly
- [ ] Vision AI operations work
- [ ] No data corruption detected

### Test Report Template

```
Backup Test Report
==================
Date: YYYY-MM-DD
Backup Date: YYYY-MM-DD
Backup ID: XXXXX

Test Results:
- Database Restore: PASS/FAIL
- Data Integrity: PASS/FAIL
- Application Startup: PASS/FAIL
- API Functionality: PASS/FAIL
- RAG System: PASS/FAIL
- Vision AI: PASS/FAIL

Notes:
[Additional observations]

Recommendations:
[Any improvements needed]
```

## Disaster Recovery

### RTO (Recovery Time Objective)

- **Critical systems**: 4 hours
- **Non-critical systems**: 24 hours
- **Full system**: 48 hours

### RPO (Recovery Point Objective)

- **Database**: 24 hours (daily backup)
- **Qdrant**: 24 hours (daily backup)
- **RAG Documents**: 24 hours (daily backup)

### Disaster Recovery Plan

1. **Assess impact** and declare disaster
2. **Activate DR team** and communication plan
3. **Restore from backups** following recovery procedures
4. **Verify system integrity** and functionality
5. **Switch to DR environment** if primary is unavailable
6. **Monitor performance** and stability
7. **Document lessons learned** and update procedures

## Security Considerations

### Backup Encryption

- Encrypt backups at rest
- Use AES-256 encryption
- Store encryption keys securely (secrets manager)
- Rotate encryption keys quarterly

### Access Control

- Restrict backup access to authorized personnel
- Use role-based access control
- Audit backup access logs
- Implement MFA for backup operations

### Backup Integrity

- Calculate checksums for all backups
- Verify checksums before restore
- Use cryptographic hashing (SHA-256)
- Store checksums separately

## Best Practices

1. **3-2-1 Rule**: 3 copies, 2 different media, 1 off-site
2. **Regular Testing**: Test backups monthly
3. **Documentation**: Keep procedures updated
4. **Automation**: Automate where possible
5. **Monitoring**: Monitor backup status continuously
6. **Security**: Encrypt and protect backups
7. **Compliance**: Meet regulatory requirements
8. **Review**: Review and update strategy quarterly

## Contact Information

**Backup Team:**
- Primary: backup-admin@company.com
- Secondary: it-ops@company.com

**Emergency Contact:**
- On-call: +1-XXX-XXX-XXXX
- Pager: emergency-pager@company.com

**Vendor Support:**
- Database Support: vendor-db@company.com
- Cloud Storage: vendor-cloud@company.com
