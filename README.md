# OC-201 lab code

Lab code for OC-201, Cloud Native Platform Engineering with OpenChoreo, from the Platform Engineering Academy by Platformetrics in collaboration with WSO2/OpenChoreo. Each folder belongs to one lab in the workbook. You run it on your own machine, next to the k3d cluster with OpenChoreo v1.3.2 from the pre-work.

**Start with [WORKBOOK.md](WORKBOOK.md).** Each module folder has two editions of its step-by-step workbook: `WORKBOOK-local.md` for OpenChoreo on your own machine, the main path for the course, and `WORKBOOK-sandbox.md` for the WSO2 OpenChoreo Sandbox. Every code block has a copy button.

New to the vocabulary? [TERMINOLOGY.md](TERMINOLOGY.md) explains each OpenChoreo term, what the industry usually does instead, and what OpenChoreo changes.

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
| `prework` | Pre-work | The workbook for installing the tools and the cluster |
| `lab1` | Lab 1, verify the install, deploy and trace | The workbook only; Lab 1 uses only OpenChoreo |
| `lab2-device-login` | Lab 2, occ login and access roles | The device authorization flow in miniature, and the role and binding that grant a team access |
| `lab3-policy-check` | Lab 3, policy check, governed cell, runtime view | A Rego policy for files and live Deployments, the governed ClusterProjectType, the project script, and the declared-versus-observed comparison |
| `lab4-agents` | Lab 4, connect an AI agent to OpenChoreo | Registration of both MCP servers (service token by default), skill installation, the prompts, and a no-agent path |
| `lab5` | Lab 5, a ComponentType and a Trait | A README and reference copies. You create the exported type, the scaffold and the component here as you run the steps |
| `lab6-traffic-control` | Lab 6, build, promote and diagnose | Traffic guardrails, canary and blue/green routing, an HTTPRoute generator, and the wirelogs and web shell exercises |
| `lab7` | Lab 7, observe, alert and scale out | The workbook for Lab 7, which uses the three folders below |
| `lab7-events` | Lab 7, fan out | One deployment event, independent consumers |
| `lab7-sre-agent` | Lab 7, alert and SRE agent | The notification channel, the alert rule, the incident setting, the SRE agent setup, Claude Code as the SRE, and a local stand-in |
| `lab7-slo` | Lab 7, stretch | An SLO, an error budget, and a request log from your own greeter scored against both |

Some steps write files into these folders as you go, such as `lab3-project.yaml`, the Lab 5 YAML and `traffic-live.log`. They are your own lab output, and git ignores them. Each lab that creates files has a `reference/` folder with a copy of each one from a working run: if a step fails or you fall behind, copy the file into place and carry on.

## What you need

- Python 3.9 or newer, with PyYAML in `.venv` for labs 5, 6 and 7
- `kubectl` and `helm` pointed at the k3d cluster
- The `occ` CLI, v1.3.2, from github.com/openchoreo/openchoreo/releases/tag/v1.3.2. v1.3.2 has no API changes from v1.3.1 and includes the fix for the eMudhra emSign root CA security issue
- OPA for lab 3: `brew install opa`
- Node.js 18 or newer, for the skills in lab 4
- An AI coding agent for lab 4. The workbook uses Claude Code; Codex CLI, Cursor, Gemini CLI, OpenCode CLI and VS Code with GitHub Copilot also work. Without one, use `lab4-agents/no-agent/run-reads.sh`.
- For the SRE agent in lab 7, an OpenAI API key, or another provider behind an OpenAI-compatible gateway. Without one, use Claude Code through the MCP servers, or `lab7-sre-agent/simulate/`.

## When the cluster does not start or answer

After a restart, a sleep or a Docker restart, the cluster may be stopped even though nothing reports an error. The signs: `The connection to the server 127.0.0.1 was refused`, `Cannot connect to the Docker daemon`, the portal does not load, or `./scripts/check-mcp.sh` in Lab 4 prints `NO ANSWER` for both servers.

Find where it stops:

```
docker info > /dev/null && echo "Docker OK" || echo "Docker is not running"
k3d cluster list
kubectl get nodes
curl -s -o /dev/null -w "API %{http_code}\n" http://api.openchoreo.localhost:8080/
```

**Docker is not running.** Start it, then the cluster, and wait for the control plane:

```
# macOS, Apple silicon. Intel Mac: colima start --cpu 4 --memory 8
colima start --vm-type=vz --vz-rosetta --cpu 4 --memory 8
# Linux: sudo systemctl start docker. Windows: open Docker Desktop
k3d cluster start openchoreo
kubectl wait -n openchoreo-control-plane --for=condition=available --timeout=300s deployment --all
```

