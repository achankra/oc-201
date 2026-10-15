#!/usr/bin/env bash
# Register both OpenChoreo MCP servers in Claude Code with browser sign-in (optional route).
# If sign-in does not complete, use ./scripts/register-claude-code-token.sh instead.
# --scope user makes them available from any folder, not only the one you run this in.
# After this, start Claude Code, run /mcp, pick each server and sign in.
#
# Defaults match the local k3d install. Override for another install:
#   CP_URL=https://... OBS_URL=https://... CALLBACK_PORT=8075 ./scripts/register-claude-code.sh
set -eu

CP_URL="${CP_URL:-http://api.openchoreo.localhost:8080/mcp}"
OBS_URL="${OBS_URL:-http://observer.openchoreo.localhost:11080/mcp}"
CALLBACK_PORT="${CALLBACK_PORT:-8075}"
CLIENT_ID="${CLIENT_ID:-user_mcp_client}"

if ! command -v claude >/dev/null 2>&1; then
  echo "claude was not found on your PATH. Install Claude Code first, or use the" >&2
  echo "steps for your agent in README.md." >&2
  exit 1
fi

# Replace earlier registrations so the script can be run again.
for scope in local user; do
  claude mcp remove openchoreo-cp -s "$scope" >/dev/null 2>&1 || true
  claude mcp remove openchoreo-obs -s "$scope" >/dev/null 2>&1 || true
done

claude mcp add --scope user --transport http \
  --client-id "$CLIENT_ID" --callback-port "$CALLBACK_PORT" \
  openchoreo-cp "$CP_URL"

claude mcp add --scope user --transport http \
  --client-id "$CLIENT_ID" --callback-port "$CALLBACK_PORT" \
  openchoreo-obs "$OBS_URL"

echo
echo "Both servers are registered. Start Claude Code, run /mcp, select each server"
echo "and sign in when the browser opens."
