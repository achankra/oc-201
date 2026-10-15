# Lab 4: Connect an AI agent to OpenChoreo

*OC-201 workbook, local install edition. Using the sandbox instead? See [WORKBOOK-sandbox.md](WORKBOOK-sandbox.md).*

**Goal:** Connect an AI coding agent to both OpenChoreo MCP servers, install the OpenChoreo skills, work with the service from Lab 1, and find the agent's own calls in the audit log.

## A. The two servers

| Server | Url | Covers |
|---|---|---|
| `openchoreo-cp` | `http://api.openchoreo.localhost:8080/mcp` | Namespaces, projects, components, workloads, release bindings, builds, environments, planes, roles |
| `openchoreo-obs` | `http://observer.openchoreo.localhost:11080/mcp` | Logs, metrics, traces, alerts, incidents, cost insights, audit logs |

### 1. Check that both answer

```bash
cd ~/oc-201-labs/lab4-agents
./scripts/check-mcp.sh
```

Each line should start with `HTTP` and a status code. `NO ANSWER` means that plane is not running.

## B. Register and connect

### 2. Pick the block for your agent

Claude Code and Codex CLI use a service token from the client `service_mcp_client`, which this install ships with the `admin` role. That route needs no browser sign-in. Browser sign-in is optional where the agent supports it.

| Agent | Browser Sign-In | Client Credentials |
|---|---|---|
| Claude Code | yes | yes |
| Cursor | yes | yes |
| Gemini CLI | yes | yes |
| OpenCode CLI | yes | yes |
| Codex CLI | no | yes |
| VS Code with GitHub Copilot | no | yes |

### 3. Register the servers

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

```bash
# Claude Code, default route: service token, no browser sign-in, lasts 24 hours
cd ~/oc-201-labs/lab4-agents
./scripts/register-claude-code-token.sh
```

```bash
# Claude Code, optional route: browser sign-in instead of the token
cd ~/oc-201-labs/lab4-agents
./scripts/register-claude-code.sh
claude
# inside Claude Code: /mcp, select openchoreo-cp, press Enter, choose Authenticate
# sign in, then repeat for openchoreo-obs
```

```bash
# Gemini CLI
gemini mcp add --transport http openchoreo-cp http://api.openchoreo.localhost:8080/mcp
gemini mcp add --transport http openchoreo-obs \
  http://observer.openchoreo.localhost:11080/mcp
gemini
# then, inside Gemini CLI: /mcp auth openchoreo-cp  and  /mcp auth openchoreo-obs
```

```bash
# Cursor: writes ~/.cursor/mcp.json only if it does not exist yet
mkdir -p ~/.cursor
[ -f ~/.cursor/mcp.json ] && echo "mcp.json exists: add the two servers by hand" || \
printf '%s\n' '{"mcpServers": {
 "openchoreo-cp": {"url": "http://api.openchoreo.localhost:8080/mcp"},
 "openchoreo-obs": {"url": "http://observer.openchoreo.localhost:11080/mcp"}}}' \
  > ~/.cursor/mcp.json
```

```bash
# Codex CLI: client credentials. The token lasts one hour, so run the export again after
mkdir -p ~/.codex
touch ~/.codex/config.toml
grep -q openchoreo-cp ~/.codex/config.toml || \
  cat ~/oc-201-labs/lab4-agents/config/codex-config.toml >> ~/.codex/config.toml
export OPENCHOREO_MCP_TOKEN=$(curl -s -u service_mcp_client:service_mcp_client_secret \
  -d grant_type=client_credentials http://thunder.openchoreo.localhost:8080/oauth2/token \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
codex
```

The token script replaces any earlier registration, registers both servers for your user so they work from any folder, and can be run again for a fresh token. With browser sign-in, use `admin@openchoreo.dev` / `Admin@123`; with recent Claude Code versions the sign-in can finish in the browser while `/mcp` still says "needs authentication", so use the token script if that happens. Gemini CLI's redirect `http://localhost:7777/oauth/callback` must be on the OAuth app's allowed list or sign-in fails. The client `service_mcp_client` already has the `admin` role on this install. **OpenCode CLI:** run `opencode mcp add` twice and answer: name `openchoreo-cp` (then `openchoreo-obs`), the URL from the table, OAuth `yes`, client ID `user_mcp_client`, client secret `no`.

## C. Confirm the connection, then add skills

### 4. Check that both servers are connected

```bash
claude mcp list | grep openchoreo
claude
```

Both lines end in `Connected`. Then start Claude Code (restart it if it was already running) and run `/mcp`: both servers show a check mark and a tool count. Do not start part D until they do. An agent without the servers falls back to `kubectl`, and those calls never reach the OpenChoreo audit log.

