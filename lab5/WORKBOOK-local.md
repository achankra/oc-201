# Lab 5: A ComponentType and a Trait

*OC-201 workbook, local install edition. Using the sandbox instead? See [WORKBOOK-sandbox.md](WORKBOOK-sandbox.md).*

**Goal:** Read the built-in service type, create a governed variant of it, attach a Trait, and watch a platform change become a new release.

## A. Read the built-ins

### 1. Print the service type and the alert-rule trait

```bash
kubectl get clustercomponenttype service -o yaml
kubectl get clustertrait observability-alert-rule -o yaml
```

Find the workload type, the validation that requires at least one endpoint, `allowedWorkflows` and `allowedTraits`, and which resources are templated with `${...}` expressions.

## B. Clone and tighten

### 2. Export a copy

```bash
mkdir -p ~/oc-201-labs/lab5 && cd ~/oc-201-labs/lab5
kubectl get clustercomponenttype service -o yaml > service-governed.yaml
```

### 3. Edit it

One Python command makes the four edits: rename to `service-governed`, drop the server-added fields, keep only the `openchoreo.dev/` annotations, and reduce `allowedTraits` to `health-probes` and `observability-alert-rule`.

```bash
cd ~/oc-201-labs/lab5
source ~/oc-201-labs/.venv/bin/activate
python3 -c "
import yaml
d = yaml.safe_load(open('service-governed.yaml'))
m = d['metadata']
drop = ('uid', 'resourceVersion', 'creationTimestamp', 'generation',
'managedFields', 'labels', 'ownerReferences')
for k in drop: m.pop(k, None)
ann = m.get('annotations', {})
m['annotations'] = {k: v for k, v in ann.items() if k.startswith('openchoreo.dev/')}
d.pop('status', None)
m['name'] = 'service-governed'
keep = ('health-probes', 'observability-alert-rule')
traits = d['spec']['allowedTraits']
d['spec']['allowedTraits'] = [t for t in traits if t['name'] in keep]
yaml.safe_dump(d, open('service-governed.yaml', 'w'), sort_keys=False)
"
head -12 service-governed.yaml
grep -n -A5 "allowedTraits" service-governed.yaml
```

### 4. Apply

> **Dry run first:** the block checks with a server-side dry run before it changes anything.

```bash
cd ~/oc-201-labs/lab5
kubectl apply --dry-run=server -f service-governed.yaml
kubectl apply -f service-governed.yaml
occ clustercomponenttype list
```

## C. Scaffold a component and attach a Trait

### 5. Scaffold

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

See what the platform asks for when a developer uses your type:

```bash
cd ~/oc-201-labs/lab5
occ component scaffold lab5-greeter -n default -p default \
  --clustercomponenttype deployment/service-governed \
  --clustertraits observability-alert-rule -o lab5-scaffold.yaml
cat lab5-scaffold.yaml
```

Required fields are placeholders; optional fields are commented examples. For the deploy, the next step builds a complete file from the greeter sample instead.

### 6. Write the component and apply it

> **Dry run first:** the block checks with a server-side dry run before it changes anything.

The greeter sample, renamed `lab5-greeter` and pointed at `deployment/service-governed`:

```bash
cd ~/oc-201-labs/lab5
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.3/samples
curl -fsSL $BASE/from-image/go-greeter-service/greeter-service.yaml \
  | sed -e 's/ame: greeter-service/ame: lab5-greeter/' \
        -e 's#name: deployment/service$#name: deployment/service-governed#' \
  > lab5-component.yaml
grep -n -E "name:|projectName" lab5-component.yaml
kubectl apply --dry-run=server -f lab5-component.yaml
kubectl apply -f lab5-component.yaml
kubectl wait --for=condition=Ready component/lab5-greeter -n default --timeout=180s
```

### 7. Attach the alert-rule Trait

> **Dry run first:** the block checks with a server-side dry run before it changes anything.

