from backend.scanner.ping_monitor import ping_host
from backend.scanner.dns_health import check_dns
from backend.database.db import connect
from datetime import datetime, timezone

def collect_health(gateway=None):
    results = {"gateway": None, "dns": check_dns()}
    if gateway:
        results["gateway"] = ping_host(gateway)
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        if results["gateway"]:
            conn.execute("INSERT INTO network_metrics(metric_name,metric_value,unit,measured_at) VALUES(?,?,?,?)",
                         ("gateway_latency", results["gateway"]["elapsed_ms"], "ms", now))
        conn.execute("INSERT INTO network_metrics(metric_name,metric_value,unit,measured_at) VALUES(?,?,?,?)",
                     ("dns_response", results["dns"]["elapsed_ms"], "ms", now))
    return results
