---
name: backend-patterns
description: Backend architecture patterns and constraints for FastAPI, Pydantic v2, SQLAlchemy 2.x, and Alembic applications, covering service/repository boundaries, transactions, validation, database access, migrations, jobs, caching, logging, and production safety.
metadata:
  origin: ECC
---

# Backend Development Patterns

Backend architecture patterns for Python services built with FastAPI, Pydantic,
SQLAlchemy, and Alembic. Use this skill for module boundaries, persistence
contracts, transaction ownership, backend constraints, and production-facing
server-side decisions.

For route-level FastAPI syntax, dependency aliases, and endpoint tests, combine
this with `fastapi-patterns`. For migration safety details, combine it with
`database-migrations`.

## When to Activate

- Designing backend module boundaries across router, schema, service,
  repository, model, and migration files
- Implementing SQLAlchemy repositories or service-layer database workflows
- Reviewing transaction boundaries, commits, rollbacks, and session ownership
- Adding or changing database-backed FastAPI features
- Designing Pydantic request, update, response, and internal DTO models
- Optimizing database access, pagination, N+1 queries, indexes, and eager loads
- Adding caching, background jobs, outbox-style workflows, or scheduled tasks
- Standardizing backend error mapping, logging, auth checks, and observability

## Stack Constraints

- Use FastAPI for HTTP routing and dependency injection.
- Use Pydantic v2 for request validation, response schemas, settings, and typed
  DTOs.
- Use SQLAlchemy 2.x style ORM and Core APIs. Prefer `select()` and typed ORM
  mappings over legacy `session.query()`.
- Keep the database style consistent. Use `AsyncSession` with async routes by
  default; if the project uses synchronous SQLAlchemy, keep DB-touching route
  handlers as `def` or isolate blocking work so sync DB calls do not block the
  event loop.
- Use Alembic for schema evolution. Do not rely on `Base.metadata.create_all()`
  in production startup paths.
- Keep SQLAlchemy ORM models as persistence models. Do not expose them directly
  as public response contracts unless a response model controls serialization.
- Keep transactions in the service layer or a dedicated unit-of-work boundary.
  Routers should not scatter commits across business logic.
- Catch structural database errors close to the transaction boundary and map
  them to domain/application errors before converting to HTTP errors.
- Treat migration files as immutable once deployed. Create a new migration for
  follow-up fixes.

## Recommended Project Shape

```text
app/
|-- main.py
|-- config.py
|-- db/
|   |-- base.py
|   |-- session.py
|   `-- migrations/              # Alembic environment or migration package
|-- models/
|   `-- user.py                  # SQLAlchemy ORM mappings
|-- schemas/
|   `-- user.py                  # Pydantic request/response schemas
|-- repositories/
|   `-- user_repository.py       # SQLAlchemy query composition
|-- services/
|   `-- user_service.py          # Business logic + transaction ownership
|-- routers/
|   `-- users.py                 # HTTP boundary only
`-- errors.py                    # Domain errors + HTTP mapping helpers
alembic.ini
alembic/
`-- versions/
```

Keep this structure flexible. Small projects can merge repository logic into a
service, but avoid putting database transaction logic and business rules inside
route handlers.

## Layering Rules

### Router Layer

Routers should parse HTTP inputs, call services, and translate application
errors to HTTP responses.

```python
# app/routers/users.py
from fastapi import APIRouter, HTTPException, status

from app.dependencies import DbDep
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import DuplicateUserEmail, UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DbDep) -> UserRead:
    try:
        return await UserService(db).create_user(payload)
    except DuplicateUserEmail as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        ) from exc
```

Avoid route handlers that manually create ORM objects, commit transactions, send
emails, enqueue jobs, and shape responses in one function.

### Pydantic Schema Layer

Use separate schemas for create, update, read, and internal operations. Use
`model_dump(exclude_unset=True)` for patch-like updates.

