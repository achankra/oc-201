# Pre-work: Install and verify

*OC-201 workbook, local install edition. Using the sandbox instead? See [WORKBOOK-sandbox.md](WORKBOOK-sandbox.md).*

**Goal:** A running local OpenChoreo v1.3.1 cluster, the occ CLI, a signed-in portal, and the lab code on your machine. Every tool is installed in the steps below.

| Tool | Minimum | Check |
|---|---|---|
| Docker | v26+, 8 GB RAM and 4 CPUs for the VM | `docker info` |
| k3d | v5.8+ | `k3d version` |
| kubectl | v1.34+ | `kubectl version --client` |
| Helm | v3.12+ | `helm version` |
| occ | v1.3.1 | `occ version` |
| Git | any recent version | `git --version` |
| Python | 3.9+ | `python3 --version` |
| OPA | any recent version, for Lab 3 | `opa version` |
| Node.js | 18+, for Lab 4 | `node --version` |

### 1. Install the tools

macOS is the default. Linux and Windows blocks follow where a step differs; paste only the blocks for your machine. On Windows, the labs run inside Ubuntu on WSL 2. On a Mac (zsh), first let pasted blocks contain `#` comment lines; without this, zsh tries to run them. bash on Linux and WSL needs nothing.

**macOS**

```bash
echo 'setopt interactivecomments' >> ~/.zshrc && source ~/.zshrc
```

```bash
# 1. Homebrew, only if brew --version fails
/bin/bash -c "$(curl -fsSL \
  https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# run the commands the installer prints under Next steps, then open a new terminal
```

```bash
# 2. The tools
brew install git colima docker k3d kubectl helm python opa node
```

**Linux**

