#!/usr/bin/env bash
# The same calls the Lab 4 prompts ask for, without an agent.
# usage: ./run-reads.sh [NAMESPACE] [COMPONENT]
#
# Steps 1, 2 and 4 read. Step 5 creates the agent-demo project with occ apply,
# because the audit log records changes only, and step 6 reads the audit log.
set -u
NS="${1:-default}"
COMP="${2:-greeter-service}"

step() { printf '\n== %s\n$ %s\n' "$1" "$2"; eval "$2" || echo "(command failed)"; }

PROJECT=$(mktemp)
trap 'rm -f "$PROJECT"' EXIT
PIPE=$(kubectl get project default -n "$NS" -o jsonpath='{.spec.deploymentPipelineRef.name}' 2>/dev/null)
cat > "$PROJECT" <<JSON
{"apiVersion": "openchoreo.dev/v1alpha1", "kind": "Project",
 "metadata": {"name": "agent-demo", "namespace": "$NS"},
 "spec": {"deploymentPipelineRef": {"name": "${PIPE:-default}"},
          "type": {"kind": "ClusterProjectType", "name": "default"}}}
JSON

step "1. Namespaces and projects" "occ namespace list; occ project list -n $NS"
step "2. The component, its ComponentType and workload" "kubectl get component $COMP -n $NS -o yaml"
step "4. Release bindings" "kubectl get releasebindings -n $NS | grep -E 'NAME|$COMP'"
step "5. Create a project (a change)" "occ apply -f $PROJECT"
step "6. Audit log, last hour" "occ auditlogs --since 1h"

cat <<MSG

Prompt 3 (recent logs) has no command here. Open the component in the portal and read its logs.
The audit log records changes (create, update, delete), not reads. Step 6 shows the agent-demo
creation from step 5 and none of the reads. The kubectl calls go to the Kubernetes API and would
not appear even if they changed something.

Remove the demo project when you are done: kubectl delete project agent-demo -n $NS
MSG
