import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Optional
from utils.multi_tenant import TenantContext

# Default to SQLite for Edge deployments. For Cloud/Centralized installations,
# set ICAP_DATABASE_URL to a PostgreSQL connection string.
DATABASE_URL = os.environ.get("ICAP_DATABASE_URL", "AuditTrail/icap_enterprise.db")
logger = logging.getLogger("Database")

# Connection pool for better performance
_connection_pool = []
_MAX_POOL_SIZE = 5

@contextmanager
def get_db_connection():
    """Get database connection with connection pooling."""
    conn = None
    try:
        if _connection_pool:
            conn = _connection_pool.pop()
        else:
            conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
            conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Optimize SQLite for performance
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-10000")  # 10MB cache
        
        yield conn
    finally:
        if conn and len(_connection_pool) < _MAX_POOL_SIZE:
            _connection_pool.append(conn)
        elif conn:
            conn.close()

def init_enterprise_db():
    os.makedirs(os.path.dirname(DATABASE_URL), exist_ok=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Measurements Table (Migrated from audit_trail.db)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                batch_id TEXT, operator_id TEXT, machine_id TEXT, client_id TEXT,
                delta_e REAL, status TEXT, method TEXT, illuminant TEXT,
                tenant_id TEXT DEFAULT 'default'
            )
        ''')

        # Add indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_timestamp ON measurements(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_batch_id ON measurements(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_machine_id ON measurements(machine_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_client_id ON measurements(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_status ON measurements(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_tenant_id ON measurements(tenant_id)')

        # 2. Clients Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT,
                tolerance REAL,
                preferred_method TEXT,
                preferred_illuminant TEXT,
                tenant_id TEXT DEFAULT 'default'
            )
        ''')

        # Add tenant_id index for clients
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_tenant_id ON clients(tenant_id)')

        # 3. Model Registry Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                version TEXT PRIMARY KEY,
                name TEXT,
                date TEXT,
                accuracy REAL,
                status TEXT,
                tenant_id TEXT DEFAULT 'default'
            )
        ''')

        # Add index for model status queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_status ON models(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_tenant_id ON models(tenant_id)')

        # Initial Data Migration if empty
        cursor.execute('SELECT COUNT(*) FROM clients')
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO clients VALUES ('GENERAL', 'Общи изисквания', 1.0, 'CIE2000', 'D65', 'default')")

        conn.commit()
        logger.info("✅ Enterprise Database initialized with indexes and multi-tenancy support.")

def get_measurements_by_batch(batch_id: str, limit: int = 100, tenant_id: Optional[str] = None):
    """Optimized query for measurements by batch ID with tenant isolation."""
    tenant_id = tenant_id or TenantContext.get_current_tenant()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM measurements 
            WHERE batch_id = ? AND tenant_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (batch_id, tenant_id, limit))
        return cursor.fetchall()

def get_measurements_by_machine(machine_id: str, limit: int = 100, tenant_id: Optional[str] = None):
    """Optimized query for measurements by machine ID with tenant isolation."""
    tenant_id = tenant_id or TenantContext.get_current_tenant()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM measurements 
            WHERE machine_id = ? AND tenant_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (machine_id, tenant_id, limit))
        return cursor.fetchall()

def get_recent_measurements(limit: int = 100, tenant_id: Optional[str] = None):
    """Optimized query for recent measurements with tenant isolation."""
    tenant_id = tenant_id or TenantContext.get_current_tenant()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM measurements 
            WHERE tenant_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (tenant_id, limit))
        return cursor.fetchall()

def get_quality_summary(client_id: Optional[str] = None, tenant_id: Optional[str] = None):
    """Optimized query for quality summary statistics with tenant isolation."""
    tenant_id = tenant_id or TenantContext.get_current_tenant()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if client_id:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Pass' THEN 1 ELSE 0 END) as passed,
                    AVG(delta_e) as avg_delta_e,
                    MIN(delta_e) as min_delta_e,
                    MAX(delta_e) as max_delta_e
                FROM measurements 
                WHERE client_id = ? AND tenant_id = ?
            ''', (client_id, tenant_id))
        else:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Pass' THEN 1 ELSE 0 END) as passed,
                    AVG(delta_e) as avg_delta_e,
                    MIN(delta_e) as min_delta_e,
                    MAX(delta_e) as max_delta_e
                FROM measurements
                WHERE tenant_id = ?
            ''', (tenant_id,))
        
        return cursor.fetchone()

def cleanup_old_data(days_to_keep: int = 90, tenant_id: Optional[str] = None):
    """Clean up old measurements to maintain database performance with tenant isolation."""
    tenant_id = tenant_id or TenantContext.get_current_tenant()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM measurements 
            WHERE timestamp < datetime('now', '-' || ? || ' days') AND tenant_id = ?
        ''', (days_to_keep, tenant_id))
        deleted = cursor.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted} old measurements for tenant {tenant_id} (older than {days_to_keep} days)")
        return deleted

def insert_measurement(measurement_data: dict, tenant_id: Optional[str] = None):
    """Insert a measurement record with tenant isolation."""
    tenant_id = tenant_id or TenantContext.get_current_tenant()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO measurements 
            (timestamp, batch_id, operator_id, machine_id, client_id, delta_e, status, method, illuminant, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            measurement_data.get('timestamp'),
            measurement_data.get('batch_id'),
            measurement_data.get('operator_id'),
            measurement_data.get('machine_id'),
            measurement_data.get('client_id'),
            measurement_data.get('delta_e'),
            measurement_data.get('status'),
            measurement_data.get('method'),
            measurement_data.get('illuminant'),
            tenant_id
        ))
        conn.commit()
        return cursor.lastrowid
