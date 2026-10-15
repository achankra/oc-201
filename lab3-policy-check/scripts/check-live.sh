#!/usr/bin/env bash
# Check every Deployment in a namespace against policies/deployment.rego.
# Use it on the namespace where OpenChoreo runs your component.
set -euo pipefail

cd "$(dirname "$0")/.."

NS="${1:-}"
if [[ -z "${NS}" ]]; then
  echo "usage: ./scripts/check-live.sh <namespace>"
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

NAMES="$(kubectl get deployments -n "${NS}" -o name)"
if [[ -z "${NAMES}" ]]; then
  echo "no deployments in namespace ${NS}"
  exit 0
fi

FAILED=0
for D in ${NAMES}; do
  echo "== ${D}"
  kubectl get "${D}" -n "${NS}" -o json > "${TMP}/deploy.json"
  if ! ./scripts/check.sh "${TMP}/deploy.json"; then
    FAILED=1
  fi
  echo ""
done

exit "${FAILED}"
