"""Platform guardrails for ingress and traffic configuration."""
from typing import Dict, Any, List

ALLOWED_HOST_SUFFIX = ".platform.local"
ALLOWED_ENVS = {"dev", "staging", "prod"}
ALLOWED_STRATEGIES = {"canary", "bluegreen"}


def validate_config(cfg: Dict[str, Any]) -> List[str]:
    """Return a list of violations. An empty list means the config is accepted.

    Rules:
    - TLS must be enabled
    - the host must be under *.platform.local
    - the traffic strategy must be canary or bluegreen
    - a canary percentage must be between 1 and 99
    - a blue/green active color must be blue or green
    """
    errors: List[str] = []

    for required_key in ("service", "host", "security", "traffic"):
        if required_key not in cfg:
            errors.append(f"missing required key: {required_key}")

    if errors:
        return errors

    if not bool(cfg.get("security", {}).get("tls")):
        errors.append("TLS must be enabled (security.tls: true)")

    host = str(cfg.get("host", ""))
    if not host.endswith(ALLOWED_HOST_SUFFIX):
        errors.append(f"Host must be under *{ALLOWED_HOST_SUFFIX} (got: {host})")

    traffic = cfg.get("traffic", {})
    strategy = traffic.get("strategy")
    if strategy not in ALLOWED_STRATEGIES:
        errors.append(f"traffic.strategy must be one of {sorted(ALLOWED_STRATEGIES)} (got: {strategy})")
        return errors

    if strategy == "canary":
        pct = traffic.get("canary_percentage")
        if pct is None:
            errors.append("canary strategy requires traffic.canary_percentage")
        else:
            try:
                if not 1 <= int(pct) <= 99:
                    errors.append("canary_percentage must be between 1 and 99")
            except (TypeError, ValueError):
                errors.append("canary_percentage must be an integer")

    if strategy == "bluegreen":
        if traffic.get("active_color") not in ("blue", "green"):
            errors.append("bluegreen strategy requires traffic.active_color: 'blue' or 'green'")

    env = cfg.get("env")
    if env is not None and env not in ALLOWED_ENVS:
        errors.append(f"env must be one of {sorted(ALLOWED_ENVS)} (got: {env})")

    return errors
