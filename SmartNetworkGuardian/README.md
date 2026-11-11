# Smart Network Guardian

A Windows-oriented local network inventory and monitoring desktop application built with Python and PyQt6.

## Current features
- Native PyQt6 application launched with `python main.py`.
- SQLite device inventory, device observations, events and network metrics.
- Manual ARP discovery on one explicitly selected private IPv4 subnet.
- Private-subnet and maximum-address-count validation.
- Device inventory with IP, MAC, hostname, first/last-seen and trust status.
- Local website blocklist stored in SQLite and mirrored to JSON.
- Default gateway discovery and DNS health measurement modules.
- CSV device inventory and PDF event exports.
- Router capability boundary that reports unsupported status instead of claiming filtering is active.

## Limitations
- Scapy discovery may require administrator privileges and a compatible packet capture driver on Windows.
- ARP discovery only sees devices that respond; it cannot prove silent devices are offline.
- Vendor enrichment, continuous monitoring UI, automatic scheduling and verified router adapters are not enabled in this initial release.
- A local blocklist does not block websites by itself.
- No router settings are changed.
- No ESP32 data is simulated.

## Install (Windows 11)
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

4. If Scapy cannot capture packets, install the appropriate Npcap driver and retry with suitable permissions.

## Data
Application records are stored locally in `data/devices.db` and `data/blocked_sites.json`. Scanning is manual, requires selecting a private IPv4 interface and asks for confirmation. No external network scanning is implemented.

## Tests
Run `pytest` from this directory. Keep network and router tests mocked; tests must not change router configuration.

## Roadmap
Scheduled monitoring, historical graphs, vendor lookup, additional report types, verified router-specific adapters and optional ESP32-S3 telemetry.
