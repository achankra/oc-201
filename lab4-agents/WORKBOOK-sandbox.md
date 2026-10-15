# Lab 4: Connect an AI agent to OpenChoreo

*OC-201 workbook, WSO2 sandbox edition. Using the local install instead? See [WORKBOOK-local.md](WORKBOOK-local.md).*

**Goal:** Connect an AI coding agent to both OpenChoreo MCP servers, install the OpenChoreo skills, work with the service from Lab 1, and find the agent's own calls in the audit log.

## Start of a sandbox session

Paste into the sandbox terminal in your browser, never into a terminal on your own machine. Skip this box if you are still in the session where you ran the previous lab; pasting it twice does no harm. In a new session, paste the setup block. It clones the lab code, sets up Python and OPA, and saves the gateway address for every later block.

```bash
setopt interactivecomments
grep -q interactivecomments ~/.zshrc || echo 'setopt interactivecomments' >> ~/.zshrc
[ -d ~/oc-201-labs ] || git clone https://github.com/achankra/oc-201.git ~/oc-201-labs
cd ~/oc-201-labs
python3 -m venv --without-pip --system-site-packages .venv
mkdir -p ~/bin
curl -fsSL -o ~/bin/opa \
  https://github.com/open-policy-agent/opa/releases/latest/download/opa_linux_amd64_static
chmod +x ~/bin/opa
GWIP=$(kubectl get svc gateway-default -n openchoreo-data-plane -o jsonpath='{.spec.clusterIP}')
sed -i -e '/^export GWADDR=/d' -e '/^export DEVHOST=/d' -e '/^export PATH=.HOME.bin/d' ~/.zshrc
echo 'export PATH=$HOME/bin:$PATH' >> ~/.zshrc
echo "export GWADDR=$GWIP:9080" >> ~/.zshrc
echo "export DEVHOST=development-default.demo.openchoreo.wso2.com" >> ~/.zshrc
source ~/.zshrc
deactivate 2>/dev/null
export PATH=$HOME/bin:$PATH
source ~/oc-201-labs/.venv/bin/activate
echo "gateway $GWADDR, host $DEVHOST"
opa version | head -1
```

```bash
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.2/samples
kubectl apply -f $BASE/from-image/go-greeter-service/greeter-service.yaml
kubectl wait --for=condition=Ready component/greeter-service -n default --timeout=180s
```

The second block redeploys the Lab 1 greeter, which this lab uses.

## A. The two servers

| Server | Url | Covers |
|---|---|---|
| `openchoreo-cp` | `https://api.demo.openchoreo.wso2.com/mcp` | Namespaces, projects, components, workloads, release bindings, builds, environments, planes, roles |
| `openchoreo-obs` | `https://observer.demo.openchoreo.wso2.com/mcp` | Logs, metrics, traces, alerts, incidents, cost insights, audit logs |

### 1. Check that both answer

```bash
claude mcp list
claude mcp get openchoreo-cp
```

The sandbox registered both servers at `https://api.demo.openchoreo.wso2.com/mcp` and `https://observer.demo.openchoreo.wso2.com/mcp`. Both show `Connected`.

## B. Register and connect

### 2. Pick the block for your agent

Claude Code, OpenCode and Codex in the sandbox already have both servers. There is nothing to register; on your own cluster this is where the token script runs.

### 3. Register the servers

Check that your key is set (pre-work step 5). The command prints only its first characters.

```bash
echo ${ANTHROPIC_API_KEY:0:7}
```

It prints `sk-ant-`. If it prints nothing, set the key as in pre-work step 5.

## C. Confirm the connection, then add skills

### 4. Check that both servers are connected

```bash
claude mcp list | grep openchoreo
claude
```

Both lines end in `Connected`. Start Claude Code and run `/mcp`: both servers show a tool count. An agent without the servers falls back to `kubectl`, and those calls never reach the OpenChoreo audit log.

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

The sandbox's occ is 1.2.0, which has no `auditlogs` command; it arrived in 1.3. Read the audit log in the console instead: open **Audit Logs** in the left menu and filter on the result. If your console has no Audit Logs page, this version does not record them; mark the step N/A.

Audit logs record calls made through the REST API and through MCP. The entries should match the agent's calls from prompts 1 to 4. Note which identity the entries show: the sandbox chose the credentials its MCP setup uses. The agent is an identity of its own, authorized by its own role binding, so give it the least access that does the job.

### 8. No agent available

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

The same reads with occ and kubectl, covering prompts 1, 2, 4 and 5, plus the logs for prompt 3:

```bash
cd ~/oc-201-labs/lab4-agents
./no-agent/run-reads.sh default greeter-service
occ component logs greeter-service -n default -p default --env development --tail 50
```

Step 5 of the script prints `(command failed)` in the sandbox, because occ 1.2.0 has no `auditlogs`. Read those entries in the console's Audit Logs page instead.

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

- `Connected` missing: start a new session; the sandbox registers the servers when it starts.
- Claude Code asks you to sign in: the key is not set. Run the `export ANTHROPIC_API_KEY=...` line, then start Claude Code again.
- The agent runs `kubectl`: the servers are not connected in that session. Restart Claude Code and check `/mcp`.
- A call is denied: find it in the console's Audit Logs and bind a role that allows the action, as in Lab 2.
- `npx skills` fails: run `npx --yes skills --help` once, then the install script again.

---

Previous: [Lab 3](../lab3-policy-check/WORKBOOK-sandbox.md) · [All modules](../WORKBOOK.md) · Next: [Lab 5](../lab5/WORKBOOK-sandbox.md)
