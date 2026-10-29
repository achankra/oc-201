# OpenChoreo terminology

The terms you will meet in OC-201, what each one means in OpenChoreo, what the rest of the industry usually uses for the same job, where that usual approach falls short, and what OpenChoreo does about it. The last line of each entry points to the lab where you use it.

Written for OpenChoreo v1.3.2, and true of v1.3.1 unless an entry says otherwise. Names in `code` are the Kubernetes kinds you can list with `kubectl get`.

## Quick map

| OpenChoreo | Closest industry term |
|---|---|
| Plane (control, data, workflow, observability) | Control plane / data plane split, management cluster and workload clusters |
| Namespace | Tenant, organization, team space |
| Project | Application, system, product |
| Cell | Team namespace with its quotas and network policies; cell-based architecture |
| Component | Service, microservice, deployable |
| Workload | Container spec, Deployment, `docker-compose` service entry |
| Endpoint | Kubernetes Service plus Ingress or HTTPRoute |
| ComponentType | Helm chart or library chart, golden path template, workload profile |
| Trait | Add-on, sidecar, OAM trait, Helm values toggle |
| ProjectType | Namespace template, tenant blueprint, landing zone |
| Workflow | CI pipeline template, buildpack |
| Environment, DeploymentPipeline | Stage, environment folder, promotion pipeline |
| ComponentRelease | Release artifact, versioned bundle |
| ReleaseBinding | Deployment of a version to an environment; a GitOps application per environment |
| RenderedRelease | Rendered manifests, Helm release |
| AuthzRole, AuthzRoleBinding | RBAC role and role binding, mapped from identity groups |
| Audit log | Kubernetes audit log, change log |
| MCP servers, skills | AI assistant tool access and instructions |
| autoDeploy | Continuous deployment on change |
| Alert rule Trait, incident | Prometheus alert rule, Alertmanager route, incident ticket |
| SRE agent | AIOps, automated root-cause analysis |

## Planes

### Control plane, data plane, workflow plane, observability plane

- **In OpenChoreo:** four separate planes. The control plane holds the platform's API, its resources and its controllers, and runs no application workloads. Data planes run workloads. The workflow plane runs builds. The observability plane stores logs, metrics, traces and alerts.
- **Elsewhere:** one cluster often does everything: the platform's own tooling, CI runners, monitoring and the applications share it. Multi-cluster setups add a management cluster that holds admin credentials for every workload cluster.
- **The usual gap:** platform tooling and applications compete for the same capacity and the same blast radius, and the management cluster becomes a store of high-privilege credentials.
- **What OpenChoreo does:** each plane can live in its own cluster. A data plane connects to the control plane through a cluster agent that dials out, so the control plane does not hold kubeconfigs for the data planes. Adding a data plane is registering it (`ClusterDataPlane`), not rewiring pipelines.
- **In the labs:** Lab 1 lists the planes; Lab 7 reads how a second data plane is registered.

### Cluster agent

- **In OpenChoreo:** the process in each remote plane that receives work from the control plane and applies it. It runs in the data, workflow and observability planes. Its Kubernetes permissions decide what OpenChoreo can create there.
- **Elsewhere:** a deployment tool pushes into each cluster with stored credentials.
- **The usual gap:** broad, long-lived credentials held centrally.
- **What OpenChoreo does:** the agent authenticates with a client certificate and connects outward. The other side of this design: anything the agent is not allowed to manage, a template cannot create. Out of the box it cannot manage ResourceQuotas, on any install, so a ProjectType that adds a quota needs the grant Lab 3 adds.
- **In the labs:** Lab 3, step 6.

## Organizing teams and applications

### Namespace (OpenChoreo)

