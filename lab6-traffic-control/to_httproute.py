"""Turn a traffic config into a Gateway API HTTPRoute.

The config is checked with the same guardrails as run_demo.py first. A config
that fails the checks produces no output.

usage: python3 to_httproute.py configs/canary.yaml --gateway <gateway-name>
"""
import argparse
import sys

import yaml

from policy import validate_config


def backends(cfg):
    traffic = cfg["traffic"]
    service = cfg["service"]
    if traffic["strategy"] == "canary":
        pct = int(traffic["canary_percentage"])
        return [(f"{service}-v1", 100 - pct), (f"{service}-v2", pct)]
    active = traffic["active_color"]
    other = "green" if active == "blue" else "blue"
    return [(f"{service}-{active}", 100), (f"{service}-{other}", 0)]


def build_route(cfg, gateway, gateway_namespace, namespace, port):
    parent = {"name": gateway}
    if gateway_namespace:
        parent["namespace"] = gateway_namespace
    return {
        "apiVersion": "gateway.networking.k8s.io/v1",
        "kind": "HTTPRoute",
        "metadata": {
            "name": f"{cfg['service']}-{cfg['traffic']['strategy']}",
            "namespace": namespace,
        },
        "spec": {
            "parentRefs": [parent],
            "hostnames": [cfg["host"]],
            "rules": [{
                "backendRefs": [
                    {"name": name, "port": port, "weight": weight}
                    for name, weight in backends(cfg)
                ],
            }],
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="path to a traffic config, for example configs/canary.yaml")
    ap.add_argument("--gateway", required=True, help="name of the Gateway the route attaches to")
    ap.add_argument("--gateway-namespace", default=None, help="namespace of the Gateway, if different from the route")
    ap.add_argument("--namespace", default="default", help="namespace for the HTTPRoute (default: default)")
    ap.add_argument("--port", type=int, default=8080, help="backend service port (default: 8080)")
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    errors = validate_config(cfg)
    if errors:
        print("CONFIG REJECTED, no route generated", file=sys.stderr)
        for e in errors:
            print(" -", e, file=sys.stderr)
        sys.exit(1)

    route = build_route(cfg, args.gateway, args.gateway_namespace, args.namespace, args.port)
    print(yaml.safe_dump(route, sort_keys=False), end="")


if __name__ == "__main__":
    main()
