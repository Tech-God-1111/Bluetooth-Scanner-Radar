import json
from backend.config.settings import BLOCKLIST_PATH, ensure_directories
from backend.database.blocked_sites_model import add_site, remove_site, list_sites

def sync_json_from_database():
    ensure_directories()
    BLOCKLIST_PATH.write_text(json.dumps(list_sites(), indent=2), encoding="utf-8")

def add_domain(domain, category="Uncategorized"):
    result = add_site(domain, category)
    sync_json_from_database()
    return result

def delete_domain(domain):
    remove_site(domain)
    sync_json_from_database()

def import_domains(path, category="Imported"):
    source = __import__("pathlib").Path(path)
    if source.suffix.lower() == ".json":
        data = json.loads(source.read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else data.get("websites", [])
        domains = [item["domain"] if isinstance(item, dict) else str(item) for item in entries]
    else:
        domains = [line.strip() for line in source.read_text(encoding="utf-8").splitlines()
                   if line.strip() and not line.strip().startswith("#")]
    added = 0
    for domain in domains:
        before = len(list_sites())
        add_domain(domain, category)
        added += int(len(list_sites()) > before)
    return added
