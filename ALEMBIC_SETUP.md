# Alembic Database Migration Setup Guide

## Prerequisites

1. **PostgreSQL Database**: Make sure PostgreSQL is running and you have created a database
2. **Environment Variables**: Ensure your `.env` file is configured with the correct database URL

## Step-by-Step Setup

### 1. Create PostgreSQL Database

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database
CREATE DATABASE fast;

# Create user (if needed)
CREATE USER postgres WITH PASSWORD 'Abhi123';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fast TO postgres;

# Exit psql
\q
```

### 2. Initialize Alembic (Already Done)

The Alembic configuration is already set up in your project. The files are:
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Environment configuration
- `alembic/versions/` - Migration files directory

### 3. Generate Initial Migration

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Generate the first migration
alembic revision --autogenerate -m "Initial migration"
```

### 4. Review the Generated Migration

After running the above command, check the generated file in `alembic/versions/`. It should contain:
- `users` table creation
- `urls` table creation  
- `url_clicks` table creation
- Proper foreign key relationships
- Enum types for UserRole, UserStatus, URLStatus

### 5. Apply Migration to Database

```bash
# Apply all pending migrations
alembic upgrade head
```

### 6. Verify Database Schema

```bash
# Connect to your database
psql -U postgres -d fast

# List tables
\dt

# Describe tables structure
\d users
\d urls
\d url_clicks

# Exit
\q
```

## Common Alembic Commands

### Migration Management
```bash
# Generate new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Show current revision
alembic current

# Show migration history
alembic history --verbose
```

### Database Reset (Development Only)
```bash
# Drop all tables and start fresh
alembic downgrade base
alembic upgrade head
```

## Troubleshooting

### Issue: "Target database is not up to date"
```bash
# Check current revision
alembic current

# Show pending migrations
alembic show head

# Apply missing migrations
alembic upgrade head
```

### Issue: "Can't locate revision identified by"
```bash
# This usually happens when migration files are deleted
# Reset the alembic version table
psql -U postgres -d fast -c "DELETE FROM alembic_version;"

# Mark current state as initial
alembic stamp head
```

### Issue: Import errors in migrations
Make sure all your model files are properly imported in `alembic/env.py`:
```python
from app.models import user, url, analytics  # Import all models
```

## Best Practices

1. **Always review generated migrations** before applying them
2. **Test migrations on a copy** of production data first
3. **Backup database** before applying migrations in production
4. **Use descriptive migration messages**
5. **Don't edit migration files** after they've been applied to production

## Production Deployment

```bash
# Set production database URL
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"

# Apply migrations
alembic upgrade head
```

## Current Database Schema

After running the initial migration, your database will have:

### Tables:
- **users**: User accounts with roles and status
- **urls**: Shortened URLs with analytics
- **url_clicks**: Click tracking data
- **alembic_version**: Migration version tracking

### Enums:
- **userrole**: admin, user
- **userstatus**: active, inactive  
- **urlstatus**: active, inactive
