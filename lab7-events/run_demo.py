"""Publish one deployment event and show which consumers react."""
import argparse

from bus import EventBus
from adapters.github_adapter import adapt_github_event
from consumers.issue_consumer import issue_consumer
from consumers.notify_consumer import notify_consumer
from consumers.deploy_marker_consumer import deploy_marker_consumer


def new_consumer(event):
    """Added later, without any change to the adapter or the other consumers."""
    print("\nNEW CONSUMER (added later)")
    print(f"- Doing something new with: {event.type} / {event.service}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("event_json", help="path to a sample GitHub event JSON file")
    ap.add_argument("--enable", default="", help="pass 'new_consumer' to subscribe the extra consumer")
    ap.add_argument("--fanout", action="store_true", help="print a fan-out summary at the end")
    args = ap.parse_args()

    print("==============================================")
    print("Event-driven pipeline")
    print("Adapter -> normalized event -> consumers")
    print("==============================================\n")

    bus = EventBus()
    bus.subscribe("*", notify_consumer)
    bus.subscribe("deployment.completed", deploy_marker_consumer)
    bus.subscribe("deployment.failed", deploy_marker_consumer)
    bus.subscribe("deployment.failed", issue_consumer)

    if args.enable == "new_consumer":
        bus.subscribe("*", new_consumer)

    evt = adapt_github_event(args.event_json)

    print("ADAPTER OUTPUT (normalized event)")
    print(f"- type: {evt.type}")
    print(f"- service: {evt.service}")
    print(f"- env: {evt.environment}")
    print(f"- version: {evt.version}")
    print(f"- correlation_id: {evt.correlation_id}")

    print("\nPublishing event on the bus...")
    bus.publish(evt)

    if args.fanout:
        print("\nFAN-OUT SUMMARY")
        print("- One event, several independent actions (notify, marker, issue).")


if __name__ == "__main__":
    main()
