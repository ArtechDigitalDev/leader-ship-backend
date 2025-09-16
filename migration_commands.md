# Alembic Migration Commands

This document provides common Alembic commands for database migrations in the FastAPI project.

## 🚀 Quick Start

### 1. Initialize Alembic (Already Done)
```bash
alembic init alembic
```

### 2. Check Current Migration Status
```bash
alembic current
```

### 3. View Migration History
```bash
alembic history
```

## 📝 Creating Migrations

### Auto-generate Migration from Model Changes
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create Empty Migration
```bash
alembic revision -m "Description of changes"
```

## 🔄 Applying Migrations

### Apply All Pending Migrations
```bash
alembic upgrade head
```

### Apply Specific Migration
```bash
alembic upgrade <revision_id>
```

### Apply One Migration Forward
```bash
alembic upgrade +1
```

### Apply Multiple Migrations Forward
```bash
alembic upgrade +3
```

## ↩️ Rolling Back Migrations

### Rollback to Previous Migration
```bash
alembic downgrade -1
```

### Rollback to Specific Migration
```bash
alembic downgrade <revision_id>
```

### Rollback to Base (Remove All Migrations)
```bash
alembic downgrade base
```

## 📊 Migration Information

### Show Migration History
```bash
alembic history --verbose
```

### Show Current Migration
```bash
alembic current
```

### Show Migration Details
```bash
alembic show <revision_id>
```

### Show Migration Tree
```bash
alembic heads
```

## 🛠️ Development Workflow

### 1. Make Changes to Models
Edit your SQLAlchemy models in `app/models/`

### 2. Generate Migration
```bash
alembic revision --autogenerate -m "Add new field to users table"
```

### 3. Review Generated Migration
Check the generated file in `alembic/versions/`

### 4. Apply Migration
```bash
alembic upgrade head
```

### 5. Test Your Changes
Run your application and test the new functionality

## 🔧 Configuration

### Database URL
The database URL is configured in `alembic.ini`:
```ini
sqlalchemy.url = postgresql://postgres:password@localhost:5432/fastapi_db
```

### Environment Configuration
Alembic uses the same environment variables as your FastAPI app:
- `DATABASE_URL` from `.env` file
- Database connection from `app.core.database`

## 📁 Project Structure

```
alembic/
├── versions/           # Migration files
│   ├── 904085ea8a01_initial_migration.py
│   └── c56ddd6ca9c1_add_terms_accepted_field_to_users_table.py
├── env.py             # Alembic environment configuration
├── README             # Alembic documentation
└── script.py.mako     # Migration template
alembic.ini           # Alembic configuration
```

## ⚠️ Important Notes

1. **Always Review Auto-generated Migrations**: Check the generated migration files before applying them
2. **Backup Database**: Always backup your database before applying migrations in production
3. **Test Migrations**: Test migrations in a development environment first
4. **Version Control**: Commit migration files to version control
5. **Team Coordination**: Coordinate with team members when applying migrations

## 🐛 Troubleshooting

### Migration Conflicts
If you encounter conflicts:
1. Check the migration history: `alembic history`
2. Identify conflicting migrations
3. Resolve conflicts manually in the migration files
4. Test the resolution

### Database Connection Issues
1. Verify database is running
2. Check connection string in `alembic.ini`
3. Ensure database user has proper permissions

### Model Import Issues
1. Check that all models are imported in `alembic/env.py`
2. Verify the import path is correct
3. Ensure all dependencies are installed

## 📚 Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
