# Lab 3: policy check, governed cell, runtime view

A Rego policy checks a Deployment before it would be created. A ClusterProjectType gives a project's cells a quota and default-deny egress. A call from outside the cell then shows the boundary is real, and a comparison shows whether the traffic matches what the application declared. This README follows Lab 3 in the workbook.

| Path | Purpose |
|---|---|
| `policies/deployment.rego` | The rules. Each rule adds a message to a set called `violations` |
| `inputs/bad-deploy.json` | A Deployment that breaks several rules |
| `inputs/good-deploy.json` | A Deployment that passes |
| `inputs/declared-deps.txt` | Sample declared dependencies, one `source -> destination` per line |
| `inputs/observed-deps.txt` | Sample observed connections, same format |
| `governed-project-type.yaml` | The default ClusterProjectType plus a ResourceQuota and a default-deny egress NetworkPolicy that still allows DNS |
| `scripts/check.sh` | Runs the policy against one input file with `opa` |
| `scripts/check-live.sh` | Runs the same policy on every Deployment in a namespace on your cluster |
| `scripts/create-governed-project.sh` | Creates the `governed-demo` project, its ProjectReleaseBindings, and waits for its cells |
| `scripts/compare_deps.py` | Compares declared dependencies with observed connections |
| `reference/` | Copies of the files you create in this lab, for catching up |

## Files you create in this lab

These are not in the repository until you run the step that writes them. Git ignores them.

| File | Created in | What it is |
|---|---|---|
| `default-project-type.yaml` | part C | The built-in `default` ClusterProjectType, exported to compare with the governed one |
| `lab3-project.yaml` | part D, by `create-governed-project.sh` | The `governed-demo` Project, using the `governed` type |
| `my-declared.txt`, `my-observed.txt` | part E | Your one-line dependency lists for the `--strict` comparison |

If a step fails or you fall behind, copy the file from `reference/`, for example `cp reference/default-project-type.yaml .`, and carry on from the next step.

## Requirements

- `opa`. On macOS: `brew install opa`. On Linux, the release binary from openpolicyagent.org.
- Python 3.9 or newer. No other packages.
- `kubectl` pointed at your k3d cluster.

## A. Policy at the point of change

```
cd ~/oc-201-labs/lab3-policy-check
chmod +x scripts/*.sh scripts/*.py
./scripts/check.sh inputs/bad-deploy.json
./scripts/check.sh inputs/good-deploy.json
grep -n "latest" policies/deployment.rego
```

The bad input prints `allow: false` and its violations: no `team` label, an image tagged `latest`, no memory request or limit, no `securityContext`. The good input prints `PASS: compliant`.

A Deployment is denied when:

- the `team` or `environment` label is missing
- a container image ends in `:latest`
- a container has no CPU or memory request
- a container has no CPU or memory limit
- the pod has no `securityContext`, or it does not set `runAsNonRoot` to true

## B. Look at a cell

A project gets one cell namespace per environment, through one ProjectReleaseBinding each. The names are generated, so look them up by label.

```
kubectl get projectreleasebindings -A
kubectl get namespaces -l openchoreo.dev/project=default -L openchoreo.dev/environment
```

The default project type creates only the namespace, so the cells have no quota or policy yet.

## C. Author a governed project type

The data plane agent creates everything a project type renders. Out of the box it may not manage ResourceQuotas, and the cell then fails with `resourcequotas ... is forbidden`. Grant it once per cluster; `AlreadyExists` means the grant is there.

```
kubectl create clusterrole lab-cluster-agent-quotas \
  --verb=get,list,watch,create,update,patch,delete --resource=resourcequotas,limitranges
kubectl create clusterrolebinding lab-cluster-agent-quotas \
  --clusterrole=lab-cluster-agent-quotas \
  --serviceaccount=openchoreo-data-plane:cluster-agent-dataplane
```

Compare the governed type with the default, then apply it:

```
cd ~/oc-201-labs/lab3-policy-check
kubectl get clusterprojecttype default -o yaml > default-project-type.yaml
diff default-project-type.yaml governed-project-type.yaml
kubectl apply --dry-run=server -f governed-project-type.yaml
kubectl apply -f governed-project-type.yaml
kubectl get clusterprojecttypes
```

