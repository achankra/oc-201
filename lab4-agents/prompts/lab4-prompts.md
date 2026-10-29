# Prompts for Lab 4

Use these in order, each as its own prompt. They name `greeter-service`, the service from Lab 1.

1. List the namespaces, projects and components you can see in OpenChoreo. Use only the OpenChoreo MCP tools.
2. Explain the `greeter-service` component: its ComponentType, its endpoints, and the environments it is bound to. Use only the OpenChoreo MCP tools.
3. Read the last 50 log lines for `greeter-service` and summarize anything unusual. Use only the OpenChoreo MCP tools.
4. List the release bindings for `greeter-service` and tell me which release each environment is running. Use only the OpenChoreo MCP tools.
5. Create a project named `agent-demo` in the default namespace, using the default deployment pipeline and the default project type. Use only the OpenChoreo MCP tools.
6. Show the audit log entries from the last hour. Which of your calls appear, and which do not? Use only the OpenChoreo MCP tools.

## What to look for

- In prompts 1, 2, 4 and 5 the agent calls tools on `openchoreo-cp`. In prompts 3 and 6 it calls tools on `openchoreo-obs`. Your agent shows each tool call. If it runs `kubectl` instead, the servers are not connected in that session.
- Prompt 5 is the only one that changes something. The audit log records changes (create, update, delete), not reads, so prompt 6 finds the project creation and none of the reads, not even a denied one.
- With the token route the caller is `service_mcp_client`, not your user: the agent is its own identity. On the local install that client has the `admin` role, so the agent could change anything. In a real platform, bind the agent's client to the narrowest role that does the job, as you bound a team in Lab 2.
- If the agent says it has no tool to create a project, ask it to list the `openchoreo-cp` tools that create or update something, and use one of those.
- Remove the demo project when you are done: `kubectl delete project agent-demo -n default`.

## Stretch

With the skills installed:

`Draft a Component for a new service called inventory-api using this platform's own ComponentType schema. Show the YAML; do not apply it.`

Then remove the skills with `npx skills remove openchoreo-developer openchoreo-platform-engineer`, ask the same prompt in a new session, compare the field names, and reinstall with `./scripts/install-skills.sh`.
