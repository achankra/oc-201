# Lab 1: Verify the install, deploy and trace

*OC-201 workbook, WSO2 sandbox edition. Using the local install instead? See [WORKBOOK-local.md](WORKBOOK-local.md).*

**Goal:** Confirm every plane is healthy, deploy a sample service, and follow one Component down to the Deployment, Service and HTTPRoute it produces.

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

## A. Verify the platform

### 1. List what the platform defines

```bash
kubectl get namespaces
kubectl api-resources | grep -i openchoreo
```

The second command lists every OpenChoreo resource kind in your version.

### 2. See the defaults the installer created

```bash
kubectl get projects,environments,deploymentpipelines -n default
kubectl get clustercomponenttypes
kubectl get clusterworkflows
```

Expect the `default` project plus `gcp-microservice-demo`, a demo application the sandbox ships, three environments, a default pipeline, the component types service, web-application, scheduled-task and worker, and the build workflows (dockerfile-builder and three buildpack builders).

## B. The portal

### 3. Open the portal and find the default project

In your browser, open https://console.demo.openchoreo.wso2.com.

Sign in with `admin@openchoreo.dev` / `Admin@123`. Open the catalog and find the default project. Namespaces, projects and components are shown as Domain, System and Component.

## C. Deploy a service

### 4. Apply the greeter-service sample

A Go service from a pre-built image, from the OpenChoreo repository, release-v1.2.

```bash
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.2/samples
kubectl apply -f $BASE/from-image/go-greeter-service/greeter-service.yaml
kubectl wait --for=condition=Ready component/greeter-service -n default --timeout=180s
```

### 5. Watch it become ready

```bash
kubectl get components,workloads -n default
kubectl get releasebindings -n default
```

## D. Trace the chain

### 6. Follow Component to ComponentRelease to ReleaseBinding

```bash
kubectl get component greeter-service -n default
kubectl get componentreleases -n default
kubectl get releasebinding greeter-service-development -n default
kubectl get renderedreleases -A
```

The ReleaseBinding is named after the component and environment: `greeter-service-development`.

### 7. Find what landed on the data plane

```bash
kubectl get deployment,svc,httproute -A -l openchoreo.dev/component=greeter-service
kubectl get deployment -A -l openchoreo.dev/component=greeter-service \
  -o jsonpath='{.items[0].metadata.namespace}{"\n"}'
```

The last command prints the namespace the objects live in. In Lab 3 you will see it belongs to a cell.

## E. Call it

### 8. Call the service through the gateway

```bash
URL=http://$GWADDR/greeter-service-http
curl -H "Host: $DEVHOST" $URL/greeter/greet
curl -H "Host: $DEVHOST" "$URL/greeter/greet?name=OpenChoreo"
```

The sandbox publishes `development-default.demo.openchoreo.wso2.com`, but its public URL sits behind a browser check, so the terminal calls the gateway inside the cluster and names the host in a `Host` header. The path follows `/{component}-{endpoint}/{path}`. The answers are `Hello, Stranger!` and `Hello, OpenChoreo!`.

## Checkpoint

- [ ] `kubectl get projects -n default` lists `default`
- [ ] The greeter answers through the gateway
- [ ] You can name the object that created the Deployment (the RenderedRelease from a ReleaseBinding)

## Troubleshooting

- 404 from curl: run `kubectl get httproute -A -l openchoreo.dev/component=greeter-service -o yaml | grep -A3 path:` and use that path.
- No answer: run `echo $GWADDR`. If it is empty, run the setup block again.
- Nothing in `get components`: run the apply again and read the error.

---

Previous: [Pre-work](../prework/WORKBOOK-sandbox.md) · [All modules](../WORKBOOK.md) · Next: [Lab 2](../lab2-device-login/WORKBOOK-sandbox.md)
