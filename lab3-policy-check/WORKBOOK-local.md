# Lab 3: Policy check, governed cell, runtime view

*OC-201 workbook, local install edition. Using the sandbox instead? See [WORKBOOK-sandbox.md](WORKBOOK-sandbox.md).*

**Goal:** Run a policy-as-code check, build your own cell template with a quota and a default-deny policy, prove the boundary exists, and compare what the application declares with what it does.

## A. Policy at the point of change

### 1. Run the check on a bad and a good deployment

```bash
cd ~/oc-201-labs/lab3-policy-check
chmod +x scripts/*.sh scripts/*.py
./scripts/check.sh inputs/bad-deploy.json
./scripts/check.sh inputs/good-deploy.json
```

The bad input prints `allow: false` and a list of violations; the good one prints `PASS: compliant`. Pick one violation and find its rule:

```bash
cd ~/oc-201-labs/lab3-policy-check
grep -n "latest" policies/deployment.rego
```

## B. Look at a cell

### 2. Find the cell namespaces for the default project

A project gets one cell namespace per environment. Their names are generated, so look them up by label.

```bash
kubectl get projectreleasebindings -A
kubectl get namespaces -l openchoreo.dev/project=default -L openchoreo.dev/environment
```

One ProjectReleaseBinding each for development, staging and production; the second command shows the namespace each one created and its environment. The name is not `default-development`.

### 3. See what the cell contains

```bash
for ns in $(kubectl get namespaces -l openchoreo.dev/project=default -o name \
    | cut -d/ -f2); do
  echo "== $ns"
  kubectl get resourcequota,networkpolicy -n $ns
done
```

`No resources found` is a valid result: the default project type provisions only the namespace. You add the quota and policy in part C.

## C. Author a governed project type

### 4. Look at the default type

```bash
cd ~/oc-201-labs/lab3-policy-check
kubectl get clusterprojecttypes
kubectl get clusterprojecttype default -o yaml > default-project-type.yaml
grep -n -A12 "resources:" default-project-type.yaml
```

`spec.resources` has one entry, `id: cell-namespace`, which creates the namespace. Every project type keeps it. `uid`, `resourceVersion`, `creationTimestamp`, `generation` and the `last-applied-configuration` annotation are added by the server; they are not copied into a new type.

### 5. Read the governed type

`governed-project-type.yaml` keeps the namespace entry and adds two resources, both `targetPlane: dataplane` in `${metadata.namespace}`:

- `cell-quota`: a ResourceQuota capping requests at 2 CPU and 4Gi, limits at 4 CPU and 8Gi
- `cell-default-deny-egress`: a NetworkPolicy that blocks all outbound traffic except DNS to kube-system

```bash
cd ~/oc-201-labs/lab3-policy-check
cat governed-project-type.yaml
diff default-project-type.yaml governed-project-type.yaml
```

### 6. Grant the agent access, check, then apply

The data plane agent creates everything a project type renders, and out of the box it may not manage ResourceQuotas. Without this grant the cell apply fails with `resourcequotas ... is forbidden` and none of the type's resources land. A project type can only stamp out what the agent is allowed to manage. If `create` says `AlreadyExists`, the grant is already there.

```bash
# once per cluster: let the data plane agent manage quotas
kubectl create clusterrole lab-cluster-agent-quotas \
  --verb=get,list,watch,create,update,patch,delete --resource=resourcequotas,limitranges
kubectl create clusterrolebinding lab-cluster-agent-quotas \
  --clusterrole=lab-cluster-agent-quotas \
  --serviceaccount=openchoreo-data-plane:cluster-agent-dataplane
```

```bash
cd ~/oc-201-labs/lab3-policy-check
kubectl apply --dry-run=server -f governed-project-type.yaml
kubectl apply -f governed-project-type.yaml
kubectl get clusterprojecttypes
```

The list shows `default` and `governed`. If the dry run returns an error, it names the field the API rejected.

## D. Use it and check it

### 7. Create a project that uses the type

The script reads the deployment pipeline name from the `default` project, writes `lab3-project.yaml`, dry-runs it and applies it. It then creates a ProjectReleaseBinding for each pipeline environment, because a project gets its cell namespaces only through these bindings, and waits for the cells. It overwrites any earlier `lab3-project.yaml`.

```bash
cd ~/oc-201-labs/lab3-policy-check
./scripts/create-governed-project.sh
cat lab3-project.yaml
kubectl get projectreleasebindings -A | grep governed-demo
```

Check what the cells contain:

```bash
for ns in $(kubectl get namespaces -l openchoreo.dev/project=governed-demo -o name \
    | cut -d/ -f2); do
  echo "== $ns"
  kubectl get resourcequota,networkpolicy -n $ns
done
```

### 8. Confirm the boundary

```bash
kubectl get resourcequota -A | grep -E 'NAMESPACE|cell-quota'
kubectl get networkpolicy -A | grep -E 'NAMESPACE|default-deny-egress'
```

Each governed cell has a `cell-quota` and a `default-deny-egress`. The REQUEST and LIMIT columns show used against the cap.

### 9. Deploy into the governed project and check it

Deploy the greeter again, renamed `greeter-governed` and owned by `governed-demo`. Then find its cell namespace and run the step 1 policy against the live Deployment.