```python
# app/schemas/user.py
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

### SQLAlchemy Model Layer

Use database constraints for uniqueness and integrity. Application pre-checks
can improve messages, but they cannot replace database constraints under
concurrency.

```python
# app/models/user.py
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
```

### Repository Layer

Repositories compose queries and hide SQLAlchemy details from business services.
They should not own commits unless the whole project intentionally uses that
pattern.

```python
# app/repositories/user_repository.py
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_active(self, *, offset: int, limit: int) -> tuple[list[User], int]:
        base_query: Select[tuple[User]] = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.id)
        )
        total_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        rows_result = await self.db.execute(base_query.offset(offset).limit(limit))
        return list(rows_result.scalars()), total_result.scalar_one()

    def add(self, user: User) -> None:
        self.db.add(user)
```

### Service Layer

Services own business rules and transaction boundaries. Prefer one commit per
use case. Roll back when database errors occur.

```python
# app/services/user_service.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.security.passwords import hash_password


class DuplicateUserEmail(Exception):
    """Raised when a user email conflicts with an existing row."""


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def create_user(self, payload: UserCreate) -> User:
        user = User(
            email=str(payload.email),
            display_name=payload.display_name,
            hashed_password=hash_password(payload.password),
        )
        self.users.add(user)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateUserEmail from exc
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, payload: UserUpdate) -> User | None:
        user = await self.users.get_by_id(user_id)
        if user is None:
            return None

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user
```

## Database Session Pattern

Use one session per request for ordinary API requests. The dependency should
close the session and roll back uncommitted work on exceptions. The examples
below use async SQLAlchemy; use the same ownership rules for a synchronous
`Session` if the project is intentionally sync.

```python
# app/db/session.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

For background jobs, CLI scripts, and scheduled tasks, create their own session
scope explicitly. Do not reuse a request-scoped session outside the request.

If a project uses synchronous SQLAlchemy, keep that choice explicit:

```python
# app/db/session.py
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
```

## Alembic Migration Contract

Every SQLAlchemy model change that affects schema must include an Alembic
migration in the same feature change.

```python
# alembic/versions/20260626_1200_add_users.py
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260626_1200"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
```

For large production tables, do not blindly trust autogenerated migrations.
Review lock behavior, defaults, nullability, index creation, and backfill
strategy with `database-migrations`.

## Query and Performance Patterns

### Select Only What You Need

```python
from sqlalchemy import select

stmt = (
    select(User.id, User.email, User.display_name)
    .where(User.is_active.is_(True))
    .order_by(User.id)
    .limit(50)
)
rows = (await db.execute(stmt)).all()
```

### Avoid N+1 Queries

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

stmt = (
    select(User)
    .options(selectinload(User.orders))
    .where(User.is_active.is_(True))
    .order_by(User.id)
)
users = list((await db.execute(stmt)).scalars())
```

Use `selectinload` for collections and `joinedload` only when row multiplication
is understood and acceptable.

### Stable Pagination

```python
stmt = select(User).order_by(User.id).offset(offset).limit(limit)
```

Offset pagination must have deterministic ordering. For large tables or
infinite scroll, prefer cursor/keyset pagination over deep offsets.

## Error Handling

Separate domain/application errors from HTTP errors. Services raise application
errors; routers map them to status codes and response details.

```python
# app/errors.py
from fastapi import HTTPException, status


class AppError(Exception):
    message = "Application error"


class ResourceNotFound(AppError):
    message = "Resource not found"


class PermissionDenied(AppError):
    message = "Permission denied"


def to_http_error(exc: AppError) -> HTTPException:
    if isinstance(exc, ResourceNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDenied):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
```

Do not leak raw database exception messages or stack traces in public API
responses.

## Caching

Use cache-aside for read-heavy data with clear invalidation rules. Cache keys
must include tenant/user scope when data is not globally public.

```python
import json

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead


async def get_user_read_model(
    user_id: int,
    repo: UserRepository,
    redis,
) -> UserRead | None:
    cache_key = f"user:{user_id}:read"
    cached = await redis.get(cache_key)
    if cached is not None:
        return UserRead.model_validate_json(cached)

    user = await repo.get_by_id(user_id)
    if user is None:
        return None

    payload = UserRead.model_validate(user).model_dump(mode="json")
    await redis.set(cache_key, json.dumps(payload), ex=300)
    return UserRead.model_validate(payload)
```

Invalidate or update cache entries inside the same use case that mutates the
underlying data. For multi-step workflows, prefer conservative invalidation over
serving stale user-specific data.

## Background Jobs

FastAPI `BackgroundTasks` is suitable for small post-response work in the same
process. Use a durable queue for work that must survive process restarts,
requires retries, or runs longer than a short request tail.

```python
from fastapi import BackgroundTasks


@router.post("/{user_id}/welcome-email", status_code=202)
async def send_welcome_email(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: DbDep,
) -> dict[str, str]:
    user = await UserService(db).get_required_user(user_id)
    background_tasks.add_task(send_email, user.email, "Welcome")
    return {"status": "queued"}
```

For durable jobs, pass identifiers to the queue, not ORM instances or live
database sessions.

## Logging and Observability

Prefer structured logs with request identifiers and business context. Avoid
logging secrets, tokens, raw passwords, or full PII payloads.

```python
import logging
from uuid import uuid4

from fastapi import Request

logger = logging.getLogger(__name__)


@app.middleware("http")
async def request_context_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )
    return response
```

## Security and Authorization

- Perform authentication in dependencies and authorization close to the use case
  being protected.
- Use `401` for missing/invalid authentication and `403` for authenticated users
  without permission.
- Never trust `user_id`, `tenant_id`, role, or permission fields from request
  bodies when they can be derived from the authenticated principal.
- Use server-side ownership checks before reads and writes.
- Validate all external callback/webhook payloads and signatures before
  mutating database state.

## Anti-Patterns

```python
# Bad: production startup mutates schemas implicitly.
@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# Good: production schemas are managed by Alembic migrations.
@asynccontextmanager
async def lifespan(app):
    yield
    await engine.dispose()
```

```python
# Bad: business logic, persistence, and HTTP errors tangled in a route.
@router.post("/users")
async def create_user(payload: UserCreate, db: DbDep):
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    await db.commit()
    return user


# Good: thin route, service-owned transaction, explicit response contract.
@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, db: DbDep):
    return await UserService(db).create_user(payload)
```

```python
# Bad: deep offset with no stable ordering.
stmt = select(User).offset(50000).limit(50)


# Good: deterministic order; use keyset pagination for large scans.
stmt = select(User).where(User.id > last_seen_id).order_by(User.id).limit(50)
```

## Review Checklist

- [ ] Router is thin and uses typed request/response models.
- [ ] Service layer owns business rules and transaction boundaries.
- [ ] Repository/query code uses SQLAlchemy 2.x `select()` style.
- [ ] Mutations catch `IntegrityError` or relevant database errors and roll back.
- [ ] ORM model constraints match business invariants.
- [ ] Every schema-changing model edit has an Alembic migration.
- [ ] Migrations have reviewed upgrade/downgrade behavior.
- [ ] Paginated queries have deterministic ordering.
- [ ] Relationship loading avoids obvious N+1 query patterns.
- [ ] Response models prevent leaking internal fields such as password hashes.
- [ ] Background jobs do not carry request sessions or ORM objects across
  process boundaries.
- [ ] Logs include useful context but exclude secrets and sensitive payloads.

**Remember**: This skill defines backend architecture constraints for the
FastAPI/Pydantic/SQLAlchemy/Alembic stack. Keep HTTP handlers thin, database
constraints real, migrations explicit, and transaction ownership easy to trace.