## D. Use it and check it

```
cd ~/oc-201-labs/lab3-policy-check
./scripts/create-governed-project.sh
kubectl get resourcequota -A | grep -E 'NAMESPACE|cell-quota'
kubectl get networkpolicy -A | grep -E 'NAMESPACE|default-deny-egress'
```

The script reads the deployment pipeline from the `default` project, writes and applies `lab3-project.yaml`, creates a ProjectReleaseBinding for each pipeline environment, and waits for the cells. Without the bindings the project has no cell namespaces and nothing deploys into it. Pass a project name and a type name to change the defaults: `./scripts/create-governed-project.sh my-project governed`.

Deploy the greeter into the governed project and run the policy against the live Deployment:

```
BASE=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.3/samples
curl -fsSL $BASE/from-image/go-greeter-service/greeter-service.yaml \
  | sed -e 's/ame: greeter-service/ame: greeter-governed/' \
        -e 's/projectName: default/projectName: governed-demo/' \
  | kubectl apply -f -
for i in $(seq 1 36); do
  kubectl get deployment -A -l openchoreo.dev/component=greeter-governed -o name \
    | grep -q . && break
  sleep 5
done
kubectl wait --for=condition=available deployment -A \
  -l openchoreo.dev/component=greeter-governed --timeout=180s
NS=$(kubectl get deployment -A -l openchoreo.dev/component=greeter-governed \
  -o jsonpath='{.items[0].metadata.namespace}')
cd ~/oc-201-labs/lab3-policy-check
./scripts/check-live.sh $NS
```

A failure shows where the platform's defaults and your policy disagree, for example a missing `team` label. In OpenChoreo the fix usually goes in the ComponentType, not the Deployment.

## E. Compare declared and observed

Call the service through the gateway, then from a pod outside the cell:

```
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

The gateway calls answer `Hello, Stranger!`. The outside call fails with `Could not connect to server`: OpenChoreo puts an ingress NetworkPolicy on every component (`openchoreo-greeter-governed`) that admits only allowed sources such as the gateway. Your `default-deny-egress` controls the other direction.

With the Cilium network module, the cell diagram's runtime view in the portal shows the gateway flow as forwarded and the curl-test flow as dropped. The default k3d install uses flannel; the module needs Cilium as the cluster's network plugin, which means recreating the cluster. Check with `kubectl get pods -n kube-system -l k8s-app=cilium`. Without it, use what the commands above showed.

Compare the lists:

```
cd ~/oc-201-labs/lab3-policy-check
./scripts/compare_deps.py inputs/declared-deps.txt inputs/observed-deps.txt
printf '%s\n' 'gateway -> greeter-governed' > my-declared.txt
printf '%s\n' 'gateway -> greeter-governed' > my-observed.txt
./scripts/compare_deps.py my-declared.txt my-observed.txt --strict
echo "exit status: $?"
```

On the samples the script prints three groups: on both sides, observed but never declared, declared but never observed. On your files `--strict` exits 0. An undeclared connection that works is a gap in the cell's policy: declare it, or tighten the policy so it stops.

## If something fails

- `resourcequotas "cell-quota" is forbidden` on the ProjectReleaseBinding: run the grant in part C, then `kubectl annotate projectreleasebinding governed-demo-development -n default lab/retry=$(date +%s) --overwrite`.
- No cell namespaces, or `namespaces ... not found` on the greeter's ReleaseBinding: the project has no ProjectReleaseBindings. Run `create-governed-project.sh` again.
- `pods "curl-test" already exists`: run `kubectl delete pod curl-test -n default`.
- `check-live.sh` prints `no deployments`: the component is not deployed yet; run the `kubectl wait` line again.

## Things to try

- Add `"team": "payments-team"` to the labels in the bad input and run it again. One violation disappears.
- Write a rule that rejects a container without a `readinessProbe` and run the bad input.
- Add a line to `my-observed.txt` that is not in `my-declared.txt` and run the comparison with `--strict`.

## How it maps to OpenChoreo

In a cluster the same rules run at admission, before an object is created. The policy limits what may be submitted. The cell limits what a team can consume and reach. A project type can only stamp out what the data plane agent is allowed to manage, so its permissions are part of your governance design.