- **In OpenChoreo:** the tenant boundary in the control plane: an organization or a team space that holds projects, environments and pipelines. Shown in the portal as a Domain.
- **Elsewhere:** "namespace" usually means a Kubernetes namespace.
- **The usual gap:** the word means two things, and that causes confusion.
- **What OpenChoreo does:** an OpenChoreo namespace (`default` in the labs) is a control-plane concept. The Kubernetes namespaces your workloads run in are generated cell namespaces such as `dp-default-default-development-…`. When a lab says "the cell namespace", it means the generated one.
- **In the labs:** Lab 1 finds the generated namespace; Lab 3 looks them up by label.

### Project

- **In OpenChoreo:** a group of components that make up one business capability. Shown in the portal as a System. At runtime a project becomes a cell, one per environment.
- **Elsewhere:** an application in a GitOps tool, a System in a service catalog, or just a label.
- **The usual gap:** grouping is a label or a catalog entry. It has no runtime effect, so the boundary between teams exists only on paper.
- **What OpenChoreo does:** the project is the unit of isolation. Its ProjectType decides what every one of its cells contains.
- **In the labs:** Labs 1 and 3.

### Cell

- **In OpenChoreo:** the runtime form of a project in one environment: its own Kubernetes namespace, plus the quotas and network policies its ProjectType adds. Traffic is described by direction: northbound (public ingress), southbound (egress to external services), westbound (internal calls into the cell) and eastbound (calls out to other cells).
- **Elsewhere:** "cell-based architecture" describes isolated, independently deployable units. In day-to-day Kubernetes it is usually a team namespace that someone sets up by hand.
- **The usual gap:** a Kubernetes namespace is not a boundary by default: every pod can reach every other pod, and nothing caps what a team consumes. Quotas and policies get added late, differently per team and per environment, and drift.
- **What OpenChoreo does:** every cell is created from the same ProjectType, through a ProjectReleaseBinding, so each environment gets the same boundary. Every component also gets an ingress NetworkPolicy that admits only allowed sources, such as the gateway. You see this in Lab 3, where a call from outside the cell is refused. Isolation is ingress only by default: nothing limits what a cell's workloads call out to unless the ProjectType adds an egress policy, as Lab 3's governed type does.
- **In the labs:** Lab 3.

## What developers declare

### Component and Workload

- **In OpenChoreo:** a Component is a deployable unit (service, web application, scheduled task, worker) that names its ComponentType. Its Workload is the runtime contract: container image, endpoints, dependencies, configuration.
- **Elsewhere:** developers write a Deployment, a Service and an Ingress, or copy a Helm chart and edit its values.
- **The usual gap:** every team owns hundreds of lines of Kubernetes YAML that encode platform decisions (probes, labels, security context, resources). Those decisions diverge from team to team and are hard to change across all of them.
- **What OpenChoreo does:** the developer declares intent in a short Component and Workload. The platform's ComponentType turns that into the Kubernetes objects.
- **In the labs:** Lab 1 deploys one; Lab 5 deploys one through your own type.

### Endpoint and Dependency

- **In OpenChoreo:** an Endpoint is how a component exposes functionality, with a type, a port and a visibility. The types are HTTP, gRPC, GraphQL, Websocket, TCP and UDP; the API spells it `Websocket`, and `WebSocket` is rejected. Visibility is a list, not a single value. A Dependency is a declared link from one workload to another component's endpoint or to a resource.
- **Elsewhere:** a Service and an Ingress; which services call which is known only from code or traffic.
- **The usual gap:** nobody declares the allowed connections, so the network stays open and a dependency map is reverse-engineered after an incident.
- **What OpenChoreo does:** the network policy comes from each endpoint's visibility, not from declared dependencies, and it covers ingress only. Declared dependencies drive the addresses injected into the workload and document what is meant to connect. The cell's runtime view (with the Cilium network module and a metrics module) shows what actually connects, so you can compare the two.
- **Gateway URL:** for a service component with an external endpoint, the URL follows `http://{environment}-{namespace}.{gateway-host}/{component}-{endpoint}/{path}`. For other components the pattern does not hold. The ReleaseBinding's `status.endpoints` shows the URL actually published.
- **In the labs:** Lab 1 calls an endpoint and reads `status.endpoints`; Lab 3 compares declared and observed connections.