```bash
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.3/samples
curl -fsSL $BASE/from-image/go-greeter-service/greeter-service.yaml \
  | sed -e 's/ame: greeter-service/ame: greeter-governed/' \
        -e 's/projectName: default/projectName: governed-demo/' \
  | kubectl apply -f -
# wait until the Deployment exists in the cell, then until it is available
for i in $(seq 1 36); do
  kubectl get deployment -A -l openchoreo.dev/component=greeter-governed -o name \
    | grep -q . && break
  sleep 5
done
kubectl wait --for=condition=available deployment -A \
  -l openchoreo.dev/component=greeter-governed --timeout=180s

NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-governed \
  -o jsonpath='{.items[0].metadata.namespace}')
echo "cell namespace: $NS"
cd ~/oc-201-labs/lab3-policy-check
./scripts/check-live.sh $NS
```

Read each result. A failure shows where the platform's defaults and your policy disagree, for example a missing `team` label. Decide which should change; in OpenChoreo the fix usually goes in the ComponentType.

## E. Compare declared and observed

### 10. Call it from inside and outside the platform

Call the service through the gateway, then from a pod outside the cell by its cluster address.

```bash
URL=http://development-default.openchoreoapis.localhost:19080/greeter-governed-http
for i in $(seq 1 5); do curl -s $URL/greeter/greet; done

NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-governed \
  -o jsonpath='{.items[0].metadata.namespace}')
PORT=$(kubectl get svc greeter-governed -n $NS -o jsonpath='{.spec.ports[0].port}')
kubectl delete pod curl-test -n default --ignore-not-found
kubectl run curl-test -n default --restart=Never --image=curlimages/curl -- \
  curl -sS -m 5 http://greeter-governed.$NS.svc.cluster.local:$PORT/greeter/greet
sleep 20
kubectl logs curl-test -n default
kubectl delete pod curl-test -n default
kubectl get networkpolicy -n $NS
```

The gateway calls answer `Hello, Stranger!`. The call from outside the cell fails with `Could not connect to server`: OpenChoreo puts an ingress NetworkPolicy on every component (`openchoreo-greeter-governed`) that admits only allowed sources such as the gateway. Your `default-deny-egress` sits beside it and controls the other direction.

```bash
NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-governed \
  -o jsonpath='{.items[0].metadata.namespace}')
kubectl get networkpolicy openchoreo-greeter-governed -n $NS -o yaml | grep -A20 ingress:
# is the Cilium network module present
kubectl get pods -n kube-system -l k8s-app=cilium
```

With Cilium, the cell diagram's runtime view shows the gateway flow as forwarded and the curl-test flow as dropped. `No resources found` means the module is not installed: the default k3d install uses flannel, and the module needs Cilium as the cluster's network plugin, which means recreating the cluster. Skip the view; the next step uses what you just saw.

### 11. Compare the two lists

Write the declared dependencies and the observed connections, one `source -> destination` per line, then compare. The sample files show all three outcomes first.

```bash
cd ~/oc-201-labs/lab3-policy-check
./scripts/compare_deps.py inputs/declared-deps.txt inputs/observed-deps.txt

printf '%s\n' 'gateway -> greeter-governed' > my-declared.txt
printf '%s\n' 'gateway -> greeter-governed' > my-observed.txt
./scripts/compare_deps.py my-declared.txt my-observed.txt --strict
echo "exit status: $?"
```

On the samples the script prints connections on both sides, observed but never declared, and declared but never observed. On your files every observed connection was declared, so `--strict` exits 0. `curl-test -> greeter-governed` is not in the observed list because the policy refused it. An undeclared connection that works would be a gap in the cell's policy: declare it, or tighten the policy so it stops.

## Checkpoint

- [ ] `bad-deploy.json` is denied with violations; `good-deploy.json` passes
- [ ] Each `governed-demo` cell namespace contains `cell-quota` and `default-deny-egress`
- [ ] `check-live.sh` prints a result for the `greeter-governed` Deployment
- [ ] The call from `curl-test` outside the cell is refused, and you can name the policy that refused it
- [ ] `compare_deps.py` shows all three groups on the samples and exits 0 with `--strict` on your files

## Troubleshooting

- `permission denied` on a script: run `chmod +x ~/oc-201-labs/lab3-policy-check/scripts/*`.
- `create-governed-project.sh` says it could not read the pipeline: run `kubectl get project default -n default -o yaml` and check `spec.deploymentPipelineRef`.
- `resourcequotas "cell-quota" is forbidden` in `kubectl get projectreleasebinding governed-demo-development -n default -o yaml`: run the grant block in step 6, then `kubectl annotate projectreleasebinding governed-demo-development -n default lab/retry=$(date +%s) --overwrite`.
- No cell namespaces or no Deployment: run `kubectl get projectreleasebindings -n default | grep governed-demo`. If nothing is listed, run `create-governed-project.sh` again; it creates the bindings.
- `greeter-governed` does not deploy: run `kubectl get releasebinding greeter-governed-development -n default -o jsonpath='{.status.conditions}'`; `namespaces ... not found` means the project has no ProjectReleaseBindings.
- `check-live.sh` prints `no deployments`: the component is not deployed yet; run the `kubectl wait` line again.
- `pods "curl-test" already exists`: run `kubectl delete pod curl-test -n default`, then the block again.
- The call from `curl-test` answers: the component has no ingress policy. Run `kubectl get networkpolicy -A | grep greeter-governed`.

---

Previous: [Lab 2](../lab2-device-login/WORKBOOK-local.md) · [All modules](../WORKBOOK.md) · Next: [Lab 4](../lab4-agents/WORKBOOK-local.md)
