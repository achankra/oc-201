# Lab 2: occ login and access roles

*OC-201 workbook, WSO2 sandbox edition. Using the local install instead? See [WORKBOOK-local.md](WORKBOOK-local.md).*

**Goal:** See the device-authorization flow end to end, sign in to OpenChoreo from the CLI, and grant a team access with a role and a binding.

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

## A. The device flow in miniature

### 1. Start the device-login demo

A self-contained demo: an identity provider, a protected API and a CLI. The sandbox has no browser on the same machine, so the script sends the approval itself, with the same form post the approval page makes.

```bash
cd ~/oc-201-labs/lab2-device-login
./terminal-demo.sh
```

The script signs in three times: as `platform-team`, `payments-team` and `guest`.

### 2. Read the three results

Scroll back through the output.

```bash
cd ~/oc-201-labs/lab2-device-login
./terminal-demo.sh platform-team | grep -A8 Claims
```

`platform-team` gets HTTP 200; `payments-team` and `guest` get HTTP 403. The client prints the token claims; find `team`. It is the same kind of value an OpenChoreo role binding matches in part D. The script stops both servers when it ends.

## B. occ setup and login

### 3. Point occ at your control plane

The sandbox signed occ in for you, so there is no `occ login` here. Check which server it uses:

```bash
occ version
occ namespace list
```

The server line shows v1.2.2.

## C. Explore from the CLI

### 4. List what you can see

```bash
occ namespace list
occ project list -n default
occ component list -n default
```

Compare with what you saw in the portal.

## D. Grant a team access

### 5. List the roles that already exist

Cluster roles apply in every namespace. The default namespace has none of its own yet.

```bash
occ clusterauthzrole list
occ authzrole list -n default
```

The cluster roles include admin, developer, platform-engineer, namespace-reader and cluster-reader.

### 6. Read one role

```bash
kubectl get clusterauthzrole developer -o yaml
```

Find `spec.actions`. Each action is `resource:verb`, for example `component:view`. `component:*` is every action on components; `*` is everything.

### 7. See the claims the existing bindings match

```bash
kubectl api-resources | grep -i authz
kubectl get clusterauthzrolebindings -o custom-columns=\
NAME:.metadata.name,CLAIM:.spec.entitlement.claim,VALUE:.spec.entitlement.value
```

Users are matched on `groups` (for example `admins`, `developers`); service clients on `client_id`. The local user `developer@openchoreo.dev` (password `Dev@123`) is in the group `developers`.

### 8. Create the developer role

```bash
cd ~/oc-201-labs/lab2-device-login/access
cat team-developer-role.yaml
kubectl apply --dry-run=server -f team-developer-role.yaml
kubectl apply -f team-developer-role.yaml
occ authzrole list -n default
```

The list now shows `team-developer`, an AuthzRole in `default` with seven actions such as `component:view` and `releasebinding:create`.

### 9. Bind the role to a team

The file binds the role to `groups = team-alpha-developers`, limited to the `default` project.

```bash
cd ~/oc-201-labs/lab2-device-login/access
cat team-developer-binding.yaml
kubectl apply --dry-run=server -f team-developer-binding.yaml
kubectl apply -f team-developer-binding.yaml
occ authzrolebinding list -n default
kubectl get authzrolebinding team-alpha-developers -n default -o yaml
```

Optional: bind the same role to the `developers` group that exists on this install, so `developer@openchoreo.dev` gets it:

```bash
cd ~/oc-201-labs/lab2-device-login/access
sed -e 's/name: team-alpha-developers/name: lab-developers/' \
    -e 's/value: team-alpha-developers/value: developers/' \
    team-developer-binding.yaml | kubectl apply -f -
kubectl get authzrolebinding lab-developers -n default -o yaml
```

## E. Review

### 10. Confirm and audit

```bash
occ authzrole list -n default
```

The sandbox's occ is 1.2.0, which has no `auditlogs` command; it arrived in 1.3. Read the audit log in the console instead: open **Audit Logs** in the left menu and filter on the result. If your console has no Audit Logs page, this version does not record them; mark the step N/A. Evaluation is fail-closed: an allow needs at least one matching binding and no matching deny.

## Checkpoint

- [ ] The device-login demo shows access granted for platform-team and forbidden for payments-team and guest
- [ ] `occ namespace list` returns `default`
- [ ] `occ authzrole list -n default` shows `team-developer`

## Troubleshooting

- Role rejected on apply: compare field names with `kubectl get clusterauthzrole developer -o yaml`.
- Binding has no effect: the value must match the claim in the token exactly. Run the custom-columns command in step 7 again.
- `Address already in use` from the demo: an earlier run is still going. Run `pkill -f idp_server.py; pkill -f api_server.py`, then the script again.

---

Previous: [Lab 1](../lab1/WORKBOOK-sandbox.md) · [All modules](../WORKBOOK.md) · Next: [Lab 3](../lab3-policy-check/WORKBOOK-sandbox.md)