```bash
# Ubuntu or Debian. 1. Docker Engine, then log out and in once so docker runs without sudo
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

```bash
# 2. The tools
sudo apt-get update
sudo apt-get install -y git curl ca-certificates lsof python3 python3-venv python3-pip
# kubectl. On ARM, replace amd64 with arm64 on the next line
KV=$(curl -L -s https://dl.k8s.io/release/stable.txt)
curl -LO "https://dl.k8s.io/release/$KV/bin/linux/amd64/kubectl"
sudo install -m 0755 kubectl /usr/local/bin/kubectl && rm kubectl
# k3d and Helm
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
# OPA
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static
chmod +x opa && sudo mv opa /usr/local/bin/
# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows, in PowerShell as Administrator**

```powershell
# 1. PowerShell as Administrator: install WSL 2 with Ubuntu, then restart Windows
wsl --install -d Ubuntu
```

**Windows, in the WSL 2 Ubuntu terminal**

```bash
# 2. In the Ubuntu terminal. Docker comes from Docker Desktop, see Start Docker
sudo apt-get update
sudo apt-get install -y git curl ca-certificates lsof python3 python3-venv python3-pip
# kubectl. On ARM, replace amd64 with arm64 on the next line
KV=$(curl -L -s https://dl.k8s.io/release/stable.txt)
curl -LO "https://dl.k8s.io/release/$KV/bin/linux/amd64/kubectl"
sudo install -m 0755 kubectl /usr/local/bin/kubectl && rm kubectl
# k3d and Helm
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
# OPA
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static
chmod +x opa && sudo mv opa /usr/local/bin/
# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Every machine**

```bash
# 3. Check
docker --version
k3d version
kubectl version --client
helm version --short
git --version
python3 --version
opa version
node --version
```

The last block is the same on every machine. **Windows:** install Docker Desktop from docker.com, then under Settings, Resources, WSL integration, turn on Ubuntu. Run every later block in the Ubuntu terminal, not PowerShell.

### 2. Start Docker

The cluster needs 8 GB of memory and 4 CPUs for Docker. On a Mac, Colima provides the Docker engine. Paste the block for your machine, then the check.

**macOS**

```bash
# Apple silicon
colima start --vm-type=vz --vz-rosetta --cpu 4 --memory 8
# the DNS fix Colima needs before the cluster is created
export K3D_FIX_DNS=0
```

```bash
# Intel Mac
colima start --cpu 4 --memory 8
export K3D_FIX_DNS=0
```

**Linux**

```bash
sudo systemctl enable --now docker
```

**Windows, in the WSL 2 Ubuntu terminal**

```bash
# Start Docker Desktop from the Start menu first. WSL 2 must allow it 8 GB of memory
docker context use default
```

**Every machine**

```bash
# every machine: check
docker info > /dev/null && echo "Docker is running"
```

On a Mac, run the install step in the same terminal as the `export` line. Linux and Windows do not need it. On Windows, WSL 2 takes half the machine's memory by default, so a 16 GB machine gives Docker the 8 GB it needs. If `docker info` says permission denied on Linux, log out and in once after the `usermod` line.

### 3. Install occ

occ is the OpenChoreo CLI. It does not need the cluster to install. Paste the block for your machine; sudo asks for your password.

**macOS**

```bash
# Apple silicon
BASE=https://github.com/openchoreo/openchoreo/releases/download/v1.3.1
curl -L $BASE/occ_v1.3.1_darwin_arm64.tar.gz | tar -xz && sudo mv occ /usr/local/bin/
occ version
```

```bash
# Intel Mac
BASE=https://github.com/openchoreo/openchoreo/releases/download/v1.3.1
curl -L $BASE/occ_v1.3.1_darwin_amd64.tar.gz | tar -xz && sudo mv occ /usr/local/bin/
occ version
```

**Linux**

```bash
# x64. On ARM, replace amd64 with arm64
BASE=https://github.com/openchoreo/openchoreo/releases/download/v1.3.1
curl -L $BASE/occ_v1.3.1_linux_amd64.tar.gz | tar -xz && sudo mv occ /usr/local/bin/
occ version
```

**Windows, in the WSL 2 Ubuntu terminal**

```bash
BASE=https://github.com/openchoreo/openchoreo/releases/download/v1.3.1
curl -L $BASE/occ_v1.3.1_linux_amd64.tar.gz | tar -xz && sudo mv occ /usr/local/bin/
occ version
```

`occ version` prints the CLI version; the server line shows `<not connected>` until Lab 2 points occ at the cluster.

### 4. Run the preflight checks

Each check catches a failure that otherwise shows up several minutes into the install.

```bash
# 1. Docker answers, with the memory and CPUs the cluster needs
docker info --format 'memory={{.MemTotal}} bytes, cpus={{.NCPU}}'
# 2. No cluster named openchoreo left from an earlier try
k3d cluster list
# 3. No container publishes the ports the cluster needs
docker ps --format "table {{.Names}}\t{{.Ports}}"
# 4. No program on your machine listens on those ports
for p in 8080 8443 19080 19443 30443 10081 10082 11080 11081 11082 11085; do
  lsof -nP -iTCP:$p -sTCP:LISTEN > /dev/null && echo "port $p is in use"
done
# 5. Mac with Colima only: prints K3D_FIX_DNS=0
echo "K3D_FIX_DNS=$K3D_FIX_DNS"
# 6. The download hosts answer
curl -sI https://raw.githubusercontent.com | head -1
curl -sI https://ghcr.io | head -1
```

1: memory close to 8 GB (about 8 billion bytes) and cpus 4 or more. 2: if `openchoreo` is listed, run `k3d cluster delete openchoreo`. 3 and 4: no line should say `is in use`; stop the container with `docker stop` or quit the program, then check again. 6: each prints an HTTP status line.

### 5. Create the cluster and install OpenChoreo

One command creates a k3d cluster named `openchoreo` and installs the control, data, workflow and observability planes at v1.3.1. Allow several minutes on a first run. Run it in the terminal where you ran the `export` line.

```bash
URL=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.3/install/k3d
curl -fsSL $URL/k3d-install.sh | bash -s -- \
  --version v1.3.1 --with-build --with-observability
```

### 6. Check the cluster

```bash
k3d cluster list
kubectl config current-context
kubectl get nodes
kubectl wait -n openchoreo-control-plane --for=condition=available \
  --timeout=300s deployment --all
kubectl get pods -A | grep -v -E 'Running|Completed'
curl -sI http://openchoreo.localhost:8080 | head -1
occ version
```

The context is `k3d-openchoreo` and the node is Ready. The `grep` line prints only the header; any other line is a pod that is not ready yet, so wait and run it again.

### 7. Open the portal

**macOS**

```bash
open http://openchoreo.localhost:8080
```

**Linux**

```bash
xdg-open http://openchoreo.localhost:8080
```

**Windows, in the WSL 2 Ubuntu terminal**

```bash
explorer.exe http://openchoreo.localhost:8080
```

Sign in with `admin@openchoreo.dev` and password `Admin@123`. Workloads are served on host port 19080 (HTTP) and 19443 (HTTPS).

### 8. Get the lab code

Clone the lab repository into your home folder and create a Python environment with its one dependency.

```bash
git clone https://github.com/achankra/oc-201.git ~/oc-201-labs
cd ~/oc-201-labs
python3 -m venv .venv
source ~/oc-201-labs/.venv/bin/activate
pip install pyyaml
python3 -c "import yaml; print('pyyaml ok')"
```

In each new terminal, run `source ~/oc-201-labs/.venv/bin/activate` before the Python programs. If you already have the repository somewhere else, link it instead of cloning, so every path in the labs works: `ln -s "/path/to/oc-201-labs" ~/oc-201-labs`.

### 9. Install an AI coding agent

Lab 4 connects an AI coding agent to OpenChoreo, and Lab 7 uses the same agent to investigate an incident. The workbook uses Claude Code. Install one agent: paste only the line under its name.

```bash
# Claude Code. On Linux and WSL, put sudo in front of npm
npm install -g @anthropic-ai/claude-code
# Codex CLI
npm install -g @openai/codex
# Gemini CLI
npm install -g @google/gemini-cli
# OpenCode CLI
npm install -g opencode-ai
```

Each tool signs you in the first time it runs. Cursor and VS Code are apps from cursor.com and code.visualstudio.com. The built-in SRE agent in Lab 7 needs an OpenAI API key (platform.openai.com/api-keys, billed to your account); without one, Claude Code does the analysis. Labs 4 and 7 each also have a path with no agent and no key.

## Checkpoint

- [ ] `docker info` works and the preflight checks came back clean
- [ ] `kubectl get nodes` shows the node Ready; pods are Running or Completed
- [ ] The portal loads and you can sign in with admin@openchoreo.dev / Admin@123
- [ ] `occ version` prints a 1.3.1 CLI version
- [ ] `ls ~/oc-201-labs` lists the lab folders and the pyyaml check prints `pyyaml ok`
- [ ] Your AI coding agent starts and signs in

## Troubleshooting

- `command not found: occ`: run `ls -l /usr/local/bin/occ`; if it is missing, repeat Install occ.
- `k3d cluster list` is empty: the install did not finish. On a Mac with Colima, run `export K3D_FIX_DNS=0`; then run the install block again. If it stops with an error, read its last lines; usually Docker memory or no network.
- `The connection to the server 127.0.0.1 was refused`: the cluster stopped. Start Docker again (Mac: the `colima start` line; Linux: `sudo systemctl start docker`; Windows: open Docker Desktop), then `k3d cluster start openchoreo`, then `kubectl get nodes`.
- `Cannot connect to the Docker daemon`: run Start Docker again.
- Pods stuck Pending or restarting: raise Docker memory to at least 8 GB and restart Colima or Docker Desktop. On Linux, check free memory with `free -g`.
- `*.openchoreo.localhost` does not resolve: run `echo '127.0.0.1 openchoreo.localhost api.openchoreo.localhost thunder.openchoreo.localhost observer.openchoreo.localhost' | sudo tee -a /etc/hosts`.
- `externally-managed-environment` from pip: run `source ~/oc-201-labs/.venv/bin/activate` first.
- Windows: `docker: command not found` in Ubuntu: turn on WSL integration for Ubuntu in Docker Desktop, then open a new Ubuntu terminal.
- Linux: `permission denied` on the Docker socket: log out and in once after `sudo usermod -aG docker $USER`.
- Linux and WSL: `EACCES` from `npm install -g`: run it with `sudo`.
- `Bind for 0.0.0.0:8080 failed: port is already allocated`: find the owner with `docker ps` and `lsof -nP -iTCP:8080 -sTCP:LISTEN`, stop it, then run the install again.

---

[All modules](../WORKBOOK.md) · Next: [Lab 1](../lab1/WORKBOOK-local.md)
