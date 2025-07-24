# Alembic Database Migrations

Alembic is now set up and configured for the Reform UK messaging project.

## Configuration

- **Database URL**: Automatically reads from `DATABASE_URL` environment variable (defaults to `sqlite:///./reform_messaging.db`)
- **Models**: Automatically detects changes in `src/models.py`
- **Migration files**: Stored in `alembic/versions/` with timestamp prefixes

## Common Commands

### Check current database version
```bash
uv run alembic current
```

### View migration history
```bash
uv run alembic history --verbose
```

### Create a new migration (auto-generate from model changes)
```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

### Create a manual migration
```bash
uv run alembic revision -m "Description of changes"
```

### Apply migrations (upgrade to latest)
```bash
uv run alembic upgrade head
```

### Apply specific number of migrations
```bash
uv run alembic upgrade +1    # Apply one migration
uv run alembic upgrade ae10  # Apply up to specific revision
```

### Rollback migrations
```bash
uv run alembic downgrade -1     # Rollback one migration
uv run alembic downgrade base   # Rollback all migrations
uv run alembic downgrade ae10   # Rollback to specific revision
```

## Workflow for Schema Changes

1. **Modify models** in `src/models.py`
2. **Generate migration**: `uv run alembic revision --autogenerate -m "Add new column"`
3. **Review the generated migration** in `alembic/versions/`
4. **Apply migration**: `uv run alembic upgrade head`

## Current State

- ✅ Alembic initialized and configured
- ✅ Database schema matches current models
- ✅ Initial migration created and stamped
- ✅ Ready for future schema changes

## Environment Support

The configuration automatically detects your database type:
- **PostgreSQL**: Uses `postgresql+asyncpg://` for async operations
- **SQLite**: Uses `sqlite+aiosqlite://` for async operations
- **Environment Variables**: Reads `DATABASE_URL` from your `.env` file

## Tips

- Always review auto-generated migrations before applying them
- Use descriptive commit messages for migrations
- Test migrations on a copy of production data before applying to production
- Keep migration files in version control 