# Lab 7: alert, incident and root cause

An alert rule on `greeter-service` fires on log lines you inject, creates an incident, and something analyzes it: the built-in SRE agent with an OpenAI key, Claude Code through the OpenChoreo MCP servers, or a local stand-in with no model. This README follows part B of Lab 7 in the workbook. Run every block from a terminal; each one starts with the `cd` or lookup it needs.

| Path | Purpose |
|---|---|
| `manifests/notification-channel-webhook.yaml` | The default notification channel for `development`. Required: the alert-rule trait will not render without one |
| `manifests/alert-rule-trait.yaml` | The alert rule: more than 3 `lab7-error` lines in 5 minutes. The workbook applies the same values as a JSON patch |
| `manifests/release-binding-incident.yaml` | The per-environment setting that creates incidents and, with an OpenAI key, runs the SRE agent |
| `scripts/setup-sre-agent.sh` | Creates the key secret, enables the SRE agent, registers it with the control plane and waits for the pod |
| `simulate/simulate_rca.py` | Local stand-in for the analysis. No model, no key |
| `simulate/sample-incident-logs.txt` | A sample log for the stand-in |

## Requirements

- The cluster from the pre-work, installed with `--with-observability`.
- `greeter-service` from Lab 1, running in `development`.
- One of: an OpenAI API key (usage is billed to your account), Claude Code connected to both MCP servers as in Lab 4, or nothing (the stand-in).

## 1. Create the notification channel, then attach the alert rule

```
cd ~/oc-201-labs/lab7-sre-agent
kubectl apply --dry-run=server -f manifests/notification-channel-webhook.yaml
kubectl apply -f manifests/notification-channel-webhook.yaml
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

Lab 5 created the same channel, so applying it again changes nothing. The channel posts to `https://example.com/openchoreo-alerts`, which accepts nothing. To receive the alerts yourself, put your own URL on the `WEBHOOK_URL` line and run:

```
cd ~/oc-201-labs/lab7-sre-agent
WEBHOOK_URL=https://example.com/openchoreo-alerts
sed "s#https://example.com/openchoreo-alerts#$WEBHOOK_URL#" \
  manifests/notification-channel-webhook.yaml | kubectl apply -f -
```

## 2. Turn on incidents

Paste one block. With an OpenAI key, incidents and the SRE agent:

```
kubectl patch releasebinding greeter-service-development -n default --type=merge -p '
{"spec":{"traitEnvironmentConfigs":{"high-error-rate-log-alert":{"enabled":true,
"actions":{"incident":{"enabled":true,"triggerAiRca":true}}}}}}'
```

Without one, incidents only:

```
kubectl patch releasebinding greeter-service-development -n default --type=merge -p '
{"spec":{"traitEnvironmentConfigs":{"high-error-rate-log-alert":{"enabled":true,
"actions":{"incident":{"enabled":true,"triggerAiRca":false}}}}}}'
```

## 3. Set up the SRE agent (OpenAI key only)

In v1.3.1 the SRE agent cannot use Claude: its image ships only the OpenAI client, and it relies on OpenAI structured output for its report. Without an OpenAI key, skip this step.

```
cd ~/oc-201-labs/lab7-sre-agent
# replace sk-your-key with your own key
export OPENAI_API_KEY=sk-your-key
export RCA_MODEL=gpt-5.4
./scripts/setup-sre-agent.sh
```

The script:

1. Creates `rca-agent-secret` in `openchoreo-observability-plane`, holding your key as `RCA_LLM_API_KEY`.
2. Upgrades the observability plane Helm release with `rca.enabled=true` and `rca.llm.modelName`.
3. Points the default `ClusterObservabilityPlane` at the agent (`rcaAgentURL`).
4. Waits for the `sre-agent` pod.

It uses chart 1.3.1, the version your cluster runs.

## 4. Cause the alert

Write `lab7-error` into the greeter's own log six times, then wait for the rule's one-minute interval. Let the 90-second wait finish.

```
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
```

Alerts and incidents show in the portal and through the Observer API. With the SRE agent, read its report in the incident, and its log:

```
kubectl logs -n openchoreo-observability-plane -l app.kubernetes.io/component=sre-agent --tail 50
```

Without the agent this prints `No resources found`. That is expected.

## 5. No OpenAI key: Claude Code as the SRE

Claude Code, connected to both MCP servers in Lab 4, reads the alert, the incident and the logs, and names a likely cause. Each tool call is visible.

```
claude mcp list | grep openchoreo
cd ~/oc-201-labs/lab7-sre-agent
claude
```

Both servers must show `Connected`. If the token expired, run `~/oc-201-labs/lab4-agents/scripts/register-claude-code-token.sh` and start Claude Code again. Then give it two prompts, one at a time:

1. `List the alerts and incidents for greeter-service in the last hour. Use only the OpenChoreo MCP tools.`
2. `Investigate the latest incident for greeter-service. Read the component logs around the time it fired, group the matching lines, and tell me the most likely root cause with the evidence for it. Use only the OpenChoreo MCP tools.`

What to expect:

- Prompt 1: one `active` incident linked to the alert, with 6 matching lines against a threshold of 3, and `AI RCA` shown as `off`. The MCP tools have no clock, so Claude takes the newest audit-log entry as "now" and says so.
- Prompt 2: the six `lab7-error simulated failure N` lines form one group, from one pod, in the same second. The verdict is a deliberate injection, not an application fault, backed by: no other errors, no failed HTTP requests, no code change since the last rollout.
- The audit trail has no record of the injection, because `kubectl exec` goes around the OpenChoreo API. Access that skips the platform also skips its audit.
- Log timestamps can read a few seconds after the alert. They record when the collector picked the line up, so treat the exact second as approximate.

## 6. No API key: the local stand-in

It counts matching lines, groups them by message shape and names the most frequent one. Fixed rules, no model; its output is not what the agent would write.

```
cd ~/oc-201-labs/lab7-sre-agent
python3 simulate/simulate_rca.py simulate/sample-incident-logs.txt
NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.namespace}')
DEP=$(kubectl get deployment -n $NS -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n $NS deploy/$DEP > logs.txt
python3 simulate/simulate_rca.py logs.txt --match 'lab7-error' --threshold 3
```

## What you should see

- The alert rule fires and an incident is created.
- The SRE agent's report, Claude Code's answer or the stand-in names the injected lines as the cause.

Read any of them as a lead, not a verdict. Confirm it with the logs, the wirelogs or a shell in the pod, as in Lab 6.

## If something fails

- `A notification channel is mandatory for alert rules` on the ReleaseBinding: the channel is missing. Run the first three lines of step 1.
- No rule after the patch: `kubectl get releasebinding greeter-service-development -n default -o yaml | grep -A10 conditions`.
- Nothing happens after the alert: `kubectl logs -n openchoreo-observability-plane deployment/observer --tail 50`.
- You pressed Ctrl-C during the 90-second wait: the injection already ran. Wait a minute, then run `kubectl get observabilityalertrules -A`.
- `can't create /proc/1/fd/1`: run `kubectl exec -n $NS deploy/$DEP -- id`; the exec user must match the process user.
- No `sre-agent` pod: you have no OpenAI key or skipped step 3. Use step 5 or 6.
- The script stops because an ExternalSecret manages `rca-agent-secret`: your cluster keeps secrets in an external store. Put the key there, or use step 5 or 6.

## How it maps to OpenChoreo

The alert rule is a Trait, so it travels with the component. Whether it creates an incident, and whether the agent looks at it, is set per environment in the ReleaseBinding. Development can be noisy and production deliberate without changing the component.