**Docker runs, but `kubectl get nodes` fails or shows NotReady.** Run `k3d cluster start openchoreo`, wait a minute, and check again.

**`k3d cluster start` fails with `Bind for 0.0.0.0:8080 failed: port is already allocated`.** Something else took port 8080 while the cluster was stopped, so the cluster's load balancer cannot start, and `kubectl` is then refused on port 6550. Find what holds the port:

```
docker ps --format '{{.Names}}\t{{.Ports}}' | grep 8080
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

Stop that container with `docker stop NAME`, or quit that program (`kill PID` with the PID `lsof` printed). Then run `k3d cluster start openchoreo` again. The cluster also uses ports 6550, 11080 and 19080; the same steps apply if one of them is named.

**The nodes are Ready, but the API line prints `000`.** Some pods have not come back yet. List them:

```
kubectl get pods -A | grep -v -E 'Running|Completed'
```

Wait a few minutes and run it again; the list should shrink to nothing. A pod that stays in `CrashLoopBackOff` or `Pending` usually means Docker has too little memory: give it at least 8 GB, as in the pre-work, and restart Docker.

**`k3d cluster list` is empty.** The cluster was deleted. Create it again with the pre-work's install step.

**Portal sign-in fails with `Authentication failed, Failed to obtain access token`, and the catalog stays empty.** The cluster was restarted without k3d, for example by restarting Docker or Colima, and CoreDNS lost the `host.k3d.internal` entry that k3d adds on `k3d cluster start`. The installer's DNS rewrite sends every `*.openchoreo.localhost` name inside the cluster to `host.k3d.internal`, so the portal can no longer reach the identity provider at `thunder.openchoreo.localhost`; its log shows `ENOTFOUND thunder.openchoreo.localhost`. Check the entry:

```
kubectl -n kube-system get configmap coredns -o jsonpath='{.data.NodeHosts}'; echo
```

If no line names `host.k3d.internal`, stop and start the cluster through k3d, which adds it back:

```
k3d cluster stop openchoreo
k3d cluster start openchoreo
kubectl wait -n openchoreo-control-plane --for=condition=available --timeout=300s deployment --all
```

Confirm the name resolves inside the cluster, then sign in again in a private window:

```
kubectl run dns-test --restart=Never --image=busybox:1.36 -- nslookup -type=a thunder.openchoreo.localhost
sleep 10; kubectl logs dns-test; kubectl delete pod dns-test
```

The lookup prints an `Address:` line. After any restart, start the cluster with `k3d cluster start openchoreo` rather than restarting its container.

**Re-running the installer fails at the control plane with `UPGRADE FAILED: conflict occurred while applying object openchoreo-control-plane/cluster-gateway-ca`.** An earlier `kubectl apply` wrote the cluster gateway's CA certificate into this ConfigMap, and Helm 4 applies upgrades server-side, so it will not overwrite a field that another tool owns. Everything before this step is fine. Delete the ConfigMap and run the same install command again:

```
kubectl delete configmap cluster-gateway-ca -n openchoreo-control-plane
```

The control plane does not need this copy after the first install, and the installer does not recreate it. Each plane keeps its own copy, which you can check is still there:

```
kubectl get configmap -A | grep cluster-gateway-ca
```

It lists the data, workflow and observability plane namespaces. The conflict comes from Helm 4, which Homebrew installs (`helm version --short`); with Helm 4, delete the ConfigMap before each re-run.

When the API line prints a status code such as `200` or `404`, the platform is up. Carry on from the step you were on.

## Known issues on v1.3

The course runs on v1.3.2. Every row holds on v1.3.1 and v1.3.2 unless it says otherwise. The labs already work around each of these. If you see one of the symptoms, the last column says what fixes it and which lab covers it.

| Symptom | Cause | Fix, and where |
|---|---|---|
| The portal, `kubectl` or the MCP servers do not answer after a restart | The cluster or Docker is stopped | See [When the cluster does not start or answer](#when-the-cluster-does-not-start-or-answer) |
| Portal sign-in fails with `Failed to obtain access token` after a Docker or Colima restart | CoreDNS lost the `host.k3d.internal` entry, so the portal cannot reach the identity provider | `k3d cluster stop openchoreo`, then `k3d cluster start openchoreo`; see [When the cluster does not start or answer](#when-the-cluster-does-not-start-or-answer) |
| Re-running the installer fails with `UPGRADE FAILED: conflict ... cluster-gateway-ca` | An earlier `kubectl apply` owns the ConfigMap's `ca.crt`, and Helm 4 will not overwrite it | Delete the ConfigMap and re-run the installer; the planes keep their own copies; see [When the cluster does not start or answer](#when-the-cluster-does-not-start-or-answer) |
| zsh runs `#` lines as commands | Comments are off in interactive zsh | `setopt interactivecomments`, pre-work |
| A new project gets no cell namespaces and nothing deploys into it | Cells come only from ProjectReleaseBindings, and a project applied with `kubectl` gets none | `create-governed-project.sh` creates one per pipeline environment, Lab 3 |
| `resourcequotas "cell-quota" is forbidden` | The cluster agent cannot manage ResourceQuotas on any install, out of the box | ClusterRole and binding for `cluster-agent-dataplane`, Lab 3 part C |
| A pod outside the cell cannot reach a component | OpenChoreo puts an ingress NetworkPolicy on every component | Expected; call through the gateway. Lab 3 part E and Lab 6 part B |
| `pods "curl-test" already exists` | A test pod from an earlier run | Each block deletes it first with `--ignore-not-found` |
| Claude Code browser sign-in finishes but `/mcp` still says "needs authentication" | OAuth with the bundled identity provider does not complete in recent Claude Code versions | `register-claude-code-token.sh`, service token, Lab 4 |
| `MCP server openchoreo-cp already exists`, or servers work in one folder only | Earlier registrations at local or user scope | The scripts remove both and register for the user, Lab 4 |
| The agent runs `kubectl` instead of MCP tools | The servers were added after the session started | Restart Claude Code; every prompt ends "Use only the OpenChoreo MCP tools", Lab 4 |
| `A notification channel is mandatory for alert rules` | The alert-rule trait needs a default channel in the environment | Apply `notification-channel-webhook.yaml` first, Labs 5 and 7 |
| The route dry-run fails against the gateway | `kubectl get gateways -A` lists one per plane; components use the data plane's | `GW_NS=openchoreo-data-plane`, Lab 6 |
| `configs/canary-broken.yaml` not found | The broken copy is generated, not shipped | Each block creates it with `sed` first; or run `cp reference/canary-broken.yaml configs/` in `lab6-traffic-control`, Lab 6 |
| `/proc/net/tcp` shows no listener | The greeter listens on an IPv6 socket | Read `/proc/net/tcp6`; port 9090 is `2382`, Lab 6 |
| No `sre-agent` pod with a Claude key | The SRE agent speaks the OpenAI API; it works with OpenAI, or with another provider through an OpenAI-compatible gateway, not with a Claude key or login | An OpenAI-compatible key, or Claude Code as the SRE through MCP, Lab 7 |
| The SRE agent fails with a newer OpenAI model | On v1.3.1, models from gpt-5.6 onward fail | Use v1.3.2, which fixes it, or `RCA_MODEL=gpt-5.4` as Lab 7 does |
| The Lab 4 audit log shows none of the agent's reads | The audit log records changes only (create, update, delete), not reads, even denied ones | Expected; prompt 5 creates a project so there is an entry to find, Lab 4 |
| A type change creates no new release | Only components with `autoDeploy: true` move to a new release on their own; it is off by default | The Lab 5 component sets it, Lab 5 part E |
| A component or type applies cleanly but does not work | Most validation errors show in the object's status, not at apply | `kubectl get <kind> <name> -o jsonpath='{.status.conditions}'`, Labs 3 and 5 |
| The live SLO run says `payments-api` | The sample SLO names a sample service | Score against `slo-greeter.yaml`, Lab 7 stretch |

