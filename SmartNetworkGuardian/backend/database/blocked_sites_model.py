from datetime import datetime, timezone
from backend.database.db import connect

def list_sites():
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM blocked_websites ORDER BY domain")]

def add_site(domain, category="Uncategorized"):
    domain = domain.strip().lower().rstrip(".")
    if not domain or "/" in domain or " " in domain or "." not in domain:
        raise ValueError("Enter a valid domain such as example.com")
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO blocked_websites(domain,category,created_at) VALUES(?,?,?)",
                     (domain, category, now))
    return domain

def remove_site(domain):
    with connect() as conn:
        conn.execute("DELETE FROM blocked_websites WHERE domain=?", (domain,))
