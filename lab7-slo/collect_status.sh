#!/usr/bin/env bash
# Call a URL several times and print one HTTP status code per line.
# A request with no response prints 000.
#
# usage: ./collect_status.sh URL [COUNT] > traffic-live.log
# Set HOST_HEADER to send a Host header, for a gateway reached by its address
# (the WSO2 sandbox edition of the workbook does this).
set -euo pipefail

URL="${1:-}"
COUNT="${2:-30}"
if [[ -z "${URL}" ]]; then
  echo "usage: ./collect_status.sh URL [COUNT] > traffic-live.log" >&2
  exit 2
fi

ARGS=(-s -o /dev/null -m 5 -w "%{http_code}\n")
if [[ -n "${HOST_HEADER:-}" ]]; then
  ARGS+=(-H "Host: ${HOST_HEADER}")
fi

for _ in $(seq 1 "${COUNT}"); do
  curl "${ARGS[@]}" "${URL}" || true
done
