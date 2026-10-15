#!/usr/bin/env bash
# Create a project named governed-demo that uses the governed ClusterProjectType,
# with a ProjectReleaseBinding for each pipeline environment.
# It copies the deployment pipeline from the default project, so no name is typed by hand.
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="${1:-governed-demo}"
TYPE="${2:-governed}"

PIPE="$(kubectl get project default -n default -o jsonpath='{.spec.deploymentPipelineRef.name}')"
if [[ -z "${PIPE}" ]]; then
  echo "could not read spec.deploymentPipelineRef.name from the default project."
  echo "Run: kubectl get project default -n default -o yaml"
  exit 1
fi

OUT="lab3-project.yaml"
cat > "${OUT}" <<YAML
apiVersion: openchoreo.dev/v1alpha1
kind: Project
metadata:
  name: ${PROJECT}
  namespace: default
spec:
  deploymentPipelineRef:
    name: ${PIPE}
  type:
    kind: ClusterProjectType
    name: ${TYPE}
YAML

echo "wrote ${OUT} (pipeline: ${PIPE}, type: ${TYPE})"
kubectl apply --dry-run=server -f "${OUT}"
kubectl apply -f "${OUT}"

# A project gets a cell namespace per environment only through a ProjectReleaseBinding.
# Create one for every environment in the pipeline.
ENVS="$(kubectl get deploymentpipeline "${PIPE}" -n default -o jsonpath='{range .spec.promotionPaths[*]}{.sourceEnvironmentRef.name}{"\n"}{range .targetEnvironmentRefs[*]}{.name}{"\n"}{end}{end}' | sort -u)"
for ENV in ${ENVS}; do
  kubectl apply -f - <<JSON
{"apiVersion": "openchoreo.dev/v1alpha1", "kind": "ProjectReleaseBinding",
 "metadata": {"name": "${PROJECT}-${ENV}", "namespace": "default",
  "labels": {"openchoreo.dev/project": "${PROJECT}", "openchoreo.dev/environment": "${ENV}"}},
 "spec": {"owner": {"projectName": "${PROJECT}"}, "environment": "${ENV}"}}
JSON
done

echo ""
echo "waiting for the cell namespaces of ${PROJECT}..."
for _ in $(seq 1 24); do
  kubectl get namespaces -l openchoreo.dev/project="${PROJECT}" -o name | grep -q . && break
  sleep 5
done
kubectl get namespaces -l openchoreo.dev/project="${PROJECT}" -L openchoreo.dev/environment
