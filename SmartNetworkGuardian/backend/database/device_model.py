from datetime import datetime, timezone
from backend.database.db import connect

def upsert_device(ip, mac=None, hostname=None, vendor=None):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM devices WHERE ip_address=? AND COALESCE(mac_address,'')=COALESCE(?, '')",
            (ip, mac)).fetchone()
        if row:
            device_id = row["id"]
            conn.execute("""UPDATE devices SET hostname=COALESCE(?,hostname),
                vendor=COALESCE(?,vendor), last_seen=?, status='online'
                WHERE id=?""", (hostname, vendor, now, device_id))
        else:
            cur = conn.execute("""INSERT INTO devices
                (ip_address,mac_address,hostname,vendor,first_seen,last_seen,status)
                VALUES(?,?,?,?,?,?, 'online')""", (ip,mac,hostname,vendor,now,now))
            device_id = cur.lastrowid
            conn.execute("INSERT INTO network_events(event_type,message,created_at) VALUES(?,?,?)",
                         ("new_device", f"New device detected: {ip}", now))
        conn.execute("INSERT INTO device_history(device_id,observed_at,ip_address,status) VALUES(?,?,?,'online')",
                     (device_id,now,ip))
        return device_id

def list_devices():
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM devices ORDER BY last_seen DESC")]

def set_trust(device_id, trust_status):
    if trust_status not in {"trusted", "unknown", "ignored"}:
        raise ValueError("Invalid trust status")
    with connect() as conn:
        conn.execute("UPDATE devices SET trust_status=? WHERE id=?", (trust_status, device_id))