## About the book

The course material draws on The Platform Engineer's Handbook by Ajay Chankramath (Packt, 2026), alongside the OpenChoreo v1.3 documentation. Everything a lab needs is in this repository, so the book is not mandatory, but we recommend getting it to go deeper: [peh-packt.platformetrics.com](https://peh-packt.platformetrics.com) or [Amazon](https://www.amazon.com/dp/B0FR59Z7Q2).

## Good to know

- Your output will not match the READMEs character for character. Names, timestamps and generated IDs differ on every machine, and the canary in Lab 6 routes requests at random.
- The identity provider in Lab 2 signs its tokens with a secret written in its source code. That is fine for a demo on your own machine and never acceptable in a real system. It uses ports 8081 and 8082, so stop anything already using them before Lab 2.
- On the local install, the wirelogs and the runtime view of the cell diagram stay empty. Wirelogs need the Cilium network plugin, which the local install does not include, and the runtime view also needs a metrics module. Wirelogs show traffic only from the moment you open them. The labs show the same results with `kubectl`.
- In Lab 4 your AI agent connects as `service_mcp_client`, which has the `admin` role on the local install. The audit log records the changes the agent makes under that name, not yours; it does not record reads. On a real platform, give an agent the narrowest role that does the job.
- If you use an API key in Lab 4 or Lab 7, never commit it to a repository.