### Resource and ResourceType

- **In OpenChoreo:** managed infrastructure bound to a project, such as a database or a queue, defined by a platform-owned ResourceType (or `ClusterResourceType`).
- **Elsewhere:** Terraform modules or infrastructure claims, run by a separate team on a separate timeline.
- **The usual gap:** infrastructure is provisioned outside the application's lifecycle, so environments drift and requests become tickets.
- **What OpenChoreo does:** a resource is declared next to the components that use it, in the same project and environments. It is promoted separately from the components that use it, so a database change and a service change move on their own.
- **In the labs:** not used in OC-201.

## What the platform team provides

### ComponentType and ClusterComponentType

- **In OpenChoreo:** a template for how one kind of component becomes Kubernetes objects. It sets the workload type in `spec.workloadType` (for example `deployment`), the parameters developers may set, the per-environment settings the platform sets, validation rules, and which Traits and Workflows are allowed. A Component refers to a type as `{workloadType}/{name}`, for example `deployment/service`. `ClusterComponentType` is the cluster-scoped variant (see Cluster-scoped variants).
- **Elsewhere:** Helm library charts, golden path templates in a developer portal, workload profiles, or composition tools.
- **The usual gap:** a template is applied once, when a service is created. After that the service's copy drifts, and a platform improvement has to be pushed to each team as a pull request.
- **What OpenChoreo does:** the type stays the source. A type change does not create releases on its own: a component with `autoDeploy: true` gets a new ComponentRelease built on the changed type and moves to it; a component without it, the default, keeps its release until someone deploys it again. Validations and the allowed lists are checked, and errors show in the object's status, not when you apply it.
- **In the labs:** Lab 5 creates `service-governed` and changes it; its component has `autoDeploy: true`, so the change becomes a new release.

### Trait and ClusterTrait

- **In OpenChoreo:** a reusable operational capability attached to a component, such as an alert rule, autoscaling or a volume. A Trait can create resources and patch the ones the ComponentType generates. Each use has an `instanceName`, so one Trait can attach more than once.
- **Elsewhere:** sidecars injected by admission webhooks, Helm values toggles, OAM traits, or copy-pasted manifests.
- **The usual gap:** each team wires the same capability differently, and nothing says which capabilities a kind of service may use.
- **What OpenChoreo does:** the ComponentType lists the Traits it allows, and the per-environment settings for each Trait live in the ReleaseBinding, so development and production can differ without editing the component.
- **In the labs:** Lab 5 attaches one; Lab 7 uses the alert-rule Trait.

### ProjectType and ClusterProjectType

- **In OpenChoreo:** the template for the cell a project becomes. It must create the namespace (`id: cell-namespace`) and can add ResourceQuotas, NetworkPolicies, baseline RBAC and more.
- **Elsewhere:** namespace templates, tenant blueprints or landing zones, often a script run once when a team is onboarded.
- **The usual gap:** a script runs once, so later changes reach only new teams.
- **What OpenChoreo does:** every cell of every project of that type is rendered from it, per environment. A type change creates a new ProjectRelease, but running cells stay on their current release until each ProjectReleaseBinding is moved to it. A project's type is fixed when the project is created.
- **In the labs:** Lab 3 creates the `governed` type.

### Workflow and ClusterWorkflow

- **In OpenChoreo:** a platform-owned template for a build or automation run, typically an Argo Workflow, such as `dockerfile-builder`.
- **Elsewhere:** each repository has its own CI pipeline file.
- **The usual gap:** hundreds of slightly different pipelines, each maintained by the team that copied it.
- **What OpenChoreo does:** the build runs from a template the platform owns, and the ComponentType lists which Workflows a component may use.
- **In the labs:** Lab 6 builds from source.

