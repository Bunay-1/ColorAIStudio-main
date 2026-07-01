-- ICAP Database Schema (v0.2.8)
-- SQLite compatible schema

-- 1. Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT UNIQUE NOT NULL,
    tenant_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL,
    tenant_id TEXT DEFAULT 'default',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- 3. Clients table
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    contact_person TEXT,
    email TEXT,
    tolerance REAL DEFAULT 1.0,
    tenant_id TEXT DEFAULT 'default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- 4. Measurements table
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    operator_id TEXT,
    machine_id TEXT,
    client_id TEXT,
    delta_e REAL,
    status TEXT,
    method TEXT DEFAULT 'CIE2000',
    lab_sample TEXT, -- JSON array
    lab_standard TEXT, -- JSON array
    tenant_id TEXT DEFAULT 'default',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- 5. Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT NOT NULL,
    resource TEXT,
    details TEXT,
    tenant_id TEXT DEFAULT 'default',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default tenant
INSERT OR IGNORE INTO tenants (tenant_id, tenant_name) VALUES ('default', 'Default Organization');
