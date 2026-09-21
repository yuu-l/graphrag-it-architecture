# ccpv

`ccpv` is a trimmed Claude Code plugin extracted from ECC for a Python FastAPI + SQLAlchemy + MySQL + Docker backend and Vue + TypeScript frontend project.

It is designed to be installed beside the unchanged `superpowers` plugin. Superpowers owns the process layer: planning, TDD, systematic debugging, verification before completion, branch finishing, and code-review workflow discipline. This plugin owns stack-specific engineering support: FastAPI, Python, SQLAlchemy/MySQL, Docker/deployment/Aliyun release automation, Vue/TypeScript, E2E, security, docs, and focused review agents.

## Included

- Skills for FastAPI, Python, testing, API design, backend patterns, database migrations, MySQL, Docker, deployment, Aliyun ECS/RDS/ACR release automation, Vue, Vite, UI-to-Vue, frontend patterns, browser/E2E QA, documentation lookup, error handling, security review, and security scan.
- `ccpv-guidance`, a lightweight coordination skill that tells Claude Code to let Superpowers own process flow and use this plugin for stack-specific technical work.
- Agents for FastAPI, Python, Vue, TypeScript, database, security, build errors, E2E, docs, code review, code exploration, and refactoring cleanup.
- Slash commands for review, build-fix, FastAPI/Python/Vue review, PR review, quality gate, security scan, test coverage, docs update, and ECC guide.
- Lightweight hooks for risky Bash command blocking and stack-specific verification reminders.
- GitHub Copilot MCP server via `https://api.githubcopilot.com/mcp`, authenticated with the user-provided `GITHUB_COPILOT_PAT` environment variable.

For a detailed Chinese usage guide for every skill, agent, command, and hook, see [`COMPONENT-GUIDE.md`](./COMPONENT-GUIDE.md).

## Excluded

The following ECC capabilities were intentionally not extracted because they overlap with Superpowers or add broad operational machinery:

- `plan`, `multi-plan`, `plan-prd`, `prp-plan`, `planner`, and planning/orchestration commands.
- `tdd-workflow`, `tdd-guide`, and language-specific TDD commands.
- `verification-loop`, `strategic-compact`, `continuous-learning`, `continuous-learning-v2`, session save/resume/evolve/promote/prune flows.
- Worktree/tmux orchestration, multi-agent execution loops, cost tracking, desktop notifications, and persistent memory hooks.
- Unrelated language stacks such as Go, Rust, Flutter, Kotlin, Java, Laravel, Django, Spring Boot, Swift, and ML-specific modules.

## Install

From a Claude Code session that supports local plugin loading:

```bash
claude --plugin-dir ./ccpv
```

For persistent marketplace-backed installation, add this plugin through your local Claude Code plugin marketplace workflow.

## Manifest Notes

`plugin.json` declares `skills`, `commands`, and the GitHub Copilot MCP server. Claude Code discovers `agents/` and `hooks/hooks.json` by convention; declaring `agents` or the standard `hooks/hooks.json` in the manifest can make validation fail or produce duplicate hook loading.
