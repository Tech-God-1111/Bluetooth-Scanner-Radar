from backend.database.db import initialize_database
from backend.database.device_model import upsert_device, list_devices

def test_device_inventory_round_trip(tmp_path, monkeypatch):
    import backend.database.db as db
    import backend.database.device_model as model
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(model, "connect", db.connect)
    initialize_database()
    upsert_device("192.168.1.10", "aa:bb:cc:dd:ee:ff", "test-host")
    rows = list_devices()
    assert len(rows) == 1
    assert rows[0]["ip_address"] == "192.168.1.10"
