from backend.services.wifi_service import parse_netsh_interfaces


SAMPLE = """
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi Adapter
    GUID                   : 00000000-0000-0000-0000-000000000000
    Physical address       : 11:22:33:44:55:66
    State                  : connected
    SSID                   : HomeNetwork
    BSSID                  : aa:bb:cc:dd:ee:ff
    Network type           : Infrastructure
    Radio type             : 802.11ac
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Connect automatically
    Channel                : 6
    Receive rate (Mbps)    : 433.3
    Transmit rate (Mbps)   : 390
    Signal                 : 82%
"""


def test_parse_connected_wifi_interface():
    result = parse_netsh_interfaces(SAMPLE)
    assert result["connected"] is True
    assert result["interface_name"] == "Wi-Fi"
    assert result["ssid"] == "HomeNetwork"
    assert result["bssid"] == "aa:bb:cc:dd:ee:ff"
    assert result["signal_percent"] == 82
    assert result["quality"] == "Excellent"
    assert result["channel"] == 6
    assert result["receive_rate_mbps"] == 433.3
    assert result["transmit_rate_mbps"] == 390.0
    assert result["distance_estimation"] == "not_available"


def test_unconnected_interface_does_not_claim_signal_or_distance():
    result = parse_netsh_interfaces("    Name : Wi-Fi\n    State : disconnected\n")
    assert result["connected"] is False
    assert result["signal_percent"] is None
    assert result["quality"] == "Unavailable"
    assert result["distance_estimation"] == "not_available"
