# Pre-work: Start a sandbox session

*OC-201 workbook, WSO2 sandbox edition. Using the local install instead? See [WORKBOOK-local.md](WORKBOOK-local.md).*

**Goal:** A fresh OpenChoreo cluster in the WSO2 sandbox, the lab code, Python, OPA and the gateway address ready in its terminal, and the console open in your browser. A session lasts one hour and nothing is kept.

| What | Value |
|---|---|
| Sandbox | https://demo.openchoreo.wso2.com, sign in with GitHub |
| Console | https://console.demo.openchoreo.wso2.com, `admin@openchoreo.dev` / `Admin@123` |
| OpenChoreo | v1.2.2 server, occ 1.2.0. The labs use the release-v1.2 samples |
| Shell | zsh, with kubectl, occ, helm, git, node, npx, jq and claude installed; occ already signed in |
| Workloads | Reached at the data plane gateway inside the cluster (`$GWADDR`) with the host name `development-default.demo.openchoreo.wso2.com`. The public URL is behind a browser check that blocks curl |
| MCP servers | Already registered in claude, opencode and codex |

### 1. Open the sandbox

In your browser, open https://demo.openchoreo.wso2.com and sign in with GitHub. A terminal opens with a fresh cluster. The timer in the top bar shows the time left. Run every block in that terminal.

### 2. Set up the session

Paste this into the sandbox terminal in your browser, once per session. **Never paste it into a terminal on your own machine:** it changes `~/.zshrc` and downloads a Linux `opa` into `~/bin`. Each lab repeats it at the top, so a lab can start in a new session.

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

The last lines print the gateway address and the OPA version. Opening a new tab in the same session needs nothing more: the settings are in `~/.zshrc`.

### 3. Check the session

```bash
occ namespace list
occ component list -n default
python3 -c "import yaml; print('pyyaml ok')"
curl -s -o /dev/null -w "%{http_code}\n" -H "Host: $DEVHOST" http://$GWADDR/
claude mcp list | grep openchoreo
```

`default` is listed; the components of the `gcp-microservice-demo` project are already deployed; `pyyaml ok`; the gateway answers with a status code such as 404; both MCP servers show `Connected`.

### 4. Open the console

In your browser, open https://console.demo.openchoreo.wso2.com and sign in with `admin@openchoreo.dev` / `Admin@123`. The developer and platform engineer accounts on the sandbox's start page work too.

### 5. Set your AI key (Labs 4 and 7)

Claude Code in the sandbox needs your own key. Type it in the terminal; it lasts for the session only. With an OpenAI key, use `codex` instead and set `OPENAI_API_KEY`.

```bash
# replace sk-ant-your-key with your own key
export ANTHROPIC_API_KEY=sk-ant-your-key
```

## Checkpoint

- [ ] The setup block printed the gateway address and an OPA version
- [ ] `occ namespace list` returns `default`
- [ ] Both MCP servers show `Connected`
- [ ] The console opens and you can sign in

## Troubleshooting

- `no matches found` from zsh: a pasted line has an unquoted `[` or `*`. Every block in this workbook is quoted; check the paste.
- `gateway , host`: the setup block did not finish. Run it again.
- `Failed to connect to 10.43...` and the prompt shows your own computer's name: you are in a terminal on your machine, not the sandbox. Use the sandbox terminal. If the setup block ran on your machine, remove the `GWADDR`, `DEVHOST` and `$HOME/bin` lines from `~/.zshrc` and delete `~/bin/opa`.
- The session ended mid-lab: start a new one, run the setup block, then the lab's own start-of-session block, then continue from the step you were on.
- A curl to the public URL returns `Just a moment...`: that is the browser check in front of the sandbox. Use `$GWADDR` with the `Host` header, as every block here does.

---

[All modules](../WORKBOOK.md) · Next: [Lab 1](../lab1/WORKBOOK-sandbox.md)
