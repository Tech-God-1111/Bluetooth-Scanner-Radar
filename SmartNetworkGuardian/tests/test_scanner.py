import pytest
from backend.scanner.network_scanner import validate_private_network

def test_private_network_accepted():
    assert str(validate_private_network("192.168.1.0/24")) == "192.168.1.0/24"

@pytest.mark.parametrize("cidr", ["8.8.8.0/24", "2001:db8::/64", "192.168.0.0/16"])
def test_external_ipv6_and_oversized_network_rejected(cidr):
    with pytest.raises(ValueError):
        validate_private_network(cidr)
