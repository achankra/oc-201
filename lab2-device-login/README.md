# Lab 2: device login

Three programs that show how a command-line tool signs a user in without ever handling a password.

| File | Role |
|---|---|
| `idp_server.py` | The identity provider. Issues a device code and a user code, shows an approval page, and returns a signed token once someone approves |
| `api_server.py` | A protected API. Checks the token signature, expiry and audience, then allows only the `platform-team` team |
| `cli_login.py` | The command-line client. Asks for a code, prints where to approve, polls until approved, then calls the API |

## Run it

Use two terminals, both in this folder.

Terminal 1, the identity provider:

```
cd ~/oc-201-labs/lab2-device-login
python3 idp_server.py
```

Terminal 2, the API in the background and then the client:

```
cd ~/oc-201-labs/lab2-device-login
python3 api_server.py &
python3 cli_login.py
```

When you are done, stop the API with `kill %1` in terminal 2 and the identity provider with Ctrl-C in terminal 1.

The client prints a URL and a six-digit code. Open the URL in a browser, enter the code, choose a team, and press Approve. The client then receives a token, prints the claims inside it (`sub`, `team`, `aud`, expiry), and calls the API.

## Without a browser

In a terminal with no browser on the same machine, such as the WSO2 OpenChoreo sandbox, run all three sign-ins with one script. It starts both servers, signs in as each team, and sends the approval with the same form post the approval page makes:

```
cd ~/oc-201-labs/lab2-device-login
./terminal-demo.sh
```

## What you should see

Run the client three times and choose a different team each time.

| Team chosen | API response |
|---|---|
| `platform-team` | HTTP 200, "Access granted to platform resource" |
| `payments-team` | HTTP 403, `forbidden`, with the team the API needed |
| `guest` | HTTP 403, `forbidden` |

The token lives for five minutes. Run the client again for a new one.

## Things to try

- Approve with a code that does not exist, then read the error in the browser.
- Wait more than five minutes after login and call the API with the same token.
- In `api_server.py`, change `ALLOWED_TEAM` and restart the API.
- Find `team` in the printed claims, then change `ALLOWED_TEAM` in the API and see which team now gets through.

## How it maps to OpenChoreo

The client plays the part of `occ login`. The identity provider plays the part of the identity provider that ships with OpenChoreo. The claim the API checks (`team`) is the same kind of value an OpenChoreo role binding matches. In the lab you grant access that way.

## Limits of the demo

The identity provider has no real login, no MFA and no key rotation. Tokens are signed with a shared secret, where a production provider signs with a private key and publishes the public key.

## Grant a team access (workbook Lab 2, part D)

The `access` folder holds the two files the workbook uses.

| File | What it creates |
|---|---|
| `access/team-developer-role.yaml` | An `AuthzRole` named `team-developer` in the `default` namespace |
| `access/team-developer-binding.yaml` | An `AuthzRoleBinding` that gives that role to the `groups` value `team-alpha-developers` on the `default` project |

```
cd ~/oc-201-labs/lab2-device-login/access
kubectl apply --dry-run=server -f team-developer-role.yaml
kubectl apply -f team-developer-role.yaml
kubectl apply --dry-run=server -f team-developer-binding.yaml
kubectl apply -f team-developer-binding.yaml
```
