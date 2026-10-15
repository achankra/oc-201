"""Validate and run traffic configurations.

With no arguments, runs configs/canary.yaml and configs/bluegreen.yaml.
Pass one or more file paths to run your own.
"""
import sys
import time

import yaml

from gateway import secure_ingress_check, print_banner, demo_before_after
from policy import validate_config


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def run(label, cfg):
    print("\n##################################################")
    print(f"### {label}")
    print("##################################################\n")

    errors = validate_config(cfg)
    if errors:
        print("CONFIG REJECTED")
        for e in errors:
            print(" -", e)
        return

    secure_ingress_check(cfg["host"], cfg["security"]["tls"])

    print("CONFIG ACCEPTED")
    print_banner(cfg)

    print("Applying ingress setup...")
    time.sleep(0.4)
    print(" - TLS termination: enabled")
    time.sleep(0.2)
    print(" - Host routing: configured")
    time.sleep(0.2)
    print(" - Traffic rules: applied\n")

    demo_before_after(cfg)


def main():
    paths = sys.argv[1:]
    if paths:
        for path in paths:
            run(path, load(path))
    else:
        run("Canary traffic control", load("configs/canary.yaml"))
        run("Blue/green traffic control", load("configs/bluegreen.yaml"))

    print("Done. The developer's intent changed between runs.")
    print("The platform's security rules did not.")


if __name__ == "__main__":
    main()
