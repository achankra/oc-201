# OC-201 lab code

Lab code for OC-201, Cloud Native Platform Engineering with OpenChoreo, from the Platform Engineering Academy by Platformetrics in collaboration with WSO2/OpenChoreo. Each folder belongs to one lab in the workbook. You run it on your own machine, next to the k3d cluster with OpenChoreo v1.3.1 from the pre-work.

Most labs start with a small local demo of one idea: device sign-in, policy checks, traffic rules, events, error budgets. The demos need no cluster. The rest of the lab does the same thing in OpenChoreo, so you recognize the idea when you meet it there.

## Setup

The workbook pre-work installs every tool and the cluster. For the lab code:

```
git clone https://github.com/achankra/oc-201.git ~/oc-201-labs
cd ~/oc-201-labs
python3 -m venv .venv
source ~/oc-201-labs/.venv/bin/activate
pip install pyyaml
```

Every command in the workbook and in these READMEs uses `~/oc-201-labs`. If the repository is somewhere else, link it: `ln -s "/path/to/oc-201-labs" ~/oc-201-labs`.

On a Mac, let pasted blocks contain `#` comment lines; without this, zsh tries to run them:

```
echo 'setopt interactivecomments' >> ~/.zshrc && source ~/.zshrc
```

## Folders

| Folder | Lab | What it holds |
|---|---|---|
| `lab2-device-login` | Lab 2, occ login and access roles | The device authorization flow in miniature, and the role and binding that grant a team access |
| `lab3-policy-check` | Lab 3, policy check, governed cell, runtime view | A Rego policy for files and live Deployments, the governed ClusterProjectType, the project script, and the declared-versus-observed comparison |
| `lab4-agents` | Lab 4, connect an AI agent to OpenChoreo | Registration of both MCP servers (service token by default), skill installation, the prompts, and a no-agent path |
| `lab5` | Lab 5, a ComponentType and a Trait | A README. The workbook steps write the exported type, the scaffold and the component here |
| `lab6-traffic-control` | Lab 6, build, promote and diagnose | Traffic guardrails, canary and blue/green routing, an HTTPRoute generator, and the wirelogs and web shell exercises |
| `lab7-events` | Lab 7, fan out | One deployment event, independent consumers |
| `lab7-sre-agent` | Lab 7, alert and SRE agent | The notification channel, the alert rule, the incident setting, the SRE agent setup, Claude Code as the SRE, and a local stand-in |
| `lab7-slo` | Lab 7, stretch | An SLO, an error budget, and a request log from your own greeter scored against both |

Lab 1 uses only OpenChoreo, so it has no folder. Some steps write files into these folders as you go, such as `lab3-project.yaml`, the Lab 5 YAML and `traffic-live.log`. They are your own lab output, and git ignores them.

## What you need

- Python 3.9 or newer, with PyYAML in `.venv` for labs 5, 6 and 7
- `kubectl` and `helm` pointed at the k3d cluster
- The `occ` CLI, v1.3.1, from github.com/openchoreo/openchoreo/releases/tag/v1.3.1
- OPA for lab 3: `brew install opa`
- Node.js 18 or newer, for the skills in lab 4
- An AI coding agent for lab 4. The workbook uses Claude Code; Codex CLI, Cursor, Gemini CLI, OpenCode CLI and VS Code with GitHub Copilot also work. Without one, use `lab4-agents/no-agent/run-reads.sh`.
- For the SRE agent in lab 7, an OpenAI API key. Without one, use Claude Code through the MCP servers, or `lab7-sre-agent/simulate/`.

## Known issues on v1.3.1

The labs already work around each of these. If you see one of the symptoms, the last column says what fixes it and which lab covers it.

| Symptom | Cause | Fix, and where |
|---|---|---|
| zsh runs `#` lines as commands | Comments are off in interactive zsh | `setopt interactivecomments`, pre-work |
| A new project gets no cell namespaces and nothing deploys into it | Cells come only from ProjectReleaseBindings | `create-governed-project.sh` creates one per pipeline environment, Lab 3 |
| `resourcequotas "cell-quota" is forbidden` | The data plane agent cannot manage ResourceQuotas | ClusterRole and binding for `cluster-agent-dataplane`, Lab 3 part C |
| A pod outside the cell cannot reach a component | OpenChoreo puts an ingress NetworkPolicy on every component | Expected; call through the gateway. Lab 3 part E and Lab 6 part B |
| `pods "curl-test" already exists` | A test pod from an earlier run | Each block deletes it first with `--ignore-not-found` |
| Claude Code browser sign-in finishes but `/mcp` still says "needs authentication" | OAuth with the bundled identity provider does not complete in recent Claude Code versions | `register-claude-code-token.sh`, service token, Lab 4 |
| `MCP server openchoreo-cp already exists`, or servers work in one folder only | Earlier registrations at local or user scope | The scripts remove both and register for the user, Lab 4 |
| The agent runs `kubectl` instead of MCP tools | The servers were added after the session started | Restart Claude Code; every prompt ends "Use only the OpenChoreo MCP tools", Lab 4 |
| `A notification channel is mandatory for alert rules` | The alert-rule trait needs a default channel in the environment | Apply `notification-channel-webhook.yaml` first, Labs 5 and 7 |
| The route dry-run fails against the gateway | `kubectl get gateways -A` lists one per plane; components use the data plane's | `GW_NS=openchoreo-data-plane`, Lab 6 |
| `configs/canary-broken.yaml` not found | The broken copy is generated, not shipped | Each block creates it with `sed` first, Lab 6 |
| `/proc/net/tcp` shows no listener | The greeter listens on an IPv6 socket | Read `/proc/net/tcp6`; port 9090 is `2382`, Lab 6 |
| No `sre-agent` pod with a Claude key | The SRE agent supports OpenAI only | Claude Code as the SRE through MCP, Lab 7 |
| The live SLO run says `payments-api` | The sample SLO names a sample service | Score against `slo-greeter.yaml`, Lab 7 stretch |

## Good to know

- Your output will not match the READMEs character for character. Names, timestamps and generated IDs differ on every machine, and the canary in Lab 6 routes requests at random.
- The identity provider in Lab 2 signs its tokens with a secret written in its source code. That is fine for a demo on your own machine and never acceptable in a real system. It uses ports 8081 and 8082, so stop anything already using them before Lab 2.
- On the local install, the wirelogs and the runtime view of the cell diagram stay empty. They need the Cilium network plugin, which the local install does not include. The labs show the same results with `kubectl`.
- In Lab 4 your AI agent connects as `service_mcp_client`, which has the `admin` role on the local install. The audit log records the agent's calls under that name, not yours. On a real platform, give an agent the narrowest role that does the job.
- If you use an API key in Lab 4 or Lab 7, never commit it to a repository.
