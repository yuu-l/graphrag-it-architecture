# Agent Orchestration

## Agent Source

Use only agents that exist in `.claude/ccpv/agents`. Do not reference or invoke agents that are not present in that directory.

## Available Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| build-error-resolver | Resolves build, TypeScript, dependency, and configuration errors with minimal diffs. | When builds, type checks, linting, imports, or package resolution fail. |
| code-explorer | Traces existing features, execution paths, architecture layers, and dependencies. | Before implementing unfamiliar features or changing code you do not fully understand. |
| database-reviewer | Reviews database queries, schema design, migrations, security, and performance. | When changing SQL, ORM models, migrations, indexes, transactions, or database access paths. |
| doc-updater | Updates documentation, codemaps, READMEs, guides, and repository maps. | After behavior, architecture, setup steps, APIs, or developer workflows change. |
| docs-lookup | Fetches current library, framework, and API documentation through Context7 MCP. | When API behavior, setup, examples, or version-specific usage is uncertain. |
| fastapi-reviewer | Reviews FastAPI applications for async correctness, dependency injection, Pydantic schemas, security, OpenAPI quality, tests, and production readiness. | When changing FastAPI routes, dependencies, schemas, middleware, exception handling, or service wiring. |
| python-reviewer | Reviews Python code for correctness, typing, idioms, security, performance, and maintainability. | After any Python code change. Must be used for Python projects. |
| refactor-cleaner | Finds and removes dead code, duplicate code, unused exports, and low-value complexity. | During cleanup work or when consolidation is explicitly part of the task. |
| security-reviewer | Reviews for secrets, injection, SSRF, unsafe crypto, authentication issues, authorization gaps, and OWASP Top 10 risks. | After changes involving user input, auth, APIs, files, external calls, secrets, or sensitive data. |
| typescript-reviewer | Reviews TypeScript and JavaScript for type safety, async correctness, Node/web security, and idiomatic patterns. | After any TypeScript or JavaScript code change. Must be used for TypeScript or JavaScript projects. |
| vue-reviewer | Reviews Vue code for Composition API correctness, reactivity, component architecture, template security, routing, Pinia, Nuxt, and Vue performance. | When changing `.vue` files or Vue ecosystem code. |

## Immediate Agent Usage

Use the matching agent without waiting for an extra user prompt when the trigger is clear:

1. Unfamiliar existing behavior or unclear call path: use `code-explorer`.
2. Python changes: use `python-reviewer`.
3. FastAPI changes: use `fastapi-reviewer`, and also use `python-reviewer` when Python implementation quality is in scope.
4. TypeScript or JavaScript changes: use `typescript-reviewer`.
5. Vue changes: use `vue-reviewer`, and use `typescript-reviewer` as needed for shared TypeScript or JavaScript logic.
6. Database, SQL, ORM, migration, transaction, or query-performance changes: use `database-reviewer`.
7. Security-sensitive changes: use `security-reviewer`.
8. Failing build, typecheck, lint, import, or dependency resolution: use `build-error-resolver`.
9. Documentation or codemap changes: use `doc-updater`.
10. Library or framework behavior is uncertain: use `docs-lookup`.
11. Cleanup, dead-code removal, or consolidation work: use `refactor-cleaner`.

## Review Routing

Pick the narrowest agent that matches the changed surface. Use multiple agents only when their scopes are genuinely different.

- For backend Python API work, prefer `fastapi-reviewer` plus `python-reviewer`.
- For frontend Vue work, prefer `vue-reviewer` plus `typescript-reviewer`.
- For persistence-layer work, include `database-reviewer` even when the code is written in Python or TypeScript.
- For authentication, authorization, user input, external API calls, file handling, or sensitive data, include `security-reviewer`.
- For build failures, use `build-error-resolver` first, then route the fixed code to the relevant reviewer.
- For documentation-only changes, use `doc-updater` unless the docs require current external API details; then use `docs-lookup` first.

## Parallel Task Execution

Use parallel Task execution for independent agent work. Parallel execution is appropriate when agents inspect different concerns and do not depend on each other's output.

```markdown
# Good: independent parallel reviews
Launch 3 agents in parallel:
1. security-reviewer: Review authentication and user-input handling.
2. database-reviewer: Review migrations, indexes, and query paths.
3. python-reviewer: Review Python implementation quality.

# Bad: dependent sequence treated as parallel
Launch build-error-resolver and reviewer agents before the build errors are understood.
```

## Multi-Perspective Analysis

For complex changes, combine focused agents instead of inventing generic roles:

- `code-explorer` for factual architecture and call-path mapping.
- `security-reviewer` for threat and vulnerability analysis.
- `database-reviewer` for persistence correctness and performance.
- `python-reviewer`, `typescript-reviewer`, `vue-reviewer`, or `fastapi-reviewer` for implementation quality in the affected stack.
- `doc-updater` for keeping documentation and codemaps aligned after the implementation is complete.

## Guardrails

- Do not mention `planner`, `tdd-guide`, `architect`, `code-reviewer`, `go-reviewer`, or `rust-reviewer` unless those agent files exist in `.claude/ccpv/agents`.
- Do not use agents as a substitute for running the project's required checks.
- Do not ask the user which agent to use when the changed files and task type make the routing obvious.
- Do not run cleanup agents during feature or bug-fix work unless cleanup is required to complete the task safely.
