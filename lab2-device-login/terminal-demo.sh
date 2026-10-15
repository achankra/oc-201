#!/usr/bin/env bash
# The device-login demo without a browser, for terminals such as the WSO2 sandbox.
# Starts the identity provider and the API, then signs in once per team.
# The approval that a person would give in the browser is sent with curl:
# the same form post the approval page makes.
set -u
cd "$(dirname "$0")"

python3 -u idp_server.py > /tmp/lab2-idp.log 2>&1 &
IDP=$!
python3 -u api_server.py > /tmp/lab2-api.log 2>&1 &
API=$!
trap 'kill $IDP $API 2>/dev/null' EXIT
sleep 1

for TEAM in "${@:-platform-team payments-team guest}"; do
  for T in $TEAM; do
    echo "================ signing in as $T"
    python3 -u cli_login.py > /tmp/lab2-cli.log 2>&1 &
    CLI=$!
    CODE=""
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      CODE=$(grep -o 'Enter code: [0-9]*' /tmp/lab2-cli.log | awk '{print $3}')
      [ -n "$CODE" ] && break
      sleep 0.5
    done
    echo "user code $CODE, approving for team $T"
    curl -s -o /dev/null -X POST -d "user_code=$CODE&team=$T" http://127.0.0.1:8081/activate
    wait $CLI
    cat /tmp/lab2-cli.log
  done
done
