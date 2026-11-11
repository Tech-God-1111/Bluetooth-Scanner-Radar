import time
import dns.resolver

def check_dns(domain="example.com", nameserver=None, timeout=3):
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    if nameserver:
        resolver.nameservers = [nameserver]
    started = time.perf_counter()
    try:
        answers = resolver.resolve(domain, "A")
        return {"ok": True, "elapsed_ms": round((time.perf_counter()-started)*1000,2),
                "addresses": [answer.to_text() for answer in answers], "error": None}
    except Exception as exc:
        return {"ok": False, "elapsed_ms": round((time.perf_counter()-started)*1000,2),
                "addresses": [], "error": str(exc)}
