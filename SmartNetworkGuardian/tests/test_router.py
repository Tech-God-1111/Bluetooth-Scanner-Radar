import pytest
from backend.router.dns_filter import DNSFilter

def test_unknown_router_is_never_reported_as_supported():
    router = DNSFilter()
    assert router.capabilities()["supported"] is False
    with pytest.raises(NotImplementedError):
        router.apply(["example.com"], confirmed=True)

def test_router_write_requires_confirmation():
    with pytest.raises(PermissionError):
        DNSFilter().apply(["example.com"], confirmed=False)
