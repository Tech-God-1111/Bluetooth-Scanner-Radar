import ipaddress
import subprocess
import psutil

def detect_default_gateway():
    result = subprocess.run(["route", "print", "-4"], capture_output=True, text=True, timeout=5)
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
            try:
                return str(ipaddress.IPv4Address(parts[2]))
            except ipaddress.AddressValueError:
                continue
    return None

def active_ipv4_interfaces():
    output = []
    for name, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family == 2 and not address.address.startswith("127."):
                output.append({"interface": name, "ip": address.address, "netmask": address.netmask})
    return output
