#!/usr/bin/env bash
# Register both OpenChoreo MCP servers in Claude Code with a service token.
# This is the default route for the lab: no browser sign-in.
#
# The token comes from the service client service_mcp_client, which the local
# k3d install ships with the admin role. It lasts 24 hours; run this script again
# to get a new one. Safe to run more than once: it replaces earlier registrations.
#
# Override for another install:
#   CP_URL=... OBS_URL=... TOKEN_URL=... CLIENT_ID=... CLIENT_SECRET=... ./scripts/register-claude-code-token.sh
set -eu

CP_URL="${CP_URL:-http://api.openchoreo.localhost:8080/mcp}"
OBS_URL="${OBS_URL:-http://observer.openchoreo.localhost:11080/mcp}"
TOKEN_URL="${TOKEN_URL:-http://thunder.openchoreo.localhost:8080/oauth2/token}"
CLIENT_ID="${CLIENT_ID:-service_mcp_client}"
CLIENT_SECRET="${CLIENT_SECRET:-service_mcp_client_secret}"

command -v claude >/dev/null 2>&1 || { echo "claude was not found on your PATH. Install Claude Code first." >&2; exit 1; }

TOKEN="$(curl -s -u "$CLIENT_ID:$CLIENT_SECRET" -d grant_type=client_credentials "$TOKEN_URL" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')"
if [ -z "$TOKEN" ]; then
  echo "Could not get a token from $TOKEN_URL. Check that the cluster is running." >&2
  exit 1
fi
echo "Got a token for $CLIENT_ID (${#TOKEN} characters)."

for scope in local user; do
  claude mcp remove openchoreo-cp -s "$scope" >/dev/null 2>&1 || true
  claude mcp remove openchoreo-obs -s "$scope" >/dev/null 2>&1 || true
done

claude mcp add --scope user --transport http openchoreo-cp "$CP_URL" \
  --header "Authorization: Bearer $TOKEN"
claude mcp add --scope user --transport http openchoreo-obs "$OBS_URL" \
  --header "Authorization: Bearer $TOKEN"

echo
claude mcp list | grep openchoreo
echo
echo "Both servers should show Connected. Start (or restart) Claude Code to use them."
