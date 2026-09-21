---
name: deploy-aliyun
description: Use when designing, generating, or executing an Aliyun deployment workflow for FastAPI/Python/Vue/Docker projects, including ECS bootstrap, code or image release, environment configuration, database schema initialization, health checks, and rollback planning.
---

# Aliyun Deployment

Use this skill when the user asks to deploy a project to Alibaba Cloud / Aliyun, especially ECS, ACR, RDS MySQL, Docker, FastAPI, Vue, or GitHub Actions based deployment.

## Operating Modes

Default to `plan` unless the user explicitly asks to write files or execute deployment commands.

- `plan`: inspect the repository and produce a concrete deployment plan without editing files.
- `init`: generate deployment files such as GitHub Actions workflow, Dockerfile, compose file, ECS bootstrap script, deploy script, healthcheck script, and environment example.
- `deploy`: execute deployment only after showing the exact remote actions and receiving clear user confirmation.
- `rollback`: generate or execute a rollback path using the previous image tag, previous release directory, or previous service unit.

## First Inspection

Read the real project before designing the pipeline:

- `pyproject.toml`, `uv.lock`, `package.json`, `pnpm-lock.yaml`, `package-lock.json`
- `README.md`, `CLAUDE.md`, `.env.example`
- `Dockerfile`, `docker-compose*.yml`, `docker/`
- `alembic.ini`, `alembic/`, migration folders
- `.github/workflows/`
- service entrypoints such as `app/main.py`, `main.py`, `src/`, `api/`

Summarize the detected stack, missing deployment prerequisites, and the safest deployment mode.

## Preferred Architecture

Prefer containerized deployment for production-like Aliyun releases:

1. GitHub Actions checks out code.
2. Run dependency install and tests.
3. Build Docker image.
4. Push image to Aliyun Container Registry (ACR) or GHCR.
5. SSH into ECS using GitHub Secrets.
6. Pull the new image.
7. Render or update `.env` from secrets.
8. Run database schema migration.
9. Restart the app with Docker Compose or systemd.
10. Call the health endpoint and report the result.

For small teaching/demo projects, direct ECS source deployment is acceptable:

1. ECS installs git, uv, Python, nginx, and systemd service files.
2. ECS clones or fetches the repository.
3. ECS writes `.env` from protected variables.
4. ECS runs `uv sync --frozen` or the project-specific install command.
5. ECS runs `uv run alembic upgrade head` if Alembic is present.
6. ECS restarts the service and runs health checks.

## Aliyun Resource Boundary

Do not assume cloud resources already exist. Ask the user to confirm or document these resources:

- ECS instance region, public IP, SSH user, SSH port.
- RDS MySQL host, port, database name, least-privilege account.
- ACR registry namespace and repository if image deployment is used.
- Domain name and HTTPS plan if nginx or TLS is in scope.

Creating or destroying ECS, RDS, VPC, security groups, or DNS records requires an explicit IaC task and separate confirmation. Do not hide those operations inside an app deployment script.

## Secrets

Never write real secrets to the repository. Generate names and examples only.

Typical GitHub Secrets:

- `ALIYUN_ECS_HOST`
- `ALIYUN_ECS_USER`
- `ALIYUN_ECS_PORT`
- `ALIYUN_ECS_SSH_KEY`
- `ALIYUN_ACR_REGISTRY`
- `ALIYUN_ACR_USERNAME`
- `ALIYUN_ACR_PASSWORD`
- `ALIYUN_ACR_NAMESPACE`
- `ALIYUN_ACR_REPOSITORY`
- `APP_ENV_PROD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `OPENAI_API_KEY` or project-specific LLM secrets when needed

If the project uses a single multiline `.env`, prefer `APP_ENV_PROD` and write it to the remote `.env` file with safe permissions.

## Database Initialization

Separate database provisioning from schema initialization:

- Provisioning: RDS instance, database, user, password, network access, backup policy. This is not automatic unless the user explicitly asks for IaC.
- Configuration: inject database connection values through GitHub Secrets or server-side secret management.
- Schema initialization: run the project's migration command.

For Alembic projects, use:

```bash
uv run alembic upgrade head
```

If Alembic is absent, inspect the project for SQL init scripts or ORM-specific migration tools. Do not invent destructive initialization. Never run `drop database`, `drop table`, `truncate`, or irreversible reset commands in production deployment scripts.

## Generated Files

When running `init`, generate only files that match the inspected project:

- `.github/workflows/deploy-aliyun.yml`
- `deploy/aliyun/bootstrap-ecs.sh`
- `deploy/aliyun/deploy.sh`
- `deploy/aliyun/healthcheck.sh`
- `Dockerfile` when missing and container deployment was chosen
- `docker-compose.prod.yml`
- `.env.production.example`
- optional `deploy/aliyun/nginx.conf`
- optional `deploy/aliyun/app.service` for non-Docker systemd deployment

Keep generated files idempotent. Scripts should be safe to rerun and should fail fast with useful error messages.

## Deployment Safety

Before executing `deploy`, show:

- target host and user, with secrets redacted
- release artifact or image tag
- commands that will run locally
- commands that will run remotely
- database migration command
- health check URL
- rollback command

Require explicit user confirmation before SSH, remote writes, service restarts, or migrations.

## Verification

After generating files:

- Validate YAML syntax when a parser is available.
- Run shell syntax checks when available.
- Run the repository's existing tests if the user requested full verification and dependencies are available.
- Report commands run and exact failures.

After deployment:

- Check the process or container status.
- Check application logs.
- Call `/health`, `/api/health`, or the discovered health endpoint.
- Confirm the running image tag, git commit, or release directory.

## Final Response

Report:

- deployment mode chosen and why
- files generated or changed
- GitHub Secrets required
- Aliyun resources the user must prepare
- database schema initialization path
- how to trigger deployment
- rollback command
- verification results