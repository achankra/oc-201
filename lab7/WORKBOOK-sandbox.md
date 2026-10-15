# Lab 7: Observe, alert and scale out

*OC-201 workbook, WSO2 sandbox edition. Using the local install instead? See [WORKBOOK-local.md](WORKBOOK-local.md).*

**Goal:** Read live signals for a running service, attach an alert rule that creates an incident, find the cause with the SRE agent or Claude Code, and see how an event-driven pipeline fans out.

## Start of a sandbox session

Paste into the sandbox terminal in your browser, never into a terminal on your own machine. Skip this box if you are still in the session where you ran the previous lab; pasting it twice does no harm. In a new session, paste the setup block. It clones the lab code, sets up Python and OPA, and saves the gateway address for every later block.

```bash
setopt interactivecomments
grep -q interactivecomments ~/.zshrc || echo 'setopt interactivecomments' >> ~/.zshrc
[ -d ~/oc-201-labs ] || git clone https://github.com/achankra/oc-201.git ~/oc-201-labs
cd ~/oc-201-labs
python3 -m venv --without-pip --system-site-packages .venv
mkdir -p ~/bin
curl -fsSL -o ~/bin/opa \
  https://github.com/open-policy-agent/opa/releases/latest/download/opa_linux_amd64_static
chmod +x ~/bin/opa
GWIP=$(kubectl get svc gateway-default -n openchoreo-data-plane -o jsonpath='{.spec.clusterIP}')
sed -i -e '/^export GWADDR=/d' -e '/^export DEVHOST=/d' -e '/^export PATH=.HOME.bin/d' ~/.zshrc
echo 'export PATH=$HOME/bin:$PATH' >> ~/.zshrc
echo "export GWADDR=$GWIP:9080" >> ~/.zshrc
echo "export DEVHOST=development-default.demo.openchoreo.wso2.com" >> ~/.zshrc
source ~/.zshrc
deactivate 2>/dev/null
export PATH=$HOME/bin:$PATH
source ~/oc-201-labs/.venv/bin/activate
echo "gateway $GWADDR, host $DEVHOST"
opa version | head -1
```

```bash
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.2/samples
kubectl apply -f $BASE/from-image/go-greeter-service/greeter-service.yaml
kubectl wait --for=condition=Ready component/greeter-service -n default --timeout=180s
```

The second block redeploys the Lab 1 greeter, which this lab uses.

## A. Observe

### 1. Generate traffic and open the observability views

```bash
URL=http://$GWADDR/greeter-service-http
for i in $(seq 1 20); do curl -s -H "Host: $DEVHOST" $URL/greeter/greet; done
occ component logs greeter-service -n default -p default --env development --tail 20
```

In the portal, open `greeter-service` and use the logs, metrics and traces tabs.

## B. Alert and SRE agent

### 2. Attach the alert rule

> **Dry run first:** the block checks with a server-side dry run before it changes anything.

The rule counts log lines matching `lab7-error`, more than 3 in 5 minutes. The greeter never logs that by itself, so you control when it fires. This is the trait in `lab7-sre-agent/manifests/alert-rule-trait.yaml`, applied as a JSON patch.

```bash
# the alert-rule trait requires a notification channel in the environment
CH=~/oc-201-labs/lab7-sre-agent/manifests/notification-channel-webhook.yaml
kubectl apply --dry-run=server -f $CH
kubectl apply -f $CH
kubectl get observabilityalertsnotificationchannels -n default
kubectl get clustertraits,traits -A | grep observability-alert-rule
P='{"spec":{"traits":[{"kind":"ClusterTrait","name":"observability-alert-rule",
"instanceName":"high-error-rate-log-alert","parameters":{
"description":"lab7-error lines in the greeter log","severity":"critical",
"source":{"type":"log","query":"lab7-error"},
"condition":{"window":"5m","interval":"1m","operator":"gt","threshold":3}}}]}}'
kubectl patch component greeter-service -n default --type=merge -p "$P" --dry-run=server
kubectl patch component greeter-service -n default --type=merge -p "$P"
sleep 20
kubectl get observabilityalertrules -A
```

