"""Read the current Windows Wi-Fi connection without inspecting other clients.

Signal percentage belongs to this PC's connection to its access point. It is
not a per-device RSSI reading and must never be converted into device distance.
"""
from datetime import datetime, timezone
import platform
import re
import subprocess


_FIELD_PATTERNS = {
    "interface_name": r"^\s*Name\s*:\s*(.+?)\s*$",
    "state": r"^\s*State\s*:\s*(.+?)\s*$",
    "ssid": r"^\s*SSID\s*:\s*(.+?)\s*$",
    "bssid": r"^\s*BSSID\s*:\s*(.+?)\s*$",
    "signal_percent": r"^\s*Signal\s*:\s*(\d+)\s*%",
    "radio_type": r"^\s*Radio type\s*:\s*(.+?)\s*$",
    "channel": r"^\s*Channel\s*:\s*(\d+)\s*$",
    "receive_rate_mbps": r"^\s*Receive rate \(Mbps\)\s*:\s*([\d.]+)",
    "transmit_rate_mbps": r"^\s*Transmit rate \(Mbps\)\s*:\s*([\d.]+)",
}


def parse_netsh_interfaces(output):
    """Parse English Windows 'netsh wlan show interfaces' output."""
    result = {}
    for field, pattern in _FIELD_PATTERNS.items():
        match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        if not match:
            result[field] = None
            continue
        value = match.group(1).strip()
        if field in {"signal_percent", "channel"}:
            result[field] = int(value)
        elif field in {"receive_rate_mbps", "transmit_rate_mbps"}:
            result[field] = float(value)
        else:
            result[field] = value

    state = (result.get("state") or "").lower()
    signal = result.get("signal_percent")
    if state == "connected" and signal is not None:
        if signal >= 75:
            quality = "Excellent"
        elif signal >= 55:
            quality = "Good"
        elif signal >= 35:
            quality = "Fair"
        else:
            quality = "Weak"
    else:
        quality = "Unavailable"

    result.update({
        "connected": state == "connected",
        "quality": quality,
        "source": "Windows netsh WLAN",
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "distance_estimation": "not_available",
    })
    return result


def get_wifi_status():
    """Return this PC's Wi-Fi link status; never infer other devices' RSSI."""
    if platform.system() != "Windows":
        return {
            "connected": False,
            "quality": "Unavailable",
            "signal_percent": None,
            "source": "Unsupported platform",
            "error": "Wi-Fi telemetry is currently implemented for Windows.",
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "distance_estimation": "not_available",
        }

    try:
        completed = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=6,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "netsh returned an error.")
        parsed = parse_netsh_interfaces(completed.stdout)
        if not parsed.get("interface_name") and not parsed.get("state"):
            parsed["error"] = "Windows did not return a readable WLAN interface."
        return parsed
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        return {
            "connected": False,
            "quality": "Unavailable",
            "signal_percent": None,
            "source": "Windows netsh WLAN",
            "error": str(exc),
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "distance_estimation": "not_available",
        }
