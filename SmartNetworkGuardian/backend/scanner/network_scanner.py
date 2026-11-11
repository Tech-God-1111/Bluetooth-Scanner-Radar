import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

def validate_private_network(cidr):
    network = ipaddress.ip_network(cidr, strict=False)
    if network.version != 4 or not network.is_private:
        raise ValueError("Only explicitly selected private IPv4 networks are allowed.")
    if network.num_addresses > 4096:
        raise ValueError("Network is too large for an interactive scan (maximum 4096 addresses).")
    return network

def discover_local_devices(cidr, timeout=1.0, progress=None):
    """Perform a bounded ARP discovery on one explicitly selected private subnet."""
    network = validate_private_network(cidr)
    try:
        from scapy.all import ARP, Ether, srp
    except ImportError as exc:
        raise RuntimeError("Scapy is not installed. Install requirements.txt and run with suitable privileges.") from exc
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=str(network))
    answered, _ = srp(packet, timeout=timeout, retry=0, verbose=False)
    found = []
    for sent, received in answered:
        ip = received.psrc
        mac = received.hwsrc.lower()
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, OSError):
            hostname = None
        found.append({"ip_address": ip, "mac_address": mac, "hostname": hostname,
                      "vendor": None, "observed_at": datetime.now(timezone.utc).isoformat()})
    if progress:
        progress(len(found), network.num_addresses)
    return found
