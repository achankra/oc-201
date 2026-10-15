from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PlatformEvent:
    type: str                 # "deployment.completed" or "deployment.failed"
    source: str               # where the event came from, for example "github"
    service: str              # for example "orders"
    environment: str          # for example "prod"
    version: str              # for example "1.2.3"
    correlation_id: str       # ties related events together
    payload: Dict[str, Any]   # commit, actor, run URL, failure reason
