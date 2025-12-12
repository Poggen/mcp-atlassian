# Add OpenTelemetry tracing and map egress for Drive network policies

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

Drive network policies are moving towards “default deny” between namespaces and to external systems. To avoid being surprised when enforcement is turned on, this system must emit OpenTelemetry (OTEL) telemetry so we can see what outbound connections it actually makes and then define the minimal allowed egress rules.

After this change, when `mcp-atlassian` is deployed in Drive with OTEL enabled, a developer can open Grafana and (a) find traces for the service and see tool-call spans plus outbound HTTP client spans (including the remote hostnames), and (b) use Drive’s “Network Policy Verdicts” view to identify traffic that would be denied and convert that evidence into `extraEgress` rules.

## Progress

- [x] (2025-12-12 14:38Z) Read `.agent/PLANS.md` and captured ExecPlan requirements.
- [x] (2025-12-12 14:38Z) Verified Drive network policy configuration shape (`extraEgress` / `extraIngress`) and how verdicts are viewed in Grafana.
- [x] (2025-12-12 14:38Z) Investigated FastMCP OpenTelemetry discussions (issues #1998 and #1501) and confirmed FastMCP’s middleware system is the right hook for MCP-level spans.
- [x] (2025-12-12 14:38Z) Confirmed Drive’s `drive-service-infra` chart sets OTEL env vars and (when OTEL is enabled) allows egress to the in-cluster collector on TCP 4318 for apps under `apps.*`.
- [x] (2025-12-12 15:45Z) Added OTEL runtime dependencies (OTLP over HTTP) and updated `apps/mcp-atlassian/uv.lock`.
- [x] (2025-12-12 15:45Z) Implemented OTEL bootstrap (`apps/mcp-atlassian/src/mcp_atlassian/utils/otel.py`) and wired it into the CLI entrypoint (`apps/mcp-atlassian/src/mcp_atlassian/__init__.py`).
- [x] (2025-12-12 15:45Z) Emitted MCP operation spans via FastMCP middleware (`apps/mcp-atlassian/src/mcp_atlassian/utils/otel_middleware.py`) and registered it in `apps/mcp-atlassian/src/mcp_atlassian/servers/main.py`.
- [x] (2025-12-12 15:45Z) Instrumented outbound HTTP calls (`requests`) and sanitized URL attributes (strip query/fragment) so spans retain destination hostnames without leaking query parameters.
- [x] (2025-12-12 15:45Z) Added regression tests for OTEL bootstrap + middleware (`apps/mcp-atlassian/tests/unit/test_otel_utils.py`, `apps/mcp-atlassian/tests/unit/test_otel_middleware.py`) and guarded test runs from ambient OTEL env vars (`apps/mcp-atlassian/tests/conftest.py`).
- [x] (2025-12-12 15:45Z) Enabled OTEL in Drive stage values (`infrastructure/stages/dev-euw1/values.yaml`, `infrastructure/stages/stg-euw1/values.yaml`, `infrastructure/stages/prd-euw1/values.yaml`) and updated network policies:
  - main app egress allow-list via `extraEgress` to Jira on TCP 443
  - custom `mcp-atlassian-confluence` Helm templates updated to respect `.Values.drive.otel.enabled` and include a CiliumNetworkPolicy allowing OTEL collector (4318), NATS (4222), and Confluence HTTPS egress
- [x] (2025-12-12 15:45Z) Updated repo docs describing OTEL + network policy expectations (`README.md`, `apps/mcp-atlassian/README.md`).
- [x] (2025-12-12 15:45Z) Ran the repo gate locally and fixed issues found along the way (pre-commit YAML exclusions, mypy/ruff), then verified `uv run pre-commit run --all-files` and `uv run pytest` are green.
- [x] (2025-12-12 15:57Z) Validated the local stage deploy using `mise run d:system:update`, then port-forwarded and confirmed `GET /healthz` returns HTTP 200.
- [x] (2025-12-12 17:32Z) Split the work into stacked PRs to keep “gate/tooling” separate from “OTEL code” and “Drive network policy config” (PRs: #6, #7, #8).
- [ ] (todo) Validate in Grafana in Drive (traces + “Network Policy Verdicts”), then tighten/promote egress allow-lists based on evidence.

## Surprises & Discoveries

- Observation: This repo’s Drive stage values originally had OTEL disabled (`drive.otel.enabled: false`), so even if the app were instrumented, the platform-provided env vars would request “no export”. This was flipped to `true` in dev/stg/prd as part of this work.
  Evidence (in this repo): `infrastructure/stages/dev-euw1/values.yaml`, `infrastructure/stages/stg-euw1/values.yaml`, `infrastructure/stages/prd-euw1/values.yaml`.

- Observation: Drive’s charting already wires up OTEL env vars and a network policy allow-list to the in-cluster collector on TCP 4318, but only for apps declared under `apps.*`.
  Evidence (from the chart behavior we validated): it sets `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-in-cluster-collector.monitoring.svc.cluster.local:4318` and toggles `OTEL_TRACES_EXPORTER` between `otlp` and `none`, and it creates a CiliumNetworkPolicy egress rule to `otel-in-cluster-collector` on port 4318 when OTEL is enabled.

- Observation: This system runs a second “confluence” deployment via a custom Helm template (`mcp-atlassian-confluence`). That template used to hard-code `OTEL_*_EXPORTER=none`, which meant it would not export traces even when OTEL was enabled for the system. The template now respects `.Values.drive.otel.enabled`.
  Evidence (in this repo): `infrastructure/stages/*/templates/mcp-atlassian-confluence.yaml`.

- Observation: FastMCP mainline does not ship built-in OpenTelemetry instrumentation yet (issues #1501 and #1998 are still open), but FastMCP’s middleware hooks (`on_call_tool`, `on_read_resource`, etc.) are sufficient for emitting spans from the application layer.
  Evidence: `gh issue view 1501 -R jlowin/fastmcp --comments` and `gh issue view 1998 -R jlowin/fastmcp --comments` during investigation.

- Observation: There is an upstream draft PR in FastMCP that adds a built-in `OpenTelemetryMiddleware` (including `_meta` trace context propagation) and an optional dependency extra (`fastmcp[opentelemetry]`). It is not merged/released at the time of writing, but it is a good reference implementation for span naming, attribute choices, and propagation behavior.
  Evidence: `gh pr view 2001 -R jlowin/fastmcp --comments` during investigation.

- Observation: Running the repo’s gate surfaced that pre-commit’s `check-yaml` hook fails on Helm templates (they are not valid YAML until rendered). We excluded rendered-only template paths from `check-yaml`.
  Evidence (in this repo): `apps/mcp-atlassian/.pre-commit-config.yaml`.

- Observation: Running mypy via pre-commit surfaced a duplicate-module-name error when mypy was invoked per-file under `apps/mcp-atlassian/src` (`mcp_atlassian.*` vs `src.mcp_atlassian.*`). We made the mypy hook run on the package directory (`pass_filenames: false`) to stabilize module discovery.
  Evidence (in this repo): `apps/mcp-atlassian/.pre-commit-config.yaml`.

- Observation: `apps/mcp-atlassian/tests/test_real_api_validation.py` claimed it was skipped unless `--use-real-data`, but fixtures constructed configs unconditionally and failed when env vars were missing. We added a module-level guard fixture so it is skipped unless the flag is provided (and also pinned anyio to `asyncio` to avoid `trio` backend failures for the FastMCP client).
  Evidence (in this repo): `apps/mcp-atlassian/tests/test_real_api_validation.py`.

- Observation: The kind-based local stage does not include the `monitoring` namespace (no in-cluster OTEL collector), so local stage validation focuses on “build + deploy + health” rather than OTLP export to a collector.
  Evidence (local kind cluster): `kubectl get ns` shows no `monitoring` namespace.

## Decision Log

- Decision: Implement OTEL in `mcp-atlassian` itself (safe, optional bootstrap + middleware), rather than waiting for FastMCP to grow first-class OTEL.
  Rationale: We need telemetry now to derive egress allow-lists before Drive enforces default-deny policies; FastMCP issues indicate this is not yet standardized upstream.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Mirror the upstream FastMCP draft PR’s span model where practical, but keep implementation local until upstream is merged and released.
  Rationale: Aligning with upstream conventions reduces long-term maintenance and makes it easier to switch to the upstream middleware later without changing dashboards/queries.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Use OTLP over HTTP (port 4318) for exports.
  Rationale: Drive’s in-cluster collector endpoint is configured at TCP 4318, and the Docker base image is Alpine; avoiding gRPC reduces native build risk and image size.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Do not include tool arguments or HTTP query strings in spans by default.
  Rationale: MCP tool arguments and URLs may contain sensitive data. For network policy work we mainly need destination hostnames/ports; payloads are not required.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Keep the existing custom “confluence” deployment for now, but update it to respect the shared OTEL enable/disable switch and to participate in the same network policy model.
  Rationale: Removing templates is a higher-coordination change. Updating the template keeps behavior stable while making network-policy enforcement feasible.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Treat OTEL as opt-in at runtime: only initialize tracing when `OTEL_TRACES_EXPORTER` is explicitly set and not `none`.
  Rationale: The Drive chart sets OTEL env vars when enabled; locally we do not want surprising exports or console spam unless a developer asks for it.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Do not implement `_meta` trace-context propagation yet; keep spans local to this service.
  Rationale: The immediate requirement for network policies is destination hostnames/ports; propagation across MCP clients is a larger compatibility surface that is likely to change when FastMCP merges its built-in OTEL support.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Enable `drive.otel.enabled: true` in dev/stg/prd values in this repo (not dev-only).
  Rationale: Keeping stages consistent avoids configuration drift and means we can compare traffic and verdicts across environments; if OTEL volume becomes an issue, it can be toggled off per-stage without changing the image.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Adjust repo tooling (pre-commit + mypy) to reflect the presence of Helm templates and the `src/` layout.
  Rationale: `check-yaml` cannot validate Helm templates, and mypy module discovery was unstable when invoked per-file under `apps/mcp-atlassian/src`; fixing the gate keeps this change shippable and repeatable.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Skip real API validation tests by default unless `pytest --use-real-data` is provided.
  Rationale: These tests require env vars and modify external systems; making them opt-in keeps CI/dev loops reliable while still enabling manual validation runs.
  Date/Author: 2025-12-12 / GPT-5.2

- Decision: Split delivery into stacked PRs (gate → OTEL → infra).
  Rationale: Reviewers can merge the “mechanical” repo gate fixes first, then review the OTEL feature with a clean diff, and finally review stage/policy changes separately.
  Date/Author: 2025-12-12 / GPT-5.2

## Outcomes & Retrospective

Implemented OpenTelemetry tracing + network-policy prep for `mcp-atlassian`:

- Added an OTEL bootstrap that is safe and opt-in via env vars, with OTLP/HTTP export support and `requests` instrumentation (URL attributes are sanitized to strip query/fragment).
- Added FastMCP middleware spans for MCP operations (tool calls, resource reads, prompt gets) so traces correlate user-visible MCP calls to outbound HTTP spans.
- Updated Drive stage configs to enable OTEL and added/updated network policies so the service can reach the in-cluster OTEL collector, NATS, and its external Atlassian endpoints when enforcement becomes default-deny.
- Added unit tests for the OTEL utilities and middleware and ensured the repo gate (pre-commit + pytest) is green.

Evidence captured locally:

    cd apps/mcp-atlassian
    uv run pre-commit run --all-files
    uv run pytest

Expected test summary (from this implementation run):

    1022 passed, 212 skipped

What remains (requires a Drive deployment + Grafana access):

- Validate in Grafana that traces appear in Tempo and that HTTP spans expose the correct destination hostnames.
- Use the “Network Policy Verdicts” dashboard to tighten/confirm the minimal `extraEgress` rules (and the confluence CiliumNetworkPolicy) based on observed traffic.
- Revisit once FastMCP merges/releases native OTEL support and consider replacing the local middleware with upstream implementation to gain `_meta` propagation.

## Context and Orientation

This repository contains a Drive-deployed MCP server that talks to Atlassian Jira and Confluence and exposes tools via FastMCP. The code is a Python package under `apps/mcp-atlassian/`.

The runtime entrypoint is `apps/mcp-atlassian/src/mcp_atlassian/__init__.py` (a Click CLI). It loads env vars, chooses a transport (stdio/sse/streamable-http), then starts the FastMCP server with `main_mcp.run_async(...)`.

The main FastMCP server is defined in `apps/mcp-atlassian/src/mcp_atlassian/servers/main.py` as `main_mcp = AtlassianMCP(...)` and mounts Jira and Confluence sub-servers. Most outbound HTTP calls in this codebase are made through Python `requests` (directly and via the `atlassian-python-api` dependency).

Drive deployment configuration lives under `infrastructure/stages/<stage>/values.yaml`. These values feed the `drive-service-infra` chart (via the `drive:` alias) which creates Deployments, Services, HTTPRoutes, and CiliumNetworkPolicies.

Drive network policy basics (embedded here so this plan is self-contained):

- “Default deny” means pods cannot send traffic (egress) or receive traffic (ingress) unless a policy explicitly allows it.
- For egress to external domains, the Cilium policy construct is `toFQDNs` with `matchName`/`matchPattern`, typically paired with `toPorts` to restrict ports and protocols.
- Drive exposes a safe way to add such rules via a Helm value `apps.<appName>.extraEgress`, a list of egress rules. A minimal example that only allows HTTPS to a single domain is:

    apps:
      probe:
        extraEgress:
          - toFQDNs:
              - matchName: "github.com"
            toPorts:
              - ports:
                  - port: "443"
                    protocol: TCP

- Drive’s Grafana includes a dashboard (“Drive / System Overview”) with a “Network Policy Verdicts” graph per namespace. The intended workflow is: deploy, exercise the app, inspect verdicts for denied/unanticipated traffic, then encode only the required egress as `extraEgress`.

OpenTelemetry basics (embedded here so this plan is self-contained):

- OpenTelemetry (OTEL) is a standard for emitting traces (spans), metrics, and logs from applications.
- OTLP is the wire protocol used to export OTEL data to a collector. In Drive we target the in-cluster OTEL collector service at `otel-in-cluster-collector.monitoring.svc.cluster.local` on TCP port 4318 (HTTP).
- A “span” is a timed operation with attributes. For this work, spans must let us answer: “what outbound hostnames did this app call?”

## Plan of Work

We will make OTEL instrumentation a first-class but optional part of the `mcp-atlassian` runtime. The implementation will have three layers:

First, a bootstrap that configures an OTEL tracer provider and exporter when (and only when) OTEL exporting is enabled via environment variables. This must not crash when OTEL libraries are absent (so local users can still run without extra dependencies) and must not require changing the Docker entrypoint.

Second, outbound HTTP client instrumentation for `requests`, which will automatically produce spans for all Jira/Confluence HTTP calls. These spans must preserve destination hostnames (for network policy allow-lists) but must scrub query strings and avoid propagating sensitive headers.

Third, MCP-level spans using FastMCP middleware so we can correlate user-visible MCP tool calls to the HTTP spans they trigger. These spans should be lightweight and privacy-preserving by default (tool name, success/failure, duration).

In parallel, we will update Drive deployment configuration so that:

- OTEL is enabled in the dev stage first.
- Both deployments (`mcp-atlassian` and the custom `mcp-atlassian-confluence`) are allowed to egress to the in-cluster OTEL collector and are configured to actually export traces.
- The minimal required `extraEgress` is declared for Jira/Confluence domains so that when default-deny enforcement is enabled, the system continues working.

Finally, we will validate in Grafana that we can see traces (Tempo) and that network policy verdicts are “clean” (only expected/allowed traffic), then promote the same configuration to staging and production.

## Concrete Steps

All commands below assume the repository root is the working directory unless stated otherwise.

### 1) Add OpenTelemetry dependencies and a bootstrap module

Edit `apps/mcp-atlassian/pyproject.toml` to add OTEL dependencies as normal runtime dependencies (not only dev dependencies). Prefer pure-Python packages that support OTLP/HTTP:

- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp-proto-http`
- `opentelemetry-instrumentation-requests`

Create a new module `apps/mcp-atlassian/src/mcp_atlassian/utils/otel.py` that exposes:

- `setup_otel() -> None`: idempotent, safe if OTEL isn’t installed.
- `shutdown_otel() -> None`: flushes and shuts down the tracer provider if it was initialized.

The bootstrap should behave like this:

- If `OTEL_SDK_DISABLED=true` or `OTEL_TRACES_EXPORTER=none`, do nothing.
- If `OTEL_TRACES_EXPORTER=otlp`, configure an OTLP/HTTP exporter using `OTEL_EXPORTER_OTLP_ENDPOINT` as the base URL. Use batch processing to avoid per-span overhead.
- If `OTEL_TRACES_EXPORTER=console`, configure a console exporter (for local development validation).
- Always create the OTEL resource from env vars: `OTEL_SERVICE_NAME` plus `OTEL_RESOURCE_ATTRIBUTES`.

Wire `setup_otel()` into the process start so it runs before the FastMCP server starts. The simplest place is at the start of `main()` in `apps/mcp-atlassian/src/mcp_atlassian/__init__.py` after env loading but before importing `mcp_atlassian.servers`.

### 2) Instrument outbound HTTP requests

In `setup_otel()`, enable `requests` instrumentation. Add a request hook that:

- Removes query strings from any URL attribute (so we keep only scheme/host/port/path as needed).
- Never attaches request/response headers as span attributes.

Add a small unit test that:

- Forces a console exporter and in-memory span processor.
- Executes a mocked/safe `requests` call.
- Asserts a span was created and includes the destination hostname attribute required for policy creation.

### 3) Add MCP operation spans via FastMCP middleware

Add a new module `apps/mcp-atlassian/src/mcp_atlassian/utils/otel_middleware.py` defining a FastMCP middleware that emits spans for:

- `tools/call` (span name `tool.<toolName>`)
- `resources/read` (span name `resource.read`)
- `prompts/get` (span name `prompt.<promptName>`)

The middleware must:

- Be a no-op if OTEL tracing is disabled.
- Not include tool arguments by default.
- Set basic attributes such as `mcp.method`, `mcp.tool.name`, `mcp.tool.success`.

Register this middleware in `apps/mcp-atlassian/src/mcp_atlassian/servers/main.py` on `main_mcp` (and therefore also for mounted servers).

Add a unit test that constructs a FastMCP server with a trivial tool and validates a “tool call” produces a middleware span (using an in-memory exporter).

### 4) Enable OTEL exports in Drive (dev/stg/prd)

Edit each stage values file and set:

    drive:
      otel:
        enabled: true

Stage files:

- `infrastructure/stages/dev-euw1/values.yaml`
- `infrastructure/stages/stg-euw1/values.yaml`
- `infrastructure/stages/prd-euw1/values.yaml`

This makes the platform set OTEL env vars for the main app deployment and allow egress to the in-cluster collector (port 4318) when policies are enforced. If you want dev-only OTEL exports, revert `stg-euw1`/`prd-euw1` to `enabled: false` until you complete Grafana validation.

Update the custom deployment templates (`infrastructure/stages/*/templates/mcp-atlassian-confluence.yaml`) so their OTEL exporter env vars follow the same enable/disable logic (do not hard-code exporters to `none`). The env var names should match the ones already present in the template (`OTEL_TRACES_EXPORTER`, `OTEL_METRICS_EXPORTER`, `OTEL_LOGS_EXPORTER`).

### 5) Declare minimal `extraEgress` for external Atlassian endpoints

Add `extraEgress` rules for the main app in each stage values file. In this repo’s current layout, `drive.apps.mcp-atlassian` talks to Jira (`JIRA_URL`), while a separate custom deployment talks to Confluence (`drive.confluence.env.CONFLUENCE_URL`). The intent is to allow only HTTPS (TCP 443) to the required external Atlassian host(s).

Example shape (replace the hostname with the stage’s actual value):

    drive:
      apps:
        mcp-atlassian:
          extraEgress:
            - toFQDNs:
                - matchName: "wcar-jira-test.riada.se"
              toPorts:
                - ports:
                    - port: "443"
                      protocol: TCP

If the confluence deployment remains custom (not under `drive.apps`), it must get equivalent egress policy coverage. Prefer migrating it into `drive.apps` later, but for now either:

- extend the template to create a CiliumNetworkPolicy for `mcp-atlassian-confluence` that allows `toFQDNs` for the Confluence host on TCP 443, and allows egress to NATS and the OTEL collector, or
- extend the wrapper chart values so the confluence deployment is represented under `drive.apps` and remove the custom template (this is a coordinated refactor; do not do it without agreement).

### 6) Validate locally and in Drive

Local validation (fast feedback):

- Install dependencies and run tests:

    cd apps/mcp-atlassian
    uv sync --frozen --all-extras --dev
    uv run pytest

- Run the server locally with console spans:

    OTEL_TRACES_EXPORTER=console OTEL_SERVICE_NAME=local.mcp-atlassian uv run mcp-atlassian -v --transport streamable-http --port 3000

Then exercise at least one MCP tool call that triggers an outbound HTTP request and confirm spans are printed for both the MCP tool span and the HTTP client span.

Drive dev validation (the reason we’re doing this):

- Deploy to `dev-euw1`, exercise the system, then open Grafana for this system/stage and verify:
  - traces exist for `service.name=mcp-atlassian.mcp-atlassian` (and for the confluence deployment if applicable),
  - outbound HTTP spans show the destination hostname for Jira/Confluence calls,
  - “Network Policy Verdicts” for the namespace is quiet or points to only the expected domains/capabilities.

## Validation and Acceptance

Acceptance requires observable behavior, not just code changes:

1. When running locally with `OTEL_TRACES_EXPORTER=console`, a single tool call produces at least:
   - one span representing the MCP tool call (named `tool.<toolName>`), and
   - one span representing the outbound HTTP request made by that tool (from requests instrumentation).

2. In Drive `dev-euw1` with `drive.otel.enabled: true`, Grafana shows traces for the service within a few minutes of generating traffic, and the trace data includes the destination hostnames needed for egress policy rules.

3. After adding `extraEgress` for the Jira/Confluence hosts, Drive’s “Network Policy Verdicts” view no longer reports denied/unanticipated egress for normal system usage (excluding explicit future integrations).

## Idempotence and Recovery

All changes must be safe to apply repeatedly:

- OTEL bootstrap must be idempotent and must not double-instrument `requests` or install duplicate span processors.
- Disabling OTEL exports must be possible by setting `drive.otel.enabled: false` (in Drive) or `OTEL_TRACES_EXPORTER=none` (locally).

If telemetry causes instability or volume issues, recovery is:

- immediately set `OTEL_TRACES_EXPORTER=none` for the affected stage to stop exports without rolling back the image, then
- adjust sampling and/or disable MCP middleware spans while keeping HTTP spans.

## Artifacts and Notes

Key env vars expected in Drive when OTEL is enabled (these are set by the platform chart for normal apps):

    OTEL_SERVICE_NAME=<system>.<app>
    OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-in-cluster-collector.monitoring.svc.cluster.local:4318
    OTEL_EXPORTER_OTLP_INSECURE=true
    OTEL_RESOURCE_ATTRIBUTES=service.namespace=<system>-<stage>,service.stage=<stage>
    OTEL_TRACES_EXPORTER=otlp

Minimal egress rule pattern we will use for external Atlassian endpoints:

    extraEgress:
      - toFQDNs:
          - matchName: "<jira-or-confluence-host>"
        toPorts:
          - ports:
              - port: "443"
                protocol: TCP

## Interfaces and Dependencies

Python packages (runtime dependencies) to add under `apps/mcp-atlassian/pyproject.toml`:

- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp-proto-http`
- `opentelemetry-instrumentation-requests`

New internal interfaces to add:

- In `apps/mcp-atlassian/src/mcp_atlassian/utils/otel.py`, define `setup_otel()` and `shutdown_otel()` (both must be safe when OTEL is disabled or not installed).
- In `apps/mcp-atlassian/src/mcp_atlassian/utils/otel_middleware.py`, define a FastMCP middleware class that emits spans for MCP operations.

Plan update note (2025-12-12 14:38Z): Added a discovery about the upstream FastMCP draft PR adding a built-in `OpenTelemetryMiddleware`, and recorded the decision to mirror that span model locally so we can align with upstream conventions while still delivering telemetry now. Also normalized gh evidence commands to avoid embedding raw GitHub URLs.

Plan update note (2025-12-12 15:45Z): Updated the plan to reflect the completed implementation (OTEL bootstrap + FastMCP middleware + Drive config changes), fixed outdated expectations (span names, stage rollout), and recorded local evidence (`pre-commit` + `pytest` green) plus remaining Drive/Grafana validation work.

Plan update note (2025-12-12 17:32Z): Recorded that the work was published as stacked PRs (gate → OTEL → infra/network-policies) to simplify review and reduce merge conflicts while Drive/Grafana validation remains outstanding.