### Environment and DeploymentPipeline

- **In OpenChoreo:** an Environment is a deployment stage mapped to a data plane. A DeploymentPipeline declares the allowed promotion paths, by default development to staging to production.
- **Elsewhere:** stages in a CI pipeline, or environment folders and overlays in a Git repository.
- **The usual gap:** promotion rules live inside pipeline scripts and differ per service.
- **What OpenChoreo does:** promotion paths are a platform resource every project uses.
- **In the labs:** Lab 1 lists them; Lab 6 promotes to staging.

### CEL templating: parameters and environment settings

- **In OpenChoreo:** templates use CEL expressions written `${...}`. `parameters` are values the developer sets on the component. `environmentConfigs` is the schema, on the ComponentType or Trait, for values the platform sets per environment. The ReleaseBinding has no field with that name: it carries the values in `componentTypeEnvironmentConfigs` and `traitEnvironmentConfigs`.
- **Elsewhere:** Helm values files per environment.
- **The usual gap:** per-environment values spread across files that developers and the platform team both edit.
- **What OpenChoreo does:** the schema says which values belong to the developer and which to the platform.
- **In the labs:** Lab 5 changes a default in the type's `environmentConfigs` schema; Lab 7 sets `traitEnvironmentConfigs` on a ReleaseBinding.

### Cluster-scoped variants

- **In OpenChoreo:** kinds that start with `Cluster`, such as ClusterComponentType, ClusterTrait, ClusterProjectType, ClusterWorkflow, ClusterResourceType, ClusterAuthzRole and ClusterAuthzRoleBinding, plus the plane kinds such as ClusterDataPlane and ClusterObservabilityPlane. They are visible from every namespace; the namespaced kinds live in one.
- **They do not apply by themselves:** a resource uses a cluster-scoped kind only when it names it with `kind: Cluster...`. A reference without a kind means the namespaced kind.
- **Why it matters:** a platform team publishes shared standards once as cluster-scoped kinds, and a tenant can still add its own.

## Rules that catch people out

### autoDeploy

- **In OpenChoreo:** a field on a Component. With `autoDeploy: true`, a change to the component, its workload or its ComponentType creates a new ComponentRelease and moves the first environment's binding to it. It is off by default.
- **Why it matters:** without it, a platform change reaches no running service until someone deploys again. The greeter sample sets it, which is what Lab 5 part E depends on.
- **In the labs:** Lab 5.

### References and fixed types

- **In OpenChoreo:** a reference to a type, trait or role without a `kind` means the namespaced kind. To use a cluster-scoped one, name it with `kind: Cluster...`. The type of a Component or a Project cannot be changed after creation.
- **Why it matters:** a missing kind points at a namespaced object that may not exist, and a project that needs a different type is a new project. Lab 3 creates `governed-demo` for that reason.
- **In the labs:** Labs 3 and 5.

### Errors show in the status

- **In OpenChoreo:** most validation runs after an object is accepted. `kubectl apply` and `occ apply` succeed, and the error appears in the object's status conditions.
- **Why it matters:** an apply that succeeds is not proof that the object works. Check the status: `kubectl get component lab5-greeter -n default -o jsonpath='{.status.conditions}'`, or `kubectl wait --for=condition=Ready`.
- **In the labs:** every lab waits for Ready after an apply.

### Isolation is ingress only by default

- **In OpenChoreo:** each component's NetworkPolicy, generated from its endpoint visibility, limits who can call in. Nothing limits what a workload calls out to.
- **Why it matters:** egress control is a platform decision you add in the ProjectType, as Lab 3's `default-deny-egress` does.
- **In the labs:** Lab 3.

### Conditions on role mappings

- **In OpenChoreo:** each role mapping in an AuthzRoleBinding can carry conditions, alongside its scope.
- **Why it matters:** this is how you answer "who may deploy this service to production": a mapping scoped to the component, with a condition on the environment, instead of a role that allows deployment everywhere.
- **In the labs:** Lab 2 creates a binding without conditions; read the binding schema with `kubectl explain authzrolebinding.spec`.