The first lines make sure `development` has a default notification channel; the trait refuses to render without one. The channel is the same one Lab 5 created, so applying it again changes nothing. The `grep` line shows the trait is a ClusterTrait on this install, which is what the patch uses.

### 3. Turn on incidents and the analysis

Set per environment, on the development ReleaseBinding. The key is the rule's `instanceName`. The sandbox has no SRE agent, so turn on incidents only.

```bash
# without a key: incident only
kubectl patch releasebinding greeter-service-development -n default --type=merge -p '
{"spec":{"traitEnvironmentConfigs":{"high-error-rate-log-alert":{"enabled":true,
"actions":{"incident":{"enabled":true,"triggerAiRca":false}}}}}}'
```

```bash
# check
kubectl get releasebinding greeter-service-development -n default \
  -o jsonpath='{.spec.traitEnvironmentConfigs}{"\n"}'
```

The default channel posts to `https://example.com/openchoreo-alerts`, which accepts nothing. Optional, to receive the alerts yourself: point it at a URL you control and apply it again.

```bash
cd ~/oc-201-labs/lab7-sre-agent
# put your own URL on the next line
WEBHOOK_URL=https://example.com/openchoreo-alerts
sed "s#https://example.com/openchoreo-alerts#$WEBHOOK_URL#" \
  manifests/notification-channel-webhook.yaml | kubectl apply -f -
```

### 4. The built-in SRE agent (not in the sandbox)

The sandbox does not run the SRE agent, and installing it needs an OpenAI key and the chart for v1.2.2. Skip this step and use step 6, where Claude Code does the analysis through the MCP servers.

### 5. Cause the alert and read the result

Write `lab7-error` into the greeter's own log six times, then wait for the rule's one-minute interval.

```bash
NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.namespace}')
DEP=$(kubectl get deployment -n $NS -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NS deploy/$DEP -- sh -c \
  'for i in 1 2 3 4 5 6; do echo "lab7-error simulated failure $i" > /proc/1/fd/1; done'
kubectl logs -n $NS deploy/$DEP --tail 8
echo "waiting 90 seconds for the rule to evaluate"
sleep 90
kubectl get observabilityalertrules -A
kubectl describe observabilityalertrules -A | grep -A8 -i status
```

The `waiting 90 seconds` pause is the rule's evaluation interval; let it finish. Alerts and incidents are in the console and through the Observer API.

### 6. Claude Code as the SRE

Claude Code, connected to both MCP servers in Lab 4, can do what the SRE agent does: read the alert, the incident and the logs, and name a likely cause. Each tool call is visible, so you see how the analysis is built. Check the connection, start Claude Code, then give it these prompts one at a time.

```bash
claude mcp list | grep openchoreo
cd ~/oc-201-labs/lab7-sre-agent
claude
```

Both servers must show `Connected`, and your key must be set (pre-work step 5). Then:

```text
List the alerts and incidents for greeter-service in the last hour.
Use only the OpenChoreo MCP tools.
```

Then paste this second prompt: `Investigate the latest incident for greeter-service. Read the component logs around the time it fired, group the matching lines, and tell me the most likely root cause with the evidence for it. Use only the OpenChoreo MCP tools.` Read the answer as a lead, not a verdict, and compare it with the local stand-in in the next step.

What to expect:

- Prompt 1: one `active` incident linked to the alert, with 6 matching lines against a threshold of 3, and `AI RCA` shown as `off` (that column belongs to the SRE agent). The MCP tools have no clock, so Claude takes the newest audit-log entry as "now" and says so.
- Prompt 2: the six `lab7-error simulated failure N` lines form one group, from one pod, in the same second. The verdict should be a deliberate injection, not an application fault, backed by: no other errors, no failed HTTP requests, no code change since the last rollout.
- The audit trail has no record of the injection, because `kubectl exec` goes around the OpenChoreo API. Access that skips the platform also skips its audit.
- Log timestamps can read a few seconds after the alert. They record when the collector picked the line up, so treat the exact second as approximate.