### 5. Install the OpenChoreo skills

```bash
cd ~/oc-201-labs/lab4-agents
./scripts/install-skills.sh
npx skills list
npx skills add openchoreo/skills --list
```

This installs `openchoreo-developer` and `openchoreo-platform-engineer`. The last command lists every skill in the repository, including the GitOps variants.

## D. Work with your service

### 6. Give the agent the prompts, in order

Paste each block into your agent as its own prompt. The same text is in `prompts/lab4-prompts.md`.

Paste each block into your agent as its own prompt.

```text
List the namespaces, projects and components you can see in OpenChoreo. Use only the OpenChoreo MCP tools.
```

```text
Explain the greeter-service component: its ComponentType, its endpoints, and the environments it is bound to. Use only the OpenChoreo MCP tools.
```

```text
Read the last 50 log lines for greeter-service and summarize anything unusual. Use only the OpenChoreo MCP tools.
```

```text
List the release bindings for greeter-service and tell me which release each environment is running. Use only the OpenChoreo MCP tools.
```

```text
Show the audit log entries for the calls you just made. Use only the OpenChoreo MCP tools.
```

Your agent shows each tool call, for example `Called openchoreo-cp 4 times`. Prompts 1, 2 and 4 use tools on `openchoreo-cp`; prompts 3 and 5 use tools on `openchoreo-obs`. If you see `kubectl` instead, stop the agent with Esc and go back to step 4.

### 7. Compare the entries with the calls

```bash
occ auditlogs --since 1h
occ auditlogs --since 1h --result denied
```

Audit logs record calls made through the REST API and through MCP. The entries should match the agent's calls from prompts 1 to 4. With the token route the caller is `service_mcp_client`, not your user: the agent is an identity of its own, authorized by its own role binding. Giving an agent access is a role binding like any other, so give it the least access that does the job. A denied call means the role bound to that identity does not allow it; bind one that does, as in Lab 2.

### 8. No agent available

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

The same reads with occ and kubectl, covering prompts 1, 2, 4 and 5, plus the logs for prompt 3:

```bash
cd ~/oc-201-labs/lab4-agents
./no-agent/run-reads.sh default greeter-service
occ component logs greeter-service -n default -p default --env development --tail 50
```

The occ calls appear in the audit log; the kubectl calls go to the Kubernetes API and do not.

### 9. Stretch: skills on and off

Paste this prompt with the skills installed:

Paste each block into your agent as its own prompt.

```text
Draft a Component for a new service called inventory-api using this platform's own ComponentType schema. Show the YAML; do not apply it.
```

Then remove the skills, paste the same prompt in a new session, compare the field names, and put the skills back:

```bash
cd ~/oc-201-labs/lab4-agents
npx skills remove openchoreo-developer openchoreo-platform-engineer
# ...ask again in a new agent session, then:
./scripts/install-skills.sh
```

## Checkpoint

- [ ] `claude mcp list` shows both OpenChoreo servers as Connected, or you ran the no-agent reads
- [ ] The agent's answers come from MCP tool calls, not `kubectl`
- [ ] The agent names `greeter-service`, its ComponentType and the environments it is bound to
- [ ] The log summary matches what you see in the portal
- [ ] The audit entries match the calls the agent made

## Troubleshooting

- `needs authentication` in `/mcp`: run `~/oc-201-labs/lab4-agents/scripts/register-claude-code-token.sh`, then restart Claude Code.
- Sign-in finishes in the browser but the server still needs authentication: use the token script; browser sign-in does not complete with some Claude Code versions.
- `already exists in user config`: an old copy of the script. The current scripts replace earlier registrations; or run `claude mcp remove openchoreo-cp -s user` and `claude mcp remove openchoreo-obs -s user` first.
- Servers registered but missing in another folder: they were registered for one folder only. Run the token script; it registers them for your user.
- The agent runs `kubectl`: the servers are not connected in that session. Restart Claude Code and check `/mcp`.
- A call is denied: run `occ auditlogs --since 1h --result denied` and bind a role that allows the action, as in Lab 2.
- Tools worked and then stop: the token expired. Run the token script again (24-hour token); for Codex, run the `export OPENCHOREO_MCP_TOKEN=...` lines again.
- Log prompt returns nothing: run `kubectl get pods -n openchoreo-observability-plane`.

---

Previous: [Lab 3](../lab3-policy-check/WORKBOOK-local.md) · [All modules](../WORKBOOK.md) · Next: [Lab 5](../lab5/WORKBOOK-local.md)
