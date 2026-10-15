# Lab 7: event-driven pipeline

One deployment event comes in from GitHub, is converted into a platform event, and is handled by independent consumers. No consumer knows about the others.

| Path | Purpose |
|---|---|
| `schemas.py` | The platform event: type, source, service, environment, version, correlation ID, payload |
| `bus.py` | An in-memory event bus. Subscribe by event type, or with `*` for every event |
| `adapters/github_adapter.py` | Converts a GitHub deployment event into the platform event |
| `consumers/notify_consumer.py` | Reacts to every event |
| `consumers/deploy_marker_consumer.py` | Emits a deploy marker for completed and failed deployments |
| `consumers/issue_consumer.py` | Creates an issue, only for failed deployments |
| `events/` | A successful and a failed sample event |
| `run_demo.py` | Wires the consumers to the bus and publishes one event |

## Requirements

Python 3.9 or newer. No other packages.

## Run it

```
cd ~/oc-201-labs/lab7-events
python3 run_demo.py events/github_deploy_completed.json
python3 run_demo.py events/github_deploy_failed.json
python3 run_demo.py events/github_deploy_completed.json --enable new_consumer
python3 run_demo.py events/github_deploy_failed.json --fanout
```

## What you should see

- The successful event reaches the notify consumer and the deploy marker. No issue is created.
- The failed event reaches the notify consumer and the deploy marker, and also creates an issue with the run link and the failure reason.
- With `--enable new_consumer`, one more consumer reacts. The producer and the other consumers did not change.
- `--fanout` adds a one-line summary at the end.

## Things to try

- Write a consumer that reacts only to events from the `prod` environment and subscribe it in `run_demo.py`.
- Add a second adapter for a different source and make it produce the same `PlatformEvent`.
- Remove `issue_consumer` from `run_demo.py` and run the failed event. Nothing else breaks.

## How it maps to OpenChoreo

OpenChoreo records what happens to a component as resources: workflow runs, releases and bindings. Those changes are the events a platform can react to. The same shape applies: one source of truth, many independent reactions.
