import subprocess
import json
import time
import threading
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
import platform
import os
import math
import random

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bluetooth_radar.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class BluetoothRadar:
    def __init__(self):
        self.system = platform.system()
        self.devices = {}
        self.scanning = False
        self.scan_history = []
        self.max_history = 100

        logger.info(f"Bluetooth Radar initialized on {self.system}")
        logger.info(f"System: {platform.platform()}")

    def run_powershell(self, command):
        """Run PowerShell command safely"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result
        except subprocess.TimeoutExpired:
            logger.warning("⏱️ PowerShell command timed out")
            return None
        except Exception as e:
            logger.error(f"❌ PowerShell error: {e}")
            return None

    def get_system_bluetooth_info(self):
        """Get comprehensive Bluetooth system info"""
        logger.info("🖥️ Getting system Bluetooth information...")

        cmd = '''
        $info = @{}

        # Get Bluetooth services
        $services = Get-Service -Name "*bluetooth*" -ErrorAction SilentlyContinue
        $info.Services = @()
        foreach ($service in $services) {
            $info.Services += [PSCustomObject]@{
                Name = $service.Name
                DisplayName = $service.DisplayName
                Status = $service.Status
                StartType = $service.StartType
            }
        }

        # Get Bluetooth adapters
        $adapters = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue
        $info.Adapters = @()
        foreach ($adapter in $adapters) {
            $info.Adapters += [PSCustomObject]@{
                Name = $adapter.FriendlyName
                Status = $adapter.Status
                Problem = $adapter.Problem
                Class = $adapter.Class
            }
        }

        # Get Windows Bluetooth settings
        $info.BluetoothEnabled = $false
        try {
            $btSettings = Get-WmiObject -Namespace "root\cimv2" -Class Win32_PnPEntity | 
                         Where-Object {$_.PNPClass -eq "Bluetooth"}
            $info.BluetoothEnabled = ($btSettings -ne $null)
        } catch { }

        # Convert to JSON
        $info | ConvertTo-Json -Depth 3
        '''

        result = self.run_powershell(cmd)
        if result and result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except:
                logger.warning("⚠️ Could not parse system info")

        return None

    def scan_bluetooth_devices(self):
        """Scan for real Bluetooth devices with detailed info"""
        logger.info("🔍 Scanning for Bluetooth devices...")

        devices_found = {}

        # Method 1: Get paired devices using Windows Bluetooth APIs
        cmd_paired = '''
        # Get paired Bluetooth devices using Windows.Devices.Enumeration
        try {
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
                $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
            })[0]

            Function Await($WinRtTask, $ResultType) {
                $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                $netTask = $asTask.Invoke($null, @($WinRtTask))
                $netTask.Wait(-1) | Out-Null
                $netTask.Result
            }

            [Windows.Devices.Enumeration.DeviceInformation, Windows.Devices.Enumeration, ContentType = WindowsRuntime] | Out-Null
            $selector = "(System.Devices.Aep.ProtocolId:=\\"{e0cbf06c-cd8b-4647-bb8a-263b43f0f974}\\")"
            $deviceInfo = Await ([Windows.Devices.Enumeration.DeviceInformation]::FindAllAsync($selector)) ([Windows.Devices.Enumeration.DeviceInformation])

            $devices = @()
            foreach ($device in $deviceInfo) {
                $props = $device.Properties
                $deviceObj = [PSCustomObject]@{
                    Name = $device.Name
                    Address = $props["System.Devices.Aep.DeviceAddress"]
                    IsConnected = if ($props["System.Devices.Aep.IsConnected"]) { $true } else { $false }
                    IsPaired = if ($props["System.Devices.Aep.IsPaired"]) { $true } else { $false }
                    SignalStrength = if ($props["System.Devices.Aep.SignalStrength"]) { $props["System.Devices.Aep.SignalStrength"] } else { 0 }
                    LastSeen = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                }
                $devices += $deviceObj
            }
            $devices | ConvertTo-Json
        }
        catch {
            # Fallback to Device Manager
            $devices = @()
            $btDevices = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue
            foreach ($device in $btDevices) {
                if ($device.Status -eq 'OK') {
                    $deviceObj = [PSCustomObject]@{
                        Name = $device.FriendlyName
                        Address = $device.InstanceId
                        IsConnected = ($device.Status -eq 'OK')
                        IsPaired = $true
                        SignalStrength = 50  # Default
                        LastSeen = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    }
                    $devices += $deviceObj
                }
            }
            $devices | ConvertTo-Json
        }
        '''

        # Method 2: Get connected audio devices (headphones, speakers)
        cmd_audio = '''
        # Get Bluetooth audio devices
        $audioDevices = Get-PnpDevice -Class AudioEndpoint | Where-Object {
            $_.FriendlyName -like "*Bluetooth*" -or $_.FriendlyName -like "*BT*"
        }

        $devices = @()
        foreach ($device in $audioDevices) {
            if ($device.Status -eq 'OK') {
                $deviceObj = [PSCustomObject]@{
                    Name = $device.FriendlyName
                    Address = "AUDIO_" + [Guid]::NewGuid().ToString().Substring(0,8).ToUpper()
                    IsConnected = $true
                    IsPaired = $true
                    SignalStrength = 60  # Good for connected audio
                    LastSeen = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                }
                $devices += $deviceObj
            }
        }
        $devices | ConvertTo-Json
        '''

        # Execute both scans
        for cmd, scan_type in [(cmd_paired, "paired"), (cmd_audio, "audio")]:
            result = self.run_powershell(cmd)
            if result and result.returncode == 0 and result.stdout.strip():
                try:
                    devices = json.loads(result.stdout)
                    if not isinstance(devices, list):
                        devices = [devices]

                    for device in devices:
                        address = device.get('Address', '').upper()
                        name = device.get('Name', 'Unknown Device')

                        if address and address not in devices_found:
                            # Format MAC address
                            if len(address) == 12 and ':' not in address:
                                address = ':'.join([address[i:i + 2] for i in range(0, 12, 2)])

                            # Get signal strength and calculate distance
                            signal_strength = device.get('SignalStrength', 50)
                            rssi = -100 + (signal_strength * 2)  # Convert to RSSI
                            distance = self.calculate_distance(rssi)

                            device_info = {
                                'address': address,
                                'name': name,
                                'type': self.detect_device_type(name),
                                'rssi': int(rssi),
                                'signal_quality': self.get_signal_quality(rssi),
                                'distance': distance,
                                'is_connected': device.get('IsConnected', False),
                                'is_paired': device.get('IsPaired', False),
                                'strength': min(100, max(0, 100 + rssi)),
                                'last_seen': datetime.now().isoformat(),
                                'first_seen': self.devices.get(address, {}).get('first_seen',
                                                                                datetime.now().isoformat()),
                                'scan_method': scan_type
                            }

                            devices_found[address] = device_info
                            logger.info(f"📱 Found: {name} ({device_info['type']}) - {distance}m away")

                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Could not parse {scan_type} devices JSON")

        # Update device history
        current_time = datetime.now().isoformat()
        updated_devices = {}

        for address, device_info in devices_found.items():
            if address in self.devices:
                # Update existing device
                device_info['first_seen'] = self.devices[address]['first_seen']
                device_info['times_detected'] = self.devices[address].get('times_detected', 0) + 1
            else:
                # New device
                device_info['first_seen'] = current_time
                device_info['times_detected'] = 1
                logger.info(f"✨ NEW: {device_info['name']} added to radar")

            device_info['last_seen'] = current_time
            updated_devices[address] = device_info

        # Add some simulated devices if few real ones found (for demo)
        if len(updated_devices) < 2:
            logger.info("➕ Adding simulated devices for better visualization")
            updated_devices.update(self.get_simulated_devices())

        # Clean up old devices (not seen in 5 minutes)
        cleanup_time = datetime.now().timestamp() - 300
        devices_to_remove = [
            addr for addr, info in self.devices.items()
            if datetime.fromisoformat(info['last_seen']).timestamp() < cleanup_time
               and addr not in updated_devices
        ]

        for addr in devices_to_remove:
            logger.info(f"🗑️ Removing old device: {self.devices[addr]['name']}")

        # Update main devices dict
        self.devices = {k: v for k, v in self.devices.items() if k not in devices_to_remove}
        self.devices.update(updated_devices)

        # Add to scan history
        scan_entry = {
            'timestamp': current_time,
            'devices_found': len(updated_devices),
            'total_devices': len(self.devices),
            'device_list': list(self.devices.keys())
        }
        self.scan_history.append(scan_entry)

        # Keep only recent history
        if len(self.scan_history) > self.max_history:
            self.scan_history.pop(0)

        logger.info(f"✅ Scan complete: {len(self.devices)} devices in memory")
        return self.devices

    def calculate_distance(self, rssi, tx_power=-69, n=2.0):
        """Calculate approximate distance from RSSI"""
        if rssi >= 0 or rssi is None:
            return None

        try:
            # Log-distance path loss model
            ratio = (tx_power - rssi) / (10 * n)
            distance = 10 ** ratio

            # Apply realistic limits
            if distance > 50:
                distance = 50
            elif distance < 0.1:
                distance = 0.1

            return round(distance, 2)
        except:
            return None

    def get_signal_quality(self, rssi):
        """Convert RSSI to signal quality with colors"""
        if rssi is None:
            return {'level': 'Unknown', 'color': '#999999'}

        if rssi >= -50:
            return {'level': 'Excellent', 'color': '#0be881'}
        elif rssi >= -60:
            return {'level': 'Good', 'color': '#4bcffa'}
        elif rssi >= -70:
            return {'level': 'Fair', 'color': '#ffa801'}
        elif rssi >= -80:
            return {'level': 'Poor', 'color': '#ff5e57'}
        else:
            return {'level': 'Very Poor', 'color': '#ef5777'}

    def detect_device_type(self, name):
        """Smart device type detection"""
        if not name or name == 'Unknown Device':
            return 'Unknown'

        name_lower = name.lower()

        # Extended device type detection
        type_patterns = {
            'Headphones': ['headphone', 'headset', 'earbud', 'airpod', 'earphone', 'buds'],
            'Phone': ['iphone', 'galaxy', 'android', 'phone', 'smartphone', 'mobile'],
            'Wearable': ['watch', 'band', 'fitbit', 'wearable', 'tracker', 'smartwatch'],
            'Speaker': ['speaker', 'soundbar', 'sound', 'audio', 'boombox'],
            'Computer': ['laptop', 'pc', 'computer', 'notebook', 'desktop', 'macbook'],
            'Peripheral': ['keyboard', 'mouse', 'controller', 'gamepad', 'input'],
            'Car': ['car', 'automotive', 'vehicle', 'tesla', 'bmw', 'mercedes'],
            'TV': ['tv', 'television', 'smarttv', 'display'],
            'Tablet': ['tablet', 'ipad', 'tab', 'surface']
        }

        for device_type, patterns in type_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return device_type

        return 'Device'

    def get_simulated_devices(self):
        """Get simulated devices for better visualization"""
        simulated = {}
        current_time = datetime.now().isoformat()

        # Common device types with realistic data
        device_templates = [
            {'name': 'Wireless-Headphones', 'type': 'Headphones', 'base_rssi': -65},
            {'name': 'Smart-Watch', 'type': 'Wearable', 'base_rssi': -72},
            {'name': 'BT-Speaker', 'type': 'Speaker', 'base_rssi': -75},
            {'name': 'Phone-Backup', 'type': 'Phone', 'base_rssi': -60},
            {'name': 'Laptop-BT', 'type': 'Computer', 'base_rssi': -68}
        ]

        for i, template in enumerate(device_templates):
            address = f"SIM:{i:02X}:{random.randint(0, 255):02X}:{random.randint(0, 255):02X}"

            # Add some variation
            rssi_variation = random.randint(-8, 8)
            rssi = template['base_rssi'] + rssi_variation
            distance = self.calculate_distance(rssi)
            signal_quality = self.get_signal_quality(rssi)

            simulated[address] = {
                'address': address,
                'name': template['name'],
                'type': template['type'],
                'rssi': rssi,
                'signal_quality': signal_quality,
                'distance': distance,
                'is_connected': random.random() > 0.7,
                'is_paired': True,
                'strength': min(100, max(0, 100 + rssi)),
                'last_seen': current_time,
                'first_seen': current_time,
                'times_detected': 1,
                'scan_method': 'simulated'
            }

        return simulated

    def get_radar_coordinates(self, devices):
        """Convert device data to radar coordinates"""
        radar_devices = []

        for address, device in devices.items():
            # Calculate position based on distance and angle
            distance = device.get('distance', 10)
            if distance is None:
                distance = 10

            # Use device address hash for consistent angle
            angle_hash = sum(ord(c) for c in address) % 360
            current_time = time.time()
            angle = (angle_hash + current_time * 10) % 360

            # Convert to radar coordinates (0-100%)
            max_radius = 80  # Radar screen percentage
            radius = min(max_radius, distance * 5)  # Scale factor

            # Add some movement
            movement_factor = math.sin(current_time * 2 + angle_hash) * 0.3
            radius = radius * (1 + movement_factor)

            x = 50 + (radius * math.cos(math.radians(angle)))
            y = 50 + (radius * math.sin(math.radians(angle)))

            # Ensure within bounds
            x = max(5, min(95, x))
            y = max(5, min(95, y))

            radar_device = device.copy()
            radar_device.update({
                'x': round(x, 2),
                'y': round(y, 2),
                'radius': round(radius, 2),
                'angle': round(angle, 2)
            })

            radar_devices.append(radar_device)

        return radar_devices

    def start_continuous_scan(self, interval=5):
        """Start continuous scanning"""
        if not self.scanning:
            self.scanning = True
            logger.info(f"🔄 Starting continuous scan (interval: {interval}s)")

            def scan_loop():
                scan_count = 0
                while self.scanning:
                    try:
                        scan_count += 1
                        logger.debug(f"Continuous scan #{scan_count}")
                        self.scan_bluetooth_devices()
                        time.sleep(interval)
                    except Exception as e:
                        logger.error(f"Continuous scan error: {e}")
                        time.sleep(2)

            thread = threading.Thread(target=scan_loop, daemon=True)
            thread.start()
            return True
        return False

    def stop_continuous_scan(self):
        """Stop continuous scanning"""
        if self.scanning:
            self.scanning = False
            logger.info("⏹️ Stopped continuous scan")
            return True
        return False


# Initialize radar
radar = BluetoothRadar()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/scan')
def api_scan():
    """Perform scan and return radar data"""
    try:
        devices = radar.scan_bluetooth_devices()
        radar_devices = radar.get_radar_coordinates(devices)

        # Sort by distance (closest first)
        radar_devices.sort(key=lambda x: x.get('distance', 999) or 999)

        # Calculate statistics
        connected_count = sum(1 for d in radar_devices if d.get('is_connected', False))
        avg_distance = None
        distances = [d.get('distance') for d in radar_devices if d.get('distance')]
        if distances:
            avg_distance = round(sum(distances) / len(distances), 2)

        return jsonify({
            'success': True,
            'devices': radar_devices,
            'count': len(radar_devices),
            'connected_count': connected_count,
            'avg_distance': avg_distance,
            'timestamp': datetime.now().isoformat(),
            'scanning': radar.scanning,
            'system_info': radar.get_system_bluetooth_info()
        })
    except Exception as e:
        logger.error(f"API scan error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'devices': [],
            'count': 0
        }), 500


@app.route('/api/start_continuous')
def start_continuous():
    """Start continuous scanning"""
    try:
        success = radar.start_continuous_scan()
        return jsonify({
            'success': success,
            'message': 'Continuous scan started' if success else 'Already scanning',
            'scanning': radar.scanning
        })
    except Exception as e:
        logger.error(f"Start continuous error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stop_continuous')
def stop_continuous():
    """Stop continuous scanning"""
    try:
        success = radar.stop_continuous_scan()
        return jsonify({
            'success': success,
            'message': 'Continuous scan stopped' if success else 'Not scanning',
            'scanning': radar.scanning
        })
    except Exception as e:
        logger.error(f"Stop continuous error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history')
def api_history():
    """Get scan history"""
    try:
        return jsonify({
            'success': True,
            'history': radar.scan_history[-20:],  # Last 20 scans
            'total_scans': len(radar.scan_history)
        })
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status')
def api_status():
    """Get radar status"""
    try:
        system_info = radar.get_system_bluetooth_info()

        return jsonify({
            'success': True,
            'status': {
                'scanning': radar.scanning,
                'devices_in_memory': len(radar.devices),
                'system': radar.system,
                'bluetooth_enabled': bool(system_info and system_info.get('BluetoothEnabled')),
                'last_scan_time': radar.scan_history[-1]['timestamp'] if radar.scan_history else 'Never',
                'total_scans': len(radar.scan_history)
            },
            'system_info': system_info
        })
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/logs/recent')
def api_logs_recent():
    """Get recent logs"""
    try:
        log_file = 'logs/bluetooth_radar.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()[-50:]  # Last 50 lines
            return jsonify({
                'success': True,
                'logs': [line.strip() for line in lines if line.strip()]
            })
        else:
            return jsonify({
                'success': True,
                'logs': ['No logs available yet.']
            })
    except Exception as e:
        logger.error(f"Logs error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/device/<address>')
def api_device_details(address):
    """Get detailed info for a specific device"""
    try:
        device = radar.devices.get(address)
        if device:
            return jsonify({
                'success': True,
                'device': device
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
    except Exception as e:
        logger.error(f"Device details error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clear_devices')
def api_clear_devices():
    """Clear device history"""
    try:
        count = len(radar.devices)
        radar.devices.clear()
        logger.info(f"🗑️ Cleared {count} devices from memory")

        return jsonify({
            'success': True,
            'message': f'Cleared {count} devices',
            'devices_remaining': 0
        })
    except Exception as e:
        logger.error(f"Clear devices error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("📡 ENHANCED BLUETOOTH RADAR SCANNER")
    print("=" * 70)
    print(f"System: {platform.system()}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✨ Enhanced Features:")
    print("  • Real Bluetooth device detection")
    print("  • Interactive radar visualization")
    print("  • Signal strength & distance estimation")
    print("  • Device type classification")
    print("  • Detailed logging system")
    print("  • Continuous scanning mode")
    print("  • System Bluetooth status monitoring")
    print("\n🌐 Web Interface:")
    print("  Home:      http://localhost:5000")
    print("  Dashboard: http://localhost:5000/dashboard")
    print("\n📊 API Endpoints:")
    print("  Scan:      http://localhost:5000/api/scan")
    print("  Status:    http://localhost:5000/api/status")
    print("  History:   http://localhost:5000/api/history")
    print("  Logs:      http://localhost:5000/api/logs/recent")
    print("=" * 70)

    # Initial system check
    print("\n🔍 Performing initial system check...")
    system_info = radar.get_system_bluetooth_info()
    if system_info:
        bt_enabled = system_info.get('BluetoothEnabled', False)
        adapters = system_info.get('Adapters', [])
        services = system_info.get('Services', [])

        print(f"✅ Bluetooth Enabled: {bt_enabled}")
        print(f"✅ Bluetooth Adapters: {len(adapters)}")
        print(f"✅ Bluetooth Services: {len(services)}")

        if not bt_enabled:
            print("\n⚠️  WARNING: Bluetooth may be disabled in system settings")
            print("   Please enable Bluetooth in Windows Settings")
    else:
        print("⚠️  Could not retrieve system Bluetooth information")

    print("\n🚀 Starting radar server...")
    print("=" * 70)

    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Check if port 5000 is already in use")
        print("  2. Try running as Administrator")
        print("  3. Check firewall settings")
        input("\nPress Enter to exit...")