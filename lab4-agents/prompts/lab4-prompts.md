# Prompts for Lab 4

Use these in order, each as its own prompt. They name `greeter-service`, the service from Lab 1.

1. List the namespaces, projects and components you can see in OpenChoreo. Use only the OpenChoreo MCP tools.
2. Explain the `greeter-service` component: its ComponentType, its endpoints, and the environments it is bound to. Use only the OpenChoreo MCP tools.
3. Read the last 50 log lines for `greeter-service` and summarize anything unusual. Use only the OpenChoreo MCP tools.
4. List the release bindings for `greeter-service` and tell me which release each environment is running. Use only the OpenChoreo MCP tools.
5. Show the audit log entries for the calls you just made. Use only the OpenChoreo MCP tools.

## What to look for

- In prompts 1, 2 and 4 the agent calls tools on `openchoreo-cp`. In prompts 3 and 5 it calls tools on `openchoreo-obs`. Your agent shows each tool call. If it runs `kubectl` instead, the servers are not connected in that session.
- If a call is denied, the role bound to your sign-in does not allow it. That is the same authorization you set up in Lab 2.
- In prompt 5 the entries should match the calls from prompts 1 to 4. With the token route the caller is `service_mcp_client`, not your user: the agent is its own identity, authorized by its own role binding.

## Stretch

With the skills installed:

`Draft a Component for a new service called inventory-api using this platform's own ComponentType schema. Show the YAML; do not apply it.`

Then remove the skills with `npx skills remove openchoreo-developer openchoreo-platform-engineer`, ask the same prompt in a new session, compare the field names, and reinstall with `./scripts/install-skills.sh`.
