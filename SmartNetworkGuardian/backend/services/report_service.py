import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from backend.database.device_model import list_devices
from backend.database.logs_model import recent_events
from backend.config.settings import REPORT_DIR, ensure_directories

def export_devices_csv():
    ensure_directories()
    path = REPORT_DIR / "exports" / "device_inventory.csv"
    rows = list_devices()
    fields = list(rows[0].keys()) if rows else ["id","ip_address","mac_address","hostname","vendor","first_seen","last_seen","status","trust_status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path

def export_events_pdf():
    ensure_directories()
    path = REPORT_DIR / "exports" / "network_events.pdf"
    doc = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 50
    doc.setFont("Helvetica-Bold", 16)
    doc.drawString(40, y, "Smart Network Guardian - Network Events")
    y -= 30
    doc.setFont("Helvetica", 9)
    for event in recent_events(100):
        if y < 45:
            doc.showPage()
            y = height - 45
            doc.setFont("Helvetica", 9)
        doc.drawString(40, y, f"{event['created_at']} | {event['event_type']} | {event['message']}"[:125])
        y -= 15
    doc.save()
    return path
