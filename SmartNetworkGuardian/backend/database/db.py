import sqlite3
from contextlib import contextmanager
from backend.config.settings import DB_PATH, ensure_directories

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS devices (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 ip_address TEXT NOT NULL,
 mac_address TEXT,
 hostname TEXT,
 vendor TEXT,
 first_seen TEXT NOT NULL,
 last_seen TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'online',
 trust_status TEXT NOT NULL DEFAULT 'unknown',
 UNIQUE(mac_address, ip_address)
);
CREATE TABLE IF NOT EXISTS device_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
 observed_at TEXT NOT NULL,
 ip_address TEXT,
 status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS network_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_type TEXT NOT NULL,
 message TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS network_metrics (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 metric_name TEXT NOT NULL,
 metric_value REAL,
 unit TEXT,
 measured_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS blocked_websites (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 domain TEXT NOT NULL UNIQUE,
 category TEXT NOT NULL DEFAULT 'Uncategorized',
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS system_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 level TEXT NOT NULL,
 message TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS router_configs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 display_name TEXT NOT NULL,
 gateway_ip TEXT,
 adapter_name TEXT,
 capabilities_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS router_sync_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 status TEXT NOT NULL,
 details TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_metrics_time ON network_metrics(measured_at);
CREATE INDEX IF NOT EXISTS idx_history_device_time ON device_history(device_id, observed_at);
"""

@contextmanager
def connect():
    ensure_directories()
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize_database():
    with connect() as conn:
        conn.executescript(SCHEMA)