### 7. No API key: the local stand-in

Not the SRE agent and no model: it counts matching lines and names the most frequent message shape. Run it on the sample, then on your own greeter's log.

```bash
cd ~/oc-201-labs/lab7-sre-agent
python3 simulate/simulate_rca.py simulate/sample-incident-logs.txt
NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.namespace}')
DEP=$(kubectl get deployment -n $NS -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n $NS deploy/$DEP > logs.txt
python3 simulate/simulate_rca.py logs.txt --match 'lab7-error' --threshold 3
```

## C. Fan out

### 8. Run the event-pipeline demo

```bash
cd ~/oc-201-labs/lab7-events
python3 run_demo.py events/github_deploy_completed.json
python3 run_demo.py events/github_deploy_failed.json
python3 run_demo.py events/github_deploy_completed.json --enable new_consumer
python3 run_demo.py events/github_deploy_failed.json --fanout
```

A success notifies and emits a marker; a failure also creates an issue; a new consumer is added without touching the producer.

### 9. Read how a second data plane is registered

```bash
kubectl get clusterdataplanes
kubectl explain clusterdataplane.spec
kubectl explain clusterdataplane.spec.clusterAgent
kubectl get clusterdataplane default -o yaml | sed -n '/^spec:/,/^status:/p'
```

Write down what each field is for: `planeID` (which physical cluster the agent connects from), `clusterAgent.clientCA` (the CA that verifies the agent's client certificate), `secretStoreRef` (the External Secrets store in that cluster), `gateway` (its ingress), and `observabilityPlaneRef` (where its logs, metrics and alerts go). You do not need a second cluster.

## D. Stretch

### 10. Compute an error budget

```bash
cd ~/oc-201-labs/lab7-slo
source ~/oc-201-labs/.venv/bin/activate
python3 calculate_slo.py
python3 calculate_slo.py traffic-bad.log
URL=http://$GWADDR/greeter-service-http/greeter/greet
HOST_HEADER=$DEVHOST ./collect_status.sh $URL 30 > traffic-live.log
sed 's/payments-api/greeter-service/' slo.yaml > slo-greeter.yaml
python3 calculate_slo.py traffic-live.log slo-greeter.yaml
```

A 99.9% objective over 30 days leaves a 0.1% error budget, 43.2 minutes. The second run shows a violation. The last commands record 30 real responses from your greeter and score them against a copy of the SLO named for it.

## Checkpoint

- [ ] You can see logs for `greeter-service` in the portal
- [ ] The alert rule fires and an incident is created
- [ ] Claude Code or the stand-in names the injected `lab7-error` lines as the cause
- [ ] The failed event creates an issue; the success event does not
- [ ] You can list the inputs needed to register a data plane

## Troubleshooting

- No logs in the portal: run `kubectl get pods -n openchoreo-observability-plane` and wait a minute for ingestion.
- Rule missing: run `kubectl get releasebinding greeter-service-development -n default -o yaml | grep -A10 conditions`. `A notification channel is mandatory` means the channel lines in step 2 did not run.
- Nothing happens after the alert: run `kubectl logs -n openchoreo-observability-plane deployment/observer --tail 50`.
- `can't create /proc/1/fd/1`: run `kubectl exec -n $NS deploy/$DEP -- id`; the exec user must match the process user.
- Event demo errors: run it from `~/oc-201-labs/lab7-events` with the exact arguments shown.
- Ctrl-C during the 90-second wait: the injection already ran. Wait a minute, then run `kubectl get observabilityalertrules -A`.
- The channel comes out with an empty URL: `WEBHOOK_URL` must be set on its own line before the `sed` line, with no comment after it.
- The live SLO run prints `Service: payments-api`: score against `slo-greeter.yaml`, as in step 10.

---

Previous: [Lab 6](../lab6-traffic-control/WORKBOOK-sandbox.md) · [All modules](../WORKBOOK.md)
