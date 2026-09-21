---
name: ccpv-guidance
description: Use when deciding how ccpv should cooperate with Superpowers in FastAPI, SQLAlchemy, MySQL, Docker, Vue, and TypeScript projects.
---

# ccpv Guidance

Use this plugin together with the unchanged `superpowers` plugin.

## Responsibility Split

Superpowers owns process discipline:

- brainstorming and requirement clarification
- implementation planning
- test-driven development
- systematic debugging
- code-review workflow discipline
- verification before completion
- branch finishing

`ccpv` owns stack-specific guidance:

- FastAPI, Python, Pydantic, SQLAlchemy, Alembic, MySQL
- Docker, deployment, and CI/CD details
- Vue 3, TypeScript, Vite, Pinia, Vue Router
- E2E/browser QA, security review, documentation lookup
- focused build, review, and refactor agents

## Operating Rule

When both plugins could apply, let Superpowers decide the workflow first, then use `ccpv` skills, commands, or agents for the concrete technical lane.

Do not use `ccpv` as a replacement for Superpowers planning, TDD, debugging, or completion verification.
