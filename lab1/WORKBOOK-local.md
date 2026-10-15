# Lab 1: Verify the install, deploy and trace

*OC-201 workbook, local install edition. Using the sandbox instead? See [WORKBOOK-sandbox.md](WORKBOOK-sandbox.md).*

**Goal:** Confirm every plane is healthy, deploy a sample service, and follow one Component down to the Deployment, Service and HTTPRoute it produces.

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

Expect a `default` project, three environments (development, staging, production), a default pipeline, the component types service, web-application, scheduled-task and worker, and the build workflows.

## B. The portal

### 3. Open the portal and find the default project

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

Sign in with `admin@openchoreo.dev` / `Admin@123`. Open the catalog and find the default project. Namespaces, projects and components are shown as Domain, System and Component.

## C. Deploy a service

### 4. Apply the greeter-service sample

A Go service from a pre-built image, from the OpenChoreo repository, release-v1.3.

```bash
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.3/samples
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
URL=http://development-default.openchoreoapis.localhost:19080/greeter-service-http
curl $URL/greeter/greet
curl "$URL/greeter/greet?name=OpenChoreo"
```

The URL pattern is `http://{environment}-{namespace}.{gateway-host}:19080/{component}-{endpoint}/{path}`. The answers are `Hello, Stranger!` and `Hello, OpenChoreo!`.

## Checkpoint

- [ ] `kubectl get projects -n default` lists `default`
- [ ] The greeter answers through the gateway
- [ ] You can name the object that created the Deployment (the RenderedRelease from a ReleaseBinding)

## Troubleshooting

- 404 from curl: run `kubectl get httproute -A -l openchoreo.dev/component=greeter-service -o yaml | grep -A3 path:` and use that path.
- Connection refused: run `kubectl get pods -A | grep -i gateway` and `docker ps | grep 19080`.
- Nothing in `get components`: run the apply again and read the error.

---

Previous: [Pre-work](../prework/WORKBOOK-local.md) · [All modules](../WORKBOOK.md) · Next: [Lab 2](../lab2-device-login/WORKBOOK-local.md)
