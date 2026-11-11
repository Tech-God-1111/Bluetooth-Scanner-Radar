from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"
LOG_DIR = ROOT / "backend" / "logs"
DB_PATH = DATA_DIR / "devices.db"
BLOCKLIST_PATH = DATA_DIR / "blocked_sites.json"
TRUSTED_PATH = DATA_DIR / "trusted_devices.json"
SETTINGS_PATH = DATA_DIR / "settings.json"
DEFAULT_CONFIG = ROOT / "backend" / "config" / "config.json"

def ensure_directories():
    for path in (DATA_DIR, REPORT_DIR / "daily", REPORT_DIR / "weekly",
                 REPORT_DIR / "exports", LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
    for path, default in ((BLOCKLIST_PATH, []), (TRUSTED_PATH, []),
                          (SETTINGS_PATH, {"scan_interval_seconds": 60})):
        if not path.exists():
            path.write_text(json.dumps(default, indent=2), encoding="utf-8")
