#!/usr/bin/env bash
# Evaluate a Deployment manifest (as JSON) against policies/deployment.rego.
set -euo pipefail

cd "$(dirname "$0")/.."

INPUT="${1:-}"
if [[ -z "${INPUT}" ]]; then
  echo "usage: ./scripts/check.sh inputs/<file>.json"
  exit 2
fi

ALLOW=$(opa eval -f raw -d policies/deployment.rego -i "$INPUT" "data.platform.compliance.allow")
echo "allow: ${ALLOW}"

if [[ "${ALLOW}" != "true" ]]; then
  echo ""
  echo "DENY: policy violations:"
  opa eval -f pretty -d policies/deployment.rego -i "$INPUT" "data.platform.compliance.violations"
  exit 1
fi

echo "PASS: compliant"
