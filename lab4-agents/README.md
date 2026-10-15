# Lab 4: connect an agent to OpenChoreo

OpenChoreo ships two MCP servers. Through them an AI coding agent can discover and manage resources, start and watch builds, read logs, metrics, traces, alerts and incidents, and update release bindings. This lab connects an agent of your choice to both servers, installs the OpenChoreo skills, and has the agent work with the service you deployed in Lab 1.

There is no program to run here. The folder holds helper scripts, one config file and the prompts for the lab.

| Path | Purpose |
|---|---|
| `scripts/check-mcp.sh` | Checks that both MCP endpoints answer |
| `scripts/register-claude-code-token.sh` | Registers both servers in Claude Code with a 24-hour service token. The default route |
| `scripts/register-claude-code.sh` | Registers both servers in Claude Code with browser sign-in. Optional |
| `scripts/install-skills.sh` | Installs the developer and platform engineer skills |
| `config/codex-config.toml` | The two server blocks for Codex CLI |
| `prompts/lab4-prompts.md` | The prompts to give the agent, and what to look for |

## Requirements

- The OpenChoreo cluster from the pre-work, with the observability plane installed. The log prompts need it.
- An AI coding agent: Claude Code, Codex CLI, Cursor, Gemini CLI, OpenCode CLI, or VS Code with GitHub Copilot.
- Node.js 18 or newer, for `npx`, which installs the skills.
- The service from Lab 1 still running.

## The two servers

| Server | URL | What it covers |
|---|---|---|
| `openchoreo-cp` | `http://api.openchoreo.localhost:8080/mcp` | Namespaces, projects, components, workloads, release bindings, builds, environments, planes, roles |
| `openchoreo-obs` | `http://observer.openchoreo.localhost:11080/mcp` | Logs, metrics, traces, alerts, incidents, cost insights, audit logs |

On an install that is not the default k3d setup, use your own URLs. Check that both answer:

```
./scripts/check-mcp.sh
```

## 1. Register the servers and sign in

There are two ways to authenticate: a service token from client credentials, or browser sign-in. For Claude Code and Codex CLI the lab uses the service token. Which one each agent supports:

| Agent | Browser sign-in | Client credentials |
|---|---|---|
| Claude Code | yes | yes |
| Cursor | yes | yes |
| Gemini CLI | yes | yes |
| OpenCode CLI | yes | yes |
| Codex CLI | no | yes |
| VS Code with GitHub Copilot | no | yes |

### Claude Code

The default route uses a service token, with no browser sign-in:

```
./scripts/register-claude-code-token.sh
claude
```

In Claude Code, run `/mcp`. Both servers should show a check mark and a tool count. If Claude Code was already running, restart it first.

The token belongs to the service client `service_mcp_client`, which the local install ships with the `admin` role. It lasts 24 hours; run the script again for a new one. The audit log records the agent's calls under that client, not under your user.

Browser sign-in is the optional route: `./scripts/register-claude-code.sh`, then `/mcp`, select each server, press Enter and choose Authenticate. With recent Claude Code versions the sign-in can complete in the browser and the server still shows "needs authentication". If that happens, use the token script.

Both scripts register the servers for your user, so they work from any folder, and both replace earlier registrations, so you can run them again.

### OpenCode CLI

Run `opencode mcp add` twice. At the prompts:

| Prompt | `openchoreo-cp` | `openchoreo-obs` |
|---|---|---|
| Server name | `openchoreo-cp` | `openchoreo-obs` |
| MCP server URL | the control plane URL above | the observer URL above |
| Requires OAuth | yes | yes |
| Client ID | `user_mcp_client` | `user_mcp_client` |
| Client secret | no | no |

### Cursor and Gemini CLI

A browser window opens for sign-in the first time the agent uses a server. Add both servers in the agent's own MCP settings. Gemini CLI uses `http://localhost:7777/oauth/callback` as its redirect address by default. That address has to be on the allowed redirect list of the OAuth application, or sign-in fails.

