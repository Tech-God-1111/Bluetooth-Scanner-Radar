# Smart Network Guardian

A local-first Windows network monitoring web application. The Python backend runs on your PC and the dashboard opens in your browser at http://127.0.0.1:5000.

## Interface
The dashboard uses the supplied off-white, pale blue-grey, medium blue and deep navy palette. It includes overview, device inventory, website list and report exports.

## Features
- Local Flask web server; no PyQt desktop window.
- SQLite device inventory, observations, events and network metrics.
- Manual ARP discovery on one explicitly selected private IPv4 subnet.
- Private-subnet and maximum-address-count validation (4096 addresses).
- Device inventory and user-managed trust status.
- Local website domain list stored in SQLite and mirrored to JSON.
- Gateway discovery and DNS/gateway health check.
- CSV device inventory and PDF event exports.
- Router capability boundary: no router settings are changed and no claim of active website filtering is made.

## Windows installation
1. Install Python 3.11+.
2. Open PowerShell in this directory.
3. Run:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python main.py
   ```

4. Open http://127.0.0.1:5000 in your browser. Keep the terminal open while using the dashboard.
5. If ARP discovery fails on Windows, install Npcap and run the terminal with appropriate permissions.

## Security and limitations
- The web server binds to 127.0.0.1, so it is accessible only from this PC by default.
- Scans are manual, require selecting an active interface and confirmation, and are restricted to one private IPv4 subnet.
- ARP discovery only sees devices that respond; a missing response does not prove a device is offline.
- The website list is local bookkeeping only. It does not block websites without a separately implemented and verified router/DNS enforcement adapter.
- No router settings are changed. No internet-wide scans, password attacks, packet injection or traffic interception are implemented.
- Device vendor enrichment, continuous monitoring, bandwidth measurement, historical charting and ESP32-S3 telemetry are not implemented.

## Tests
Run pytest from this directory. Network discovery and router operations should be mocked in automated tests.

## Radar dashboard and Wi-Fi telemetry
- The overview includes an animated discovery radar that plots devices returned by the existing manual ARP scan.
- Marker positions are deterministic visual placements only. Rings and marker positions do not represent physical distance, direction, or a floor plan.
- The Wi-Fi panel reads the current Windows PC-to-access-point connection using `netsh wlan show interfaces`: SSID, BSSID, signal percentage, channel, radio type, and reported link rates when available.
- Signal history is sampled in memory while the dashboard is open; it is not a persistent long-term measurement history.
- The Wi-Fi signal belongs to this PC's connection. It is not the RSSI of other LAN devices and is never converted into per-device distance.
- Individual device proximity requires an authorized source of per-client radio measurements (for example, supported router telemetry or compatible receiver hardware). This build does not claim to provide that.
