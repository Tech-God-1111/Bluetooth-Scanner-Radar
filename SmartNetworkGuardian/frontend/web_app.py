import threading
import time
from flask import Flask, jsonify, render_template, request, send_file
from backend.database.device_model import list_devices, set_trust
from backend.database.blocked_sites_model import list_sites
from backend.database.logs_model import recent_events, record_event
from backend.scanner.network_scanner import discover_local_devices, validate_private_network
from backend.scanner.device_detector import ingest_scan_results
from backend.router.router_manager import active_ipv4_interfaces, detect_default_gateway
from backend.services.monitoring_service import collect_health
from backend.services.wifi_service import get_wifi_status
from backend.services.website_service import add_domain, delete_domain
from backend.services.report_service import export_devices_csv, export_events_pdf

_scan_lock = threading.Lock()
_scan_state = {"running": False, "message": "Ready", "last_count": 0}
_wifi_history = []
_last_wifi_history_at = 0.0


def _wifi_snapshot():
    """Collect this PC's Wi-Fi link data and retain a small in-memory history."""
    global _last_wifi_history_at
    wifi = get_wifi_status()
    now = time.monotonic()
    signal = wifi.get("signal_percent")
    if wifi.get("connected") and isinstance(signal, int) and now - _last_wifi_history_at >= 15:
        _wifi_history.append({
            "signal_percent": signal,
            "quality": wifi.get("quality"),
            "measured_at": wifi.get("measured_at"),
        })
        del _wifi_history[:-60]
        _last_wifi_history_at = now
    wifi["history"] = list(_wifi_history)
    return wifi


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.get("/")
    def dashboard():
        return render_template("index.html")

    @app.get("/api/overview")
    def overview():
        devices = list_devices()
        return jsonify({
            "devices": devices, "events": recent_events(12),
            "total_devices": len(devices),
            "trusted_devices": sum(d["trust_status"] == "trusted" for d in devices),
            "unknown_devices": sum(d["trust_status"] == "unknown" for d in devices),
            "gateway": detect_default_gateway(),
            "interfaces": active_ipv4_interfaces(), "scan": dict(_scan_state)
        })

    @app.get("/api/radar")
    def radar_data():
        devices = list_devices()
        return jsonify({
            "devices": devices,
            "gateway": detect_default_gateway(),
            "scan": dict(_scan_state),
            "wifi": _wifi_snapshot(),
            "position_semantics": "visual_layout_only_not_physical_distance",
        })

    @app.get("/api/wifi")
    def wifi_data():
        return jsonify(_wifi_snapshot())

    @app.get("/api/devices")
    def devices():
        return jsonify(list_devices())

    @app.post("/api/devices/<int:device_id>/trust")
    def trust_device(device_id):
        status = (request.json or {}).get("status", "unknown")
        try:
            set_trust(device_id, status)
            record_event("trust_changed", f"Device {device_id} trust status changed to {status}")
            return jsonify({"ok": True})
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.get("/api/interfaces")
    def interfaces():
        return jsonify(active_ipv4_interfaces())

    @app.post("/api/scan")
    def start_scan():
        payload = request.json or {}
        cidr = payload.get("cidr", "")
        try:
            network = validate_private_network(cidr)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        if not _scan_lock.acquire(blocking=False):
            return jsonify({"error": "A scan is already running."}), 409
        _scan_state.update(running=True, message=f"Scanning {network}", last_count=0)

        def worker():
            try:
                results = discover_local_devices(str(network))
                ingest_scan_results(results)
                _scan_state.update(message=f"Scan complete: {len(results)} responding devices", last_count=len(results))
                record_event("scan_complete", f"Manual ARP scan of {network}: {len(results)} responding devices")
            except Exception as exc:
                _scan_state.update(message=f"Scan failed: {exc}")
                record_event("scan_failed", str(exc))
            finally:
                _scan_state["running"] = False
                _scan_lock.release()

        threading.Thread(target=worker, daemon=True).start()
        return jsonify({"ok": True, "message": "Scan started"})

    @app.get("/api/scan/status")
    def scan_status():
        return jsonify(_scan_state)

    @app.get("/api/health")
    def health():
        gateway = detect_default_gateway()
        try:
            return jsonify(collect_health(gateway))
        except Exception as exc:
            return jsonify({"error": str(exc), "gateway": gateway}), 500

    @app.get("/api/sites")
    def sites():
        return jsonify(list_sites())

    @app.post("/api/sites")
    def add_site_route():
        payload = request.json or {}
        try:
            domain = add_domain(payload.get("domain", ""), payload.get("category", "Uncategorized"))
            record_event("blocklist_updated", f"Added {domain} to local website list")
            return jsonify({"ok": True, "domain": domain})
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.delete("/api/sites")
    def remove_site_route():
        domain = (request.json or {}).get("domain", "")
        delete_domain(domain)
        record_event("blocklist_updated", f"Removed {domain} from local website list")
        return jsonify({"ok": True})

    @app.get("/api/reports/devices.csv")
    def devices_csv():
        return send_file(export_devices_csv(), as_attachment=True)

    @app.get("/api/reports/events.pdf")
    def events_pdf():
        return send_file(export_events_pdf(), as_attachment=True)

    return app