The trait refuses to render unless the environment has a notification channel, so create the default channel for `development` first. Then attach the trait. `instanceName` must be unique within the component.

```bash
# the alert-rule trait requires a notification channel in the environment
CH=~/oc-201-labs/lab7-sre-agent/manifests/notification-channel-webhook.yaml
kubectl apply --dry-run=server -f $CH
kubectl apply -f $CH
kubectl get observabilityalertsnotificationchannels -n default
```

```bash
P='{"spec":{"traits":[{"kind":"ClusterTrait","name":"observability-alert-rule",
"instanceName":"high-error-rate","parameters":{"description":"Lab 5 error lines",
"severity":"warning","source":{"type":"log","query":"lab5-error"},
"condition":{"window":"5m","interval":"1m","operator":"gt","threshold":100}}}]}}'
kubectl patch component lab5-greeter -n default --type=merge -p "$P" --dry-run=server
kubectl patch component lab5-greeter -n default --type=merge -p "$P"
kubectl get component lab5-greeter -n default -o jsonpath='{.spec.traits}{"\n"}'
sleep 20
kubectl get releasebinding lab5-greeter-development -n default \
  -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}{"\n"}'
```

The last line should say the binding is ready. `A notification channel is mandatory` means the channel is missing: run the first block again.

## D. Deploy

### 8. Trace it and call it

```bash
kubectl get components,componentreleases,releasebindings -n default | grep -E 'NAME|lab5'
kubectl wait --for=condition=available deployment -A \
  -l openchoreo.dev/component=lab5-greeter --timeout=180s
URL=http://development-default.openchoreoapis.localhost:19080/lab5-greeter-http
curl $URL/greeter/greet
```

The greeter answers `Hello, Stranger!` through your governed type.

## E. See a platform change become a release

### 9. Change the type and look again

Change the type's default replica count from 1 to 2, then compare the releases and the binding before and after.

```bash
kubectl get componentreleases -n default | grep -E 'NAME|lab5'
kubectl get releasebinding lab5-greeter-development -n default \
  -o jsonpath='{.spec.releaseName}{"\n"}'

kubectl patch clustercomponenttype service-governed --type=json -p '[{"op":"replace",
"path":"/spec/environmentConfigs/openAPIV3Schema/properties/replicas/default","value":2}]'
sleep 20

kubectl get componentreleases -n default | grep -E 'NAME|lab5'
kubectl get releasebinding lab5-greeter-development -n default \
  -o jsonpath='{.spec.releaseName}{"\n"}'
kubectl get deployment -A -l openchoreo.dev/component=lab5-greeter
```

A new ComponentRelease appears, because a release snapshots the type. The binding shows which release development runs; with `autoDeploy: true` it moves to the new one and the Deployment goes to 2 replicas.

## Checkpoint

- [ ] `occ clustercomponenttype list` shows `service-governed`
- [ ] `lab5-greeter` deploys and answers through the gateway
- [ ] A new ComponentRelease appears after the type change

## Troubleshooting

- `A notification channel is mandatory for alert rules`: apply `~/oc-201-labs/lab7-sre-agent/manifests/notification-channel-webhook.yaml`, as in step 7.
- Trait rejected: its name must be in the type's `allowedTraits`; run `grep -A5 allowedTraits ~/oc-201-labs/lab5/service-governed.yaml`.
- Component rejected: the type requires at least one endpoint; run `grep -A4 endpoints ~/oc-201-labs/lab5/lab5-component.yaml`.
- `ModuleNotFoundError: yaml`: run `source ~/oc-201-labs/.venv/bin/activate` and repeat the edit.
- No new release: run `kubectl get component lab5-greeter -n default -o jsonpath='{.spec.componentType}'`; it must name `deployment/service-governed` with kind ClusterComponentType.

---

Previous: [Lab 4](../lab4-agents/WORKBOOK-local.md) · [All modules](../WORKBOOK.md) · Next: [Lab 6](../lab6-traffic-control/WORKBOOK-local.md)
