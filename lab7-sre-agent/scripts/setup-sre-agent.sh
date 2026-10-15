#!/usr/bin/env bash
# Set up the OpenChoreo SRE agent on the local k3d install.
#
# Required:
#   OPENAI_API_KEY   your OpenAI API key
#   RCA_MODEL        the model name, for example gpt-5.4
# Optional:
#   CHART_VERSION    chart version of the observability plane (default 1.3.1)
#   RCA_AGENT_URL    address registered with the control plane
#                    (default http://rca-agent.openchoreo.localhost:11080)
#
# usage: OPENAI_API_KEY=... RCA_MODEL=gpt-5.4 ./scripts/setup-sre-agent.sh
set -euo pipefail

NS="openchoreo-observability-plane"
CHART="oci://ghcr.io/openchoreo/helm-charts/openchoreo-observability-plane"
CHART_VERSION="${CHART_VERSION:-1.3.1}"
RCA_AGENT_URL="${RCA_AGENT_URL:-http://rca-agent.openchoreo.localhost:11080}"

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY to your OpenAI API key}"
: "${RCA_MODEL:?Set RCA_MODEL to a model name, for example gpt-5.4}"

for tool in kubectl helm; do
  command -v "$tool" >/dev/null 2>&1 || { echo "$tool was not found on your PATH" >&2; exit 1; }
done

if kubectl get externalsecret rca-agent-secret -n "$NS" >/dev/null 2>&1; then
  echo "An ExternalSecret named rca-agent-secret already manages this secret."
  echo "Put the key in the secret store behind it instead, then run the Helm step by hand."
  exit 1
fi

echo "1/4  Creating the secret rca-agent-secret in $NS"
kubectl create secret generic rca-agent-secret \
  -n "$NS" \
  --from-literal=RCA_LLM_API_KEY="$OPENAI_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "2/4  Enabling the SRE agent (chart $CHART_VERSION, model $RCA_MODEL)"
helm upgrade --install openchoreo-observability-plane "$CHART" \
  --version "$CHART_VERSION" \
  --namespace "$NS" \
  --reuse-values \
  --set rca.enabled=true \
  --set rca.llm.modelName="$RCA_MODEL"

echo "3/4  Registering the agent with the control plane"
kubectl patch clusterobservabilityplane default --type=merge \
  -p "{\"spec\":{\"rcaAgentURL\":\"$RCA_AGENT_URL\"}}"

echo "4/4  Checking the pod"
kubectl get pods -n "$NS" -l app.kubernetes.io/component=sre-agent
if ! kubectl wait --for=condition=Ready pod -l app.kubernetes.io/component=sre-agent \
     -n "$NS" --timeout=180s; then
  echo "The sre-agent pod is not ready yet. Look at its logs:"
  echo "  kubectl logs -n $NS -l app.kubernetes.io/component=sre-agent"
  exit 1
fi
echo "The SRE agent is running."
