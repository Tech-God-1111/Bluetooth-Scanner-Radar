from backend.database.device_model import list_devices, set_trust
from backend.database.logs_model import record_event

def get_devices():
    return list_devices()

def update_trust(device_id, status):
    set_trust(device_id, status)
    record_event("trust_changed", f"Device {device_id} trust status changed to {status}")