### Users and service clients

- **In OpenChoreo:** bindings match users on the `groups` claim, for example `developers`, and service clients on `client_id`, for example `service_mcp_client`.
- **Why it matters:** a pipeline or an agent is not in a group, so binding a group gives it nothing. Bind its `client_id`.
- **In the labs:** Lab 2 reads the claims existing bindings match; Lab 4's agent connects as a service client.

## From declaration to running

### ComponentRelease, ReleaseBinding and RenderedRelease

- **In OpenChoreo:** a ComponentRelease is an immutable snapshot of a component, its workload, its ComponentType and its Traits. A ReleaseBinding binds a release to an environment (named `{component}-{environment}`) and carries that environment's settings. A RenderedRelease is what the control plane applies to the data plane, and it produces the Deployment, Service and HTTPRoute.
- **Elsewhere:** an image tag promoted through environment overlays in Git, with a GitOps tool syncing each environment.
- **The usual gap:** "what is running where" is spread across repositories and tags, a promotion is a pull request that edits a file, and the platform's own template is not part of what was released, so the same tag can deploy differently tomorrow.
- **What OpenChoreo does:** the release captures the application and the platform template together. Promotion moves a binding to a release, and every generated object traces back through labels and owners.
- **In the labs:** Lab 1 traces the chain; Lab 5 sees a type change create a new release for a component with `autoDeploy: true`.

### ProjectRelease and ProjectReleaseBinding

- **In OpenChoreo:** the same pattern for projects. The platform creates a ProjectRelease automatically. A ProjectReleaseBinding owns the cell namespace for one environment, and it is not created automatically for a project you apply with `kubectl`.
- **Why it matters:** a project with no ProjectReleaseBindings has no cells, and nothing can deploy into it. Lab 3's script creates one per environment. A new ProjectRelease reaches a cell only when its binding moves to it.
- **In the labs:** Lab 3.

## Identity and access

### AuthzRole, AuthzRoleBinding and their cluster variants

- **In OpenChoreo:** a role is a list of actions written `resource:verb`, such as `component:view` or `releasebinding:create`. A binding maps one entitlement (a claim and value from the sign-in token) to one or more roles. Each role mapping has its own scope (the namespace, or a project, component or resource) and optional conditions, and the binding has an effect: allow or deny.
- **Elsewhere:** Kubernetes RBAC per cluster, plus portal permissions, plus CI permissions, each configured separately.
- **The usual gap:** Kubernetes RBAC speaks in pods and deployments, not in platform terms, and it is set per cluster, so "who may deploy this service to production" has no single answer.
- **What OpenChoreo does:** permissions are written in the platform's own terms and evaluated by the control plane for the portal, `occ`, the API and AI agents alike. Evaluation fails closed: an allow needs a matching binding and no matching deny. A deny blocks only the entitlement it is bound to: a user who gets an allow through another group still has access.
- **In the labs:** Lab 2.

### Audit logs

- **In OpenChoreo:** a record of the changes made through the OpenChoreo API and MCP servers (create, update and delete), with the authorization decision on each. Reads are not recorded, not even denied reads, and recording reads of the audit log itself is off by default.
- **Elsewhere:** Kubernetes audit logs, which record low-level API calls, and separate CI and portal logs.
- **The usual gap:** no single place answers who changed what in which service.
- **What OpenChoreo does:** platform-level changes are recorded in one log, whoever made them. Calls that go straight to Kubernetes with `kubectl` bypass it. Lab 4 shows the first part: the agent's project creation is there and its reads are not. Lab 7 shows the second, when Claude Code finds no audit record of the injected log lines.
- **In the labs:** Labs 2, 4 and 7.

## AI agents

### MCP servers and skills

