from datetime import datetime, timezone
from backend.database.db import connect

def record_event(event_type, message):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        conn.execute("INSERT INTO network_events(event_type,message,created_at) VALUES(?,?,?)",
                     (event_type, message, now))

def recent_events(limit=100):
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM network_events ORDER BY id DESC LIMIT ?", (limit,))]