### Codex CLI and VS Code with GitHub Copilot: client credentials

These two use a bearer token from the client `service_mcp_client`. A client credentials client sees nothing until it has a role binding, the same as any other user; on the local install this one already has `admin`. For Codex CLI the token lasts one hour, so run the `export` again when the tools stop working:

```
mkdir -p ~/.codex
touch ~/.codex/config.toml
grep -q openchoreo-cp ~/.codex/config.toml || \
  cat ~/oc-201-labs/lab4-agents/config/codex-config.toml >> ~/.codex/config.toml
export OPENCHOREO_MCP_TOKEN=$(curl -s -u service_mcp_client:service_mcp_client_secret \
  -d grant_type=client_credentials http://thunder.openchoreo.localhost:8080/oauth2/token \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
codex
```

## 2. Install the skills

```
./scripts/install-skills.sh
```

This installs `openchoreo-developer` and `openchoreo-platform-engineer`. They teach the agent how OpenChoreo works so it does not guess. To see every skill in the repository, including the GitOps variants:

```
npx skills add openchoreo/skills --list
```

The developer skill needs the MCP servers configured. The platform engineer skill also needs `kubectl` and Helm.

## 3. Work with your service

Check that both servers are connected:

```
claude mcp list | grep openchoreo
```

Both lines end in `Connected`. Start Claude Code, or restart it if it was already running; it reads the server list only at start. Run `/mcp` and check both servers show a tool count. Then use the prompts in `prompts/lab4-prompts.md`, in order. Each asks the agent to use only the OpenChoreo MCP tools, so it does not fall back to `kubectl`, whose calls never reach the audit log. They ask the agent to list what is running, explain the Lab 1 service, read its recent logs and list its release bindings.

## 4. Find the agent's actions in the audit log

The last prompt asks the agent to show its own calls from the audit log. Audit logs record calls made through the REST API and through MCP. The agent reads them with the observability server.

## No agent available

If you do not have a coding agent, run the same reads with `occ` and `kubectl`:

```
./no-agent/run-reads.sh default greeter-service
```

It covers prompts 1, 2, 4 and 5. For prompt 3: `occ component logs greeter-service -n default -p default --env development --tail 50`. Audit logs cover calls made through the OpenChoreo API, so the `occ` calls appear and the `kubectl` calls do not. You get the same data, but you do not see how an agent uses the tools.

## What you should see

- Both servers show as connected in your agent.
- The agent names your Lab 1 service, its ComponentType and the environments it is bound to.
- The log summary matches what you see in the portal.
- The audit entries match the calls the agent made.

## If something fails

- No tools appear: run `./scripts/register-claude-code-token.sh` and restart Claude Code, or check that both URLs answer with `./scripts/check-mcp.sh`.
- `MCP server openchoreo-cp already exists`: an old copy of a script. The current scripts remove earlier registrations first; or run `claude mcp remove openchoreo-cp -s user` and `claude mcp remove openchoreo-obs -s user`.
- Servers work in one folder only: they were registered for that folder. Run the token script; it registers them for your user.
- Sign-in completes in the browser but the server still says "needs authentication": use `./scripts/register-claude-code-token.sh`.
- The agent runs `kubectl` instead of MCP tools: the servers are not connected. Fix that first; add "Use only the OpenChoreo MCP tools" to the prompt.
- A call is denied: the role bound to your sign-in does not allow that action. Bind a role that does, as in Lab 2.
- Tools work and then stop: the token expired. Run `./scripts/register-claude-code-token.sh` again (24 hours), or the Codex `export` line (one hour).

## How it maps to OpenChoreo

The agent is a user of the platform. It signs in through the same identity provider, it is authorized by the same roles and bindings, and what it does is recorded in the same audit log. Giving an agent access is a role binding like any other, so give it the least access that does the job.
