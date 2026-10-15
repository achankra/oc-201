# Lab 6: traffic control and diagnosis

This folder holds the traffic-control part of Lab 6. The rest of the lab, building from source and promoting, happens in OpenChoreo and is in the workbook. The two Diagnose sections below cover the wirelogs and web shell steps.

A simulated gateway with platform guardrails. A developer describes intent in a short YAML file. The platform checks it, then routes requests either as a canary or as blue/green.

| Path | Purpose |
|---|---|
| `policy.py` | The guardrails. Returns a list of violations for a config |
| `gateway.py` | The simulated gateway: ingress checks and request routing |
| `run_demo.py` | Loads configs, validates them, and prints routing before and after |
| `to_httproute.py` | Turns a config into a Gateway API HTTPRoute with weighted backends |
| `configs/canary.yaml` | 20 percent of requests go to v2 |
| `configs/bluegreen.yaml` | All requests go to the active color |

## Requirements

Python 3.9 or newer and PyYAML, installed in the pre-work: `source ~/oc-201-labs/.venv/bin/activate`.

## Run it

```
cd ~/oc-201-labs/lab6-traffic-control
source ~/oc-201-labs/.venv/bin/activate
python3 run_demo.py
```

This runs the canary config and then the blue/green config. To run your own file, or a single one, pass the paths:

```
cd ~/oc-201-labs/lab6-traffic-control
python3 run_demo.py configs/canary.yaml
```

## What you should see

For each config the program prints `CONFIG ACCEPTED`, a short setup log, twelve routed requests, and one forced request. In the canary run about one request in five goes to `orders-v2`, and the exact requests change between runs. In the blue/green run every request goes to `orders-blue`, and the forced request goes to `orders-green`.

## Generate a real route

`to_httproute.py` applies the same guardrails and then prints a Gateway API HTTPRoute. A canary config becomes two weighted backends (80 and 20 for `canary_percentage: 20`). A blue/green config sends weight 100 to the active color and 0 to the other.

Use the data plane's Gateway, which serves your components (there is one Gateway per plane), then generate the route and have the cluster validate it without creating it:

```
cd ~/oc-201-labs/lab6-traffic-control
kubectl get gateways -A
GW_NS=openchoreo-data-plane
GW_NAME=$(kubectl get gateways -n $GW_NS -o jsonpath='{.items[0].metadata.name}')
python3 to_httproute.py configs/canary.yaml --gateway $GW_NAME --gateway-namespace $GW_NS \
  | kubectl apply --dry-run=server -f -
```

To see a guardrail stop a route, make a broken copy of the canary config and run it:

```
cd ~/oc-201-labs/lab6-traffic-control
sed 's/canary_percentage: 20/canary_percentage: 150/' configs/canary.yaml > configs/canary-broken.yaml
python3 to_httproute.py configs/canary-broken.yaml --gateway $GW_NAME
```

It prints `CONFIG REJECTED, no route generated` and `canary_percentage must be between 1 and 99`.

Options: `--namespace` (where the route lives, default `default`) and `--port` (backend port, default 8080). A config that breaks a guardrail prints the violations and produces no route. TLS is a listener setting on the Gateway, so it does not appear in the route.

The backends `orders-v1` and `orders-v2` do not exist, so use `--dry-run=server` and do not apply the route for real.

## Diagnose with wirelogs

Wirelogs are the flow records Cilium keeps for traffic between workloads. Each record shows a source, a destination and a verdict: forwarded or dropped. OpenChoreo shows them in the portal and through the Observer API. They come from the Cilium network module, which is separate from the core install. Without the module the wirelogs view is not available. To add it, follow the README of the `networking-cilium` module in the `openchoreo/community-modules` repository. If you skip the module, read the request in the component logs instead.

Use `greeting-service`, built in part A of the lab. Its endpoint is `greeter-api`, so its gateway path is `/greeting-service-greeter-api`. Call it so there is something to read:

```
curl -i http://development-default.openchoreoapis.localhost:19080/greeting-service-greeter-api/greeter/greet
```

Read the same request in the wirelogs for the component, then cause three different failures and compare what each one looks like:

| Failure | How to cause it | What to expect in the wirelogs |
|---|---|---|
| The application answers with an error | Request a path that does not exist | A forwarded flow. The connection worked; the app answered `404 page not found` |
| Nothing is running | Scale the Deployment to 0, then call the service. Scale back to 1 afterward | No flow reaches the pod. The gateway answers `503 no healthy upstream` and the EndpointSlice is empty |
| The cell refuses the connection | From a pod outside the cell, call the service by its cluster address | A dropped flow. OpenChoreo puts an ingress NetworkPolicy on every component, so curl reports `Could not connect to server` |

The workbook has the exact commands for all three, including how to find the cell namespace and the Deployment name.

A dropped flow points at a network policy. A forwarded flow with a failing response points at the application.

## Diagnose with the web shell

When the flow records say the request reached the pod and the pod still fails, look inside it. The portal can open an interactive shell in a running component instance. The CLI can do the same:

```
occ component exec greeting-service -n default -p default --env development
```

Or run single checks without an interactive shell:

```
oc_exec() { occ component exec greeting-service -n default -p default \
  --env development -- "$@"; }
oc_exec ps
oc_exec env
oc_exec nslookup kubernetes.default.svc.cluster.local
oc_exec cat /proc/net/tcp /proc/net/tcp6
```

Check:

- which process is running, and which port it listens on
- the environment variables the platform injected
- whether the pod can reach and resolve the services it depends on

A pod listening on a different port than the endpoint declares is a common cause. Compare what the shell shows with the endpoint declared on the component. The tools inside the pod depend on its image. A minimal image may have no `ps`, `ss` or `curl`; the socket tables `cat /proc/net/tcp /proc/net/tcp6` always work. The greeter listens on `:::9090`, an IPv6 socket, so it appears in `tcp6`, with the port in hex (`2382`).

The environment variables are worth reading. The `*_SERVICE_HOST` and `*_PORT` variables are Kubernetes listing the other services in the same namespace, not configuration from OpenChoreo; a component's own configuration arrives through its ComponentType.

Exec is authorized like any other action. If it is denied, the role bound to your sign-in does not allow it.

## The guardrails

A config is rejected when:

- `security.tls` is not true
- the host is not under `.platform.local`
- the strategy is not `canary` or `bluegreen`
- a canary percentage is outside 1 to 99
- a blue/green active color is not `blue` or `green`

## Things to try

- Set `tls: false` and read the message.
- Change `active_color` to `green`. All traffic moves in one edit.
- Change the host to `orders.example.com`.

## How it maps to OpenChoreo

A developer's endpoint declaration plays the part of the YAML file. The gateway and routes OpenChoreo generates play the part of `gateway.py`. The checks in `policy.py` are the kind of rule a platform team writes into a ComponentType or a policy, so developers cannot opt out of them.