- **In OpenChoreo:** two MCP servers, one on the control plane and one on the observability plane, through which an AI agent can list and manage resources, read logs, metrics, traces, alerts and incidents, and update release bindings. Skills are packaged instructions that teach the agent how OpenChoreo works.
- **Elsewhere:** an AI assistant with a terminal and the user's own credentials, working from general knowledge.
- **The usual gap:** the agent guesses field names, acts with whatever access the user has, and its actions are indistinguishable from the user's.
- **What OpenChoreo does:** the agent works through the platform's API as an identity of its own, authorized by role bindings like any user, and the changes it makes are in the audit log under that identity. In the labs it connects as `service_mcp_client`, which has the `admin` role on the local install, so the agent can do anything an admin can. On a real platform you bind the agent's client to the narrowest role that does the job.
- **In the labs:** Lab 4.

### SRE agent and FinOps agent

- **In OpenChoreo:** built-in agents, both off by default. The SRE agent analyzes an incident's logs, metrics and traces and reports likely root causes. The FinOps agent analyzes resource usage and recommends rightsizing; it also needs a FinOps module such as OpenCost.
- **Elsewhere:** separate AIOps products that copy telemetry into their own store.
- **The usual gap:** another tool, another copy of the data, another access model.
- **What OpenChoreo does:** the SRE agent runs inside the observability plane and is triggered per environment from the incident setting in the ReleaseBinding. It speaks the OpenAI API: it works with OpenAI models, or with another provider through an OpenAI-compatible gateway. On v1.3.1 it fails with OpenAI models from gpt-5.6 onward; v1.3.2 fixes this. Lab 7 also uses Claude Code through the MCP servers as an alternative.
- **In the labs:** Lab 7.

## Observability

### Alert rule Trait, notification channel and incident

- **In OpenChoreo:** an alert rule is a Trait on the component. A notification channel is the environment's default destination for alerts, and the alert-rule Trait will not render without one. The ReleaseBinding decides per environment whether a firing rule creates an incident and whether the SRE agent analyzes it.
- **Elsewhere:** alert rules in a separate monitoring repository, routed by a separate configuration.
- **The usual gap:** alerts drift from the services they watch, and the same rule is noisy in development and missing in production.
- **What OpenChoreo does:** the alert travels with the component; how loud it is is set per environment.
- **In the labs:** Lab 5 attaches one; Lab 7 fires one.

### Wirelogs and the cell runtime view

- **In OpenChoreo:** flow records for traffic between workloads, each with a verdict (forwarded or dropped), and the cell diagram's view of what actually connects. Wirelogs come from the Cilium network module; the runtime view also needs a metrics module.
- **Elsewhere:** network flow tools, separate from the platform's model of the application.
- **The usual gap:** network data does not know which service, project or environment a flow belongs to.
- **What OpenChoreo does:** flows are shown on the same cell and component model the developer declared. Wirelogs show traffic only from the moment you open them, not earlier requests, so open them first and then make the request. The default local install does not include Cilium, so in the labs you see the same cases with `kubectl` instead.
- **In the labs:** Labs 3 and 6.

## Tools

### occ

- **In OpenChoreo:** the OpenChoreo CLI. It talks to the OpenChoreo API, so its calls are authorized by your roles and the changes it makes are recorded in the audit log.
- **Compared with `kubectl`:** `kubectl` talks to Kubernetes directly. It is useful for inspecting what the platform generated, but it skips OpenChoreo's authorization and audit.
- **In the labs:** every lab uses both, on purpose.

### Portal

- **In OpenChoreo:** the Backstage-based developer portal. OpenChoreo namespaces, projects and components appear as Domain, System and Component entities without anyone writing catalog files.
- **Elsewhere:** catalog entries written and maintained by hand, which go stale.
- **What OpenChoreo does:** the catalog is generated from what the platform runs, so it stays current. Catalog files are still used for things the platform does not run.
- **In the labs:** Lab 1; OC-210 covers the portal in depth.
