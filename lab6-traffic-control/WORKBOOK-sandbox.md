# Lab 6: Build, promote and diagnose

*OC-201 workbook, WSO2 sandbox edition. Using the local install instead? See [WORKBOOK-local.md](WORKBOOK-local.md).*

**Goal:** Take a service from Git source to a running endpoint, promote it, run the traffic-control demo while the build works, then diagnose failures with wirelogs and a shell in the pod.

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

## A. Build and promote

### 1. Start the build-from-source sample

The greeting-service sample, a Go service built from Git source by the build workflow.

```bash
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.2/samples
kubectl apply -f $BASE/from-source/services/go-docker-greeter/greeting-service.yaml
kubectl get workflow -A --watch
```

Press Ctrl-C when the workflow shows `Succeeded`, after about two minutes. The Argo Workflows UI is not exposed in the sandbox; the build's run also shows on the component page in the console.

### 2. Call the built service

```bash
kubectl wait --for=condition=available deployment -A \
  -l openchoreo.dev/component=greeting-service --timeout=300s
GW_HOST=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.hostnames[0]}')
PATH_PREFIX=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.rules[0].matches[0].path.value}')
curl -H "Host: ${GW_HOST}" "http://${GWADDR}${PATH_PREFIX}/greeter/greet"
```

### 3. Scaffold your own and compare

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

```bash
mkdir -p ~/oc-201-labs/lab6 && cd ~/oc-201-labs/lab6
occ component scaffold my-greeter -n default -p default \
  --clustercomponenttype deployment/service \
  --clusterworkflow dockerfile-builder -o lab6-scaffold.yaml
cat lab6-scaffold.yaml
```

Compare it with the sample: `curl -fsSL https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.2/samples/from-source/services/go-docker-greeter/greeting-service.yaml`. Find the workflow reference and the Git settings.

### 4. Run the traffic-control demo

The script validates and runs a canary and a blue/green configuration. Guardrails reject TLS off, hosts outside `*.platform.local`, a canary percentage outside 1 to 99, and an active color other than blue or green.

```bash
cd ~/oc-201-labs/lab6-traffic-control
source ~/oc-201-labs/.venv/bin/activate
python3 run_demo.py
```

Now break one rule in a copy of the canary config and run that:

```bash
cd ~/oc-201-labs/lab6-traffic-control
sed 's/canary_percentage: 20/canary_percentage: 150/' configs/canary.yaml \
  > configs/canary-broken.yaml
python3 run_demo.py configs/canary-broken.yaml
```

### 5. Turn a config into a real route

The same guardrails gate a Gateway API HTTPRoute. Workloads are served by the data plane's Gateway, so the block uses that one. It generates the route, has the cluster validate it without creating it, then tries the broken config.

```bash
cd ~/oc-201-labs/lab6-traffic-control
source ~/oc-201-labs/.venv/bin/activate
sed 's/canary_percentage: 20/canary_percentage: 150/' configs/canary.yaml \
  > configs/canary-broken.yaml
kubectl get gateways -A
GW_NS=openchoreo-data-plane
GW_NAME=$(kubectl get gateways -n $GW_NS -o jsonpath='{.items[0].metadata.name}')
python3 to_httproute.py configs/canary.yaml --gateway $GW_NAME --gateway-namespace $GW_NS
python3 to_httproute.py configs/canary.yaml --gateway $GW_NAME --gateway-namespace $GW_NS \
  | kubectl apply --dry-run=server -f -
python3 to_httproute.py configs/canary-broken.yaml --gateway $GW_NAME
```

`kubectl get gateways -A` lists one Gateway per plane; the data plane's is the one in front of your components. The weights are 80 and 20. The backends do not exist, so the route is only dry-run. The broken config prints `CONFIG REJECTED` and no route.

### 6. Check the bindings

```bash
kubectl get releasebindings -n default | grep -E 'NAME|greeting-service'
GW_HOST=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.hostnames[0]}')
PATH_PREFIX=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.rules[0].matches[0].path.value}')
curl -H "Host: ${GW_HOST}" "http://${GWADDR}${PATH_PREFIX}/greeter/greet"
```

### 7. Promote to staging

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

```bash
occ component deploy greeting-service -n default -p default --to staging
kubectl get releasebindings -n default | grep -E 'NAME|greeting-service'
```

The default pipeline allows development to staging, then staging to production.

## B. Diagnose with wirelogs

### 8. Read a healthy request

Wirelogs are the flow records Cilium keeps for traffic between workloads, each with a source, a destination and a verdict: forwarded or dropped. The sandbox runs Cilium, so they are available. Make a request:

```bash
kubectl get pods -n kube-system -l k8s-app=cilium
GW_HOST=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.hostnames[0]}')
PATH_PREFIX=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.rules[0].matches[0].path.value}')
curl -i -H "Host: ${GW_HOST}" "http://${GWADDR}${PATH_PREFIX}/greeter/greet"
```

