from backend.database.device_model import upsert_device, list_devices

def ingest_scan_results(devices):
    for device in devices:
        upsert_device(device["ip_address"], device.get("mac_address"),
                      device.get("hostname"), device.get("vendor"))
    return list_devices()
