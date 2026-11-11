"""Router capability registry. Add adapters only after verifying vendor documentation."""
SUPPORTED_ADAPTERS = {}

def list_supported_routers():
    return sorted(SUPPORTED_ADAPTERS)
