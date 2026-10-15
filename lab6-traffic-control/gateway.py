"""A simulated gateway: ingress checks and traffic routing."""
import random
from typing import Dict, Any, Optional


def print_banner(cfg: Dict[str, Any]) -> None:
    traffic = cfg["traffic"]
    strategy = traffic["strategy"]

    print("==============================================")
    print("Secure ingress and traffic control")
    print("==============================================")
    print(f"Service:   {cfg['service']}")
    print(f"Ingress:   https://{cfg['host']}  (TLS enforced by the platform)")
    print(f"Strategy:  {strategy}")
    if strategy == "canary":
        print(f"Canary %:  {traffic['canary_percentage']}% to v2")
    if strategy == "bluegreen":
        print(f"Active:    {traffic['active_color']}")
    print("")


def secure_ingress_check(host: str, tls: bool) -> None:
    """Simulate the ingress checks a real platform would perform.

    A real setup adds TLS termination, host routing through the Gateway API,
    and WAF, rate limiting and authorization at the edge.
    """
    if not tls:
        raise RuntimeError("SECURITY VIOLATION: TLS is required but disabled.")
    if not host.endswith(".platform.local"):
        raise RuntimeError("SECURITY VIOLATION: host is outside the platform-owned DNS zone.")


def route_request(cfg: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> str:
    """Pick a backend for one request.

    canary:    a percentage of requests go to v2; X-Canary: true forces v2.
    bluegreen: all requests go to the active color; X-Force-Color overrides it.
    """
    headers = headers or {}
    traffic = cfg["traffic"]
    service = cfg["service"]
    strategy = traffic["strategy"]

    if strategy == "canary":
        if headers.get("X-Canary") == "true":
            return f"{service}-v2"
        pct = int(traffic["canary_percentage"])
        return f"{service}-v2" if random.randint(1, 100) <= pct else f"{service}-v1"

    if strategy == "bluegreen":
        if traffic.get("allow_header_override", True):
            forced = headers.get("X-Force-Color")
            if forced in ("blue", "green"):
                return f"{service}-{forced}"
        return f"{service}-{traffic['active_color']}"

    return f"{service}-v1"


def demo_before_after(cfg: Dict[str, Any]) -> None:
    """Show routing without and with platform traffic control."""
    service = cfg["service"]

    print("=== BEFORE (no platform traffic control) ===")
    for i in range(5):
        print(f"Request {i + 1:02d} -> routed to {service}-v1")
    print("")

    print("=== AFTER (platform-managed traffic control) ===")
    for i in range(12):
        print(f"Request {i + 1:02d} -> routed to {route_request(cfg)}")
    print("")

    print("=== SAFE TEST (header override) ===")
    if cfg["traffic"]["strategy"] == "canary":
        backend = route_request(cfg, {"X-Canary": "true"})
        print(f"Request -> routed to {backend} (forced canary with X-Canary: true)")
    else:
        inactive = "green" if cfg["traffic"]["active_color"] == "blue" else "blue"
        backend = route_request(cfg, {"X-Force-Color": inactive})
        print(f"Request -> routed to {backend} (forced {inactive} with X-Force-Color)")
    print("")