Find the request in the component's wirelogs in the console.

### 9. Cause three failures and compare them

| Failure | What To Expect In The Wirelogs |
|---|---|
| 1. The application answers with an error | A forwarded flow. The connection worked; the cause is in the application |
| 2. Nothing is running | No flow reaches the pod. The request stops earlier |
| 3. A pod outside the cell calls in | A dropped flow if the cell's policy blocks it. If it goes through, the policy is looser than you thought |

```bash
GW_HOST=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.hostnames[0]}')
PATH_PREFIX=$(kubectl get httproute -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].spec.rules[0].matches[0].path.value}')
NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].metadata.namespace}')
DEP=$(kubectl get deployment -n $NS -l openchoreo.dev/component=greeting-service \
  -o jsonpath='{.items[0].metadata.name}')

# 1. a path that does not exist: the app answers 404
curl -i -H "Host: ${GW_HOST}" "http://${GWADDR}${PATH_PREFIX}/greeter/does-not-exist"

# 2. nothing running: no endpoints behind the service
kubectl scale deployment $DEP -n $NS --replicas=0
sleep 10
curl -i -H "Host: ${GW_HOST}" "http://${GWADDR}${PATH_PREFIX}/greeter/greet"
kubectl get endpointslices -n $NS -l kubernetes.io/service-name=greeting-service
kubectl scale deployment $DEP -n $NS --replicas=1

# 3. from a pod outside the cell, by cluster address
PORT=$(kubectl get svc greeting-service -n $NS -o jsonpath='{.spec.ports[0].port}')
kubectl delete pod curl-test -n default --ignore-not-found
kubectl run curl-test -n default --restart=Never --image=curlimages/curl -- \
  curl -sS -m 5 http://greeting-service.$NS.svc.cluster.local:$PORT/greeter/greet
sleep 20
kubectl logs curl-test -n default
kubectl delete pod curl-test -n default
```

Case 3 is refused by the ingress policy OpenChoreo puts on every component, as in Lab 3. A dropped flow points at a network policy. A forwarded flow with a failing response points at the application. The platform may scale the Deployment back up by itself after case 2; that is the reconciler restoring the declared state.

## C. Diagnose with the web shell

### 10. Open a shell in the running component

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

When the request reached the pod and the pod still fails, look inside it. The portal can open the same shell.

```bash
occ component exec greeting-service -n default -p default --env development
# you are now in a shell inside the pod. Type exit to leave
```

### 11. Check three things

The same checks as single commands, without an interactive shell:

```bash
oc_exec() { occ component exec greeting-service -n default -p default \
  --env development -- "$@"; }
# 1. which process runs, and which port it listens on
oc_exec ps
oc_exec netstat -tln
# 2. the environment variables the platform injected
oc_exec env
# 3. whether the pod resolves cluster names
oc_exec nslookup kubernetes.default.svc.cluster.local
# if netstat is missing, read the socket tables. The port is hex in column 2
oc_exec cat /proc/net/tcp /proc/net/tcp6
```

The greeter listens on `:::9090`, an IPv6 socket, so in the socket tables it appears in `tcp6`, where port 9090 shows as `2382`. A pod listening on a different port than the endpoint declares is a common cause. Compare the port with `kubectl get workload -n default -o yaml | grep -A4 endpoints`. Exec is authorized like any other action; if it is denied, see Lab 2.

## Checkpoint

- [ ] The workflow run finishes and the deployment becomes available
- [ ] The endpoint answers through the gateway
- [ ] A ReleaseBinding exists for staging
- [ ] You can tell the three failure cases apart (in the wirelogs with Cilium, or from the commands without it)
- [ ] You have listed the process and listening port from inside the pod

## Troubleshooting

- Build never finishes: run `kubectl get pods -A | grep -i workflow`; the workflow plane must be installed.
- Image pull errors: run `kubectl describe pod -n $(kubectl get deployment -A -l openchoreo.dev/component=greeting-service -o jsonpath='{.items[0].metadata.namespace}')` and read the Events.
- `ModuleNotFoundError: yaml`: run `source ~/oc-201-labs/.venv/bin/activate`.
- `occ component deploy` asks for flags: run `occ component deploy --help`.
- Exec denied: the role bound to your sign-in does not allow it. See Lab 2.
- `configs/canary-broken.yaml` not found: run the `sed` line that creates it, in step 4 or 5.
- Route dry-run rejected: check `GW_NS=openchoreo-data-plane`; the control plane's Gateway does not serve components.
- `/proc/net/tcp` shows no listener on 9090: the greeter listens on IPv6; read `/proc/net/tcp6`, port `2382`.
- No workflow listed: run `kubectl get ns | grep workflow` and `kubectl get workflow -A`.

---

Previous: [Lab 5](../lab5/WORKBOOK-sandbox.md) · [All modules](../WORKBOOK.md) · Next: [Lab 7](../lab7/WORKBOOK-sandbox.md)
