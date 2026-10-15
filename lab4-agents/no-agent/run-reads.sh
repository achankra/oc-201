#!/usr/bin/env bash
# The same reads the Lab 4 prompts ask for, without an agent.
# usage: ./run-reads.sh [NAMESPACE] [COMPONENT]
set -u
NS="${1:-default}"
COMP="${2:-greeter-service}"

step() { printf '\n== %s\n$ %s\n' "$1" "$2"; eval "$2" || echo "(command failed)"; }

step "1. Namespaces and projects" "occ namespace list; occ project list -n $NS"
step "2. The component, its ComponentType and workload" "kubectl get component $COMP -n $NS -o yaml"
step "4. Release bindings" "kubectl get releasebindings -n $NS | grep -E 'NAME|$COMP'"
step "5. Audit log, last hour" "occ auditlogs --since 1h"

cat <<MSG

Prompt 3 (recent logs) has no command here. Open the component in the portal and read its logs.
Audit logs cover calls made through the OpenChoreo API. The occ calls above should appear in
step 5. The kubectl calls go to the Kubernetes API and will not.
MSG
