#!/usr/bin/env python3
"""Command-line client for the device authorization flow."""
import base64, json, time, urllib.error, urllib.request

IDP = "http://127.0.0.1:8081"
API = "http://127.0.0.1:8082"


def call(url, data=None, headers=None):
    """Return (status, parsed JSON body). HTTP errors are returned, not raised."""
    body = json.dumps(data).encode("utf-8") if data is not None else None
    hdrs = dict(headers or {})
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs)
    try:
        with urllib.request.urlopen(req) as r:
            return r.getcode(), json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def decode_claims(token):
    """Read the payload of a JWT. The signature is not checked here."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))


def main():
    _, device = call(f"{IDP}/device/code", data={})
    print("\nDevice login")
    print(f"1) Open: {device['verification_uri']}")
    print(f"2) Enter code: {device['user_code']}")
    print("3) Approve in the browser\n")

    while True:
        status, resp = call(f"{IDP}/oauth/token", data={"device_code": device["device_code"]})
        if status == 200:
            token = resp["access_token"]
            break
        if resp.get("error") == "authorization_pending":
            time.sleep(device["interval"])
            continue
        raise SystemExit(f"Login failed: {resp}")

    print("Token issued. Claims in the token (decoded, not verified):")
    print(json.dumps(decode_claims(token), indent=2))
    print("\nCalling the protected API.\n")
    status, resp = call(f"{API}/platform/resource", headers={"Authorization": f"Bearer {token}"})
    print(f"HTTP {status}")
    print(json.dumps(resp, indent=2))


if __name__ == "__main__":
    main()
