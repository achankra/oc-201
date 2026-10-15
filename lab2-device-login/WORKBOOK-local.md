# Lab 2: occ login and access roles

*OC-201 workbook, local install edition. Using the sandbox instead? See [WORKBOOK-sandbox.md](WORKBOOK-sandbox.md).*

**Goal:** See the device-authorization flow end to end, sign in to OpenChoreo from the CLI, and grant a team access with a role and a binding.

## A. The device flow in miniature

### 1. Start the device-login demo

A self-contained demo: an identity provider, a protected API and a CLI. It is separate from the real `occ login`. Use two terminals.

```bash
# terminal 1: the identity provider
cd ~/oc-201-labs/lab2-device-login
python3 idp_server.py
```

```bash
# terminal 2: the API in the background, then the CLI
cd ~/oc-201-labs/lab2-device-login
python3 api_server.py &
python3 cli_login.py
```

Open the URL the CLI prints, enter the six-digit code, choose `platform-team` and press Approve.

### 2. Approve as two other teams

```bash
# terminal 2, run twice: choose payments-team, then guest
python3 cli_login.py
python3 cli_login.py
```

`platform-team` gets HTTP 200; `payments-team` and `guest` get HTTP 403. The client prints the token claims; find `team`. It is the same kind of value an OpenChoreo role binding matches in part D. When you are done, stop both servers:

```bash
# terminal 2
kill %1
# terminal 1: press Ctrl-C
```

## B. occ setup and login

### 3. Point occ at your control plane

> **Verify:** flags can differ between versions. If this fails, run the command with `--help`.

```bash
occ config controlplane update default --url http://api.openchoreo.localhost:8080
occ login
```

A browser opens. Sign in with `admin@openchoreo.dev` / `Admin@123`.

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
occ auditlogs --since 1d
occ auditlogs --since 1d --result denied
```

Evaluation is fail-closed: an allow needs at least one matching binding and no matching deny. The last command shows only the requests that were refused.

## Checkpoint

- [ ] The device-login demo shows access granted for platform-team and forbidden for payments-team and guest
- [ ] `occ namespace list` returns `default`
- [ ] `occ authzrole list -n default` shows `team-developer`

## Troubleshooting

- Browser does not open: copy the URL from the terminal into a browser.
- `Address already in use` in the demo: run `lsof -nP -iTCP:8081 -sTCP:LISTEN` and `lsof -nP -iTCP:8082 -sTCP:LISTEN`, stop what they show, start again.
- Role rejected on apply: compare field names with `kubectl get clusterauthzrole developer -o yaml`.
- Binding has no effect: the value must match the claim in the token exactly. Run the custom-columns command in step 7 again.

---

Previous: [Lab 1](../lab1/WORKBOOK-local.md) · [All modules](../WORKBOOK.md) · Next: [Lab 3](../lab3-policy-check/WORKBOOK-local.md)
