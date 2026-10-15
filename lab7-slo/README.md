# Lab 7, optional step: SLO and error budget

A short script that compares a request log with an SLO and reports whether the objective was met.

| Path | Purpose |
|---|---|
| `slo.yaml` | The objective: 99.9 percent of requests under HTTP 500, over a 30-day window |
| `traffic-good.log` | Fifteen requests, all HTTP 200 |
| `traffic-bad.log` | Twenty requests, one HTTP 503 |
| `collect_status.sh` | Calls a URL several times and records one status code per line |
| `calculate_slo.py` | Reads a log and the SLO, then prints the result |

## Requirements

Python 3.9 or newer and PyYAML, installed in the pre-work: `source ~/oc-201-labs/.venv/bin/activate`.

## Run it

```
cd ~/oc-201-labs/lab7-slo
source ~/oc-201-labs/.venv/bin/activate
python3 calculate_slo.py
python3 calculate_slo.py traffic-bad.log
```

The first argument is the request log. An optional second argument is a different SLO file.

## Score your own service

Record real responses from the greeter you deployed in Lab 1, then score them against a copy of the SLO named for it:

```
URL=http://development-default.openchoreoapis.localhost:19080/greeter-service-http/greeter/greet
./collect_status.sh $URL 50 > traffic-live.log
sed 's/payments-api/greeter-service/' slo.yaml > slo-greeter.yaml
python3 calculate_slo.py traffic-live.log slo-greeter.yaml
```

A request with no response is recorded as `000` and counts as a failure. The live run prints `Service: greeter-service`, because it uses the greeter copy of the SLO.

To watch the SLI drop, scale the greeter to zero, collect again, then scale it back:

```
NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.namespace}')
DEP=$(kubectl get deployment -n $NS -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.name}')
kubectl scale deployment $DEP -n $NS --replicas=0
sleep 10
./collect_status.sh $URL 20 > traffic-down.log
python3 calculate_slo.py traffic-down.log slo-greeter.yaml
kubectl scale deployment $DEP -n $NS --replicas=1
```

## What you should see

For the good log: an SLI of 100 percent, and `SLO met. Safe to deploy.` For the bad log: an SLI of 95 percent, `SLO violated`, and a shortfall of 4.90 percentage points. For your greeter: 30 of 30 good, 100 percent.

Both runs print the error budget. A 99.9 percent objective over 30 days leaves a budget of 0.1 percent, which is 43.2 minutes of full outage in the window.

## Things to try

- Change the target in `slo.yaml` to 99 and run the bad log again.
- Add more `200` lines to the bad log until the objective is met.
- Change the window to `7d` and see how the budget in minutes changes.
- Point the collector at a path that does not exist and see how 404 responses are scored. Only status 500 and above, and no response, count against the objective.

## How it maps to OpenChoreo

OpenChoreo's observability plane collects the metrics and logs that would feed this calculation. Alert rules attached as a Trait are the live version of the check: they act when the budget is being spent too fast.
