class DNSFilter:
    """Safe capability boundary: no router is modified unless a verified adapter is registered."""
    def __init__(self, adapter=None):
        self.adapter = adapter

    def capabilities(self):
        if self.adapter is None:
            return {"supported": False, "reason": "No verified router adapter is configured."}
        return self.adapter.capabilities()

    def preview(self, domains):
        return {"domains": sorted(set(domains)), "will_apply": False,
                "message": "Preview only. No router changes have been made."}

    def apply(self, domains, confirmed=False):
        if not confirmed:
            raise PermissionError("Explicit confirmation is required.")
        if self.adapter is None:
            raise NotImplementedError("The detected router has no verified filtering adapter.")
        return self.adapter.apply_domains(sorted(set(domains)))
