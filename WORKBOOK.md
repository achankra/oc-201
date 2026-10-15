# OC-201 workbook

Cloud Native Platform Engineering with OpenChoreo. Seven hands-on labs, with a pre-work module before Day 1.

Each module folder has two editions of its workbook:

- **WORKBOOK-local.md**: OpenChoreo v1.3.1 on a k3d cluster on your own machine. This is the main path for the course.
- **WORKBOOK-sandbox.md**: the WSO2 OpenChoreo Sandbox at demo.openchoreo.wso2.com (v1.2.2, one-hour sessions). Use it if you cannot run the cluster locally.

## Modules

| Module | Topic | Local install | Sandbox |
|---|---|---|---|
| Pre-work | Before Day 1: Install the tools and the k3d cluster; confirm the portal opens | [WORKBOOK-local.md](prework/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](prework/WORKBOOK-sandbox.md) |
| Lab 1 | M01 Foundations: Verify planes, deploy a service, trace Component to Deployment | [WORKBOOK-local.md](lab1/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](lab1/WORKBOOK-sandbox.md) |
| Lab 2 | M02 Control plane and identity: Run the device-flow demo, sign in with occ, grant a team access | [WORKBOOK-local.md](lab2-device-login/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](lab2-device-login/WORKBOOK-sandbox.md) |
| Lab 3 | M03 Governance and cells: Run a policy check, build a governed cell with a quota, compare declared and observed connections | [WORKBOOK-local.md](lab3-policy-check/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](lab3-policy-check/WORKBOOK-sandbox.md) |
| Lab 4 | M04 Using AI coding agents: Connect an agent to both MCP servers, install skills, read its calls in the audit log | [WORKBOOK-local.md](lab4-agents/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](lab4-agents/WORKBOOK-sandbox.md) |
| Lab 5 | M05 Platform APIs: Create a ComponentType variant, attach a Trait, watch a release | [WORKBOOK-local.md](lab5/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](lab5/WORKBOOK-sandbox.md) |
| Lab 6 | M06 Golden paths: Build from source, promote, run the traffic-control demo, diagnose with wirelogs and a shell | [WORKBOOK-local.md](lab6-traffic-control/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](lab6-traffic-control/WORKBOOK-sandbox.md) |
| Lab 7 | M07 Scaling: Observe, attach an alert rule, run the SRE agent, run the event demo | [WORKBOOK-local.md](lab7/WORKBOOK-local.md) | [WORKBOOK-sandbox.md](lab7/WORKBOOK-sandbox.md) |

## How to use the workbook

- Code blocks are commands to paste; GitHub shows a copy button on each. Lines starting with `#` are comments; the shell ignores them once the pre-work `setopt interactivecomments` line has run (macOS, zsh).
- Blocks are self-contained. A value such as a cell namespace is looked up in the block that needs it, so a block works in a fresh terminal.
- The lab code lives in `~/oc-201-labs`. Every `cd` uses that full path, so it works from any folder.
- No block asks you to paste YAML. Files come from the lab repository; changes are made with `kubectl patch`, `sed` or a lab script.
- Long commands are split with `\` at the end of a line. Paste the whole block.
- The only value you type yourself is your own secret: an OpenAI API key, if you use one in Lab 7.
- macOS blocks are the default. Where a step differs, blocks labeled **Linux** and **Windows** follow; paste only the ones for your machine. On Windows every block runs in the Ubuntu terminal on WSL 2, except the ones marked PowerShell. Untagged blocks are the same on every machine.
- **Verify** marks a command whose flags depend on your installed version. If it fails, run it with `--help`.
- Output is described, not reproduced. If what you see differs materially from the checkpoint, stop and ask.

## Cheat sheet

| Task | Command |
|---|---|
| Version / login | `occ version` · `occ login` |
| List | `occ namespace list` · `occ project list -n default` · `occ component list -n default` |
| Apply YAML | `occ apply -f file.yaml` |
| Scaffold | `occ component scaffold my-greeter -n default -p default --clustercomponenttype deployment/service` |
| Deploy / promote | `occ component deploy greeting-service -n default -p default --to staging` |
| Logs | `occ component logs greeter-service -n default -p default --env development --tail 50` |
| Shell in a component | `occ component exec greeting-service -n default -p default --env development` |
| Audit | `occ auditlogs --since 7d --result denied` |
| Cell namespace of a component | `kubectl get deployment -A -l openchoreo.dev/component=greeter-service` |
| MCP servers | `~/oc-201-labs/lab4-agents/scripts/register-claude-code-token.sh` · `claude mcp list` · `/mcp` |
| Skills | `npx skills add openchoreo/skills --skill openchoreo-developer` |
| Dry run | `kubectl apply --dry-run=server -f file.yaml` |
| Discover kinds | `kubectl api-resources \| grep -i openchoreo` |

### How the objects connect

| Object | Becomes |
|---|---|
| Component | → ComponentRelease (immutable) → ReleaseBinding → RenderedRelease → Deployment, Service, HTTPRoute |
| Project | → ProjectRelease → ProjectReleaseBinding → cell namespace, quota, policies |
| Alert rule | Notification channel in the environment → Trait on the component → ObservabilityAlertRule → incident (set per environment in the ReleaseBinding) → SRE agent report, or Claude Code through MCP |
| Gateway URL | `http://{env}-{namespace}.openchoreoapis.localhost:19080/{component}-{endpoint}/{path}` |
| MCP servers | `http://api.openchoreo.localhost:8080/mcp` · `http://observer.openchoreo.localhost:11080/mcp` |

### Sandbox differences

| Object | In the sandbox |
|---|---|
| Gateway | `http://$GWADDR` with `Host: {env}-{namespace}.demo.openchoreo.wso2.com`, path `/{component}-{endpoint}/{path}` |
| MCP servers | `https://api.demo.openchoreo.wso2.com/mcp` · `https://observer.demo.openchoreo.wso2.com/mcp` |
| Audit | Console, Audit Logs page (occ 1.2 has no `auditlogs`) |
| Call a workload | `curl -H "Host: $DEVHOST" http://$GWADDR/greeter-service-http/greeter/greet` |


Sources: OpenChoreo v1.3 documentation (openchoreo.dev), the OpenChoreo repository (release-v1.3) and CNCF project page, and The Platform Engineer's Handbook.
