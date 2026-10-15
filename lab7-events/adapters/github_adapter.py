import json

from schemas import PlatformEvent


def adapt_github_event(json_path: str) -> PlatformEvent:
    """Map a deployment event from GitHub into the platform's event schema."""
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    d = raw["deployment"]
    evt_type = "deployment.completed" if d["status"] == "success" else "deployment.failed"

    return PlatformEvent(
        type=evt_type,
        source="github",
        service=d["service"],
        environment=d["environment"],
        version=d["version"],
        correlation_id=d["id"],
        payload={
            "commit": d.get("commit"),
            "actor": d.get("actor"),
            "run_url": d.get("run_url"),
            "reason": d.get("reason", ""),
        },
    )
