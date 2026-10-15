#!/usr/bin/env bash
# Check that both OpenChoreo MCP endpoints answer.
# Any HTTP status means the server is up. 000 means nothing answered.
#
# Override the URLs for an install that is not the default k3d setup:
#   CP_URL=https://... OBS_URL=https://... ./scripts/check-mcp.sh
set -u

CP_URL="${CP_URL:-http://api.openchoreo.localhost:8080/mcp}"
OBS_URL="${OBS_URL:-http://observer.openchoreo.localhost:11080/mcp}"

status=0
for entry in "openchoreo-cp|$CP_URL" "openchoreo-obs|$OBS_URL"; do
  name="${entry%%|*}"
  url="${entry#*|}"
  code=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' "$url" || true)
  if [ "$code" = "000" ] || [ -z "$code" ]; then
    echo "NO ANSWER  $name  $url"
    status=1
  else
    echo "HTTP $code   $name  $url"
  fi
done

if [ "$status" -ne 0 ]; then
  echo
  echo "At least one server did not answer. Check that the cluster is running and that"
  echo "the control plane and observability plane are installed."
fi
exit "$status"
