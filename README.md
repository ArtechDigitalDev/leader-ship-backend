# Leader Assessment API

A FastAPI backend for the ROI Leadership Journey: 5Cs Assessment, featuring a modern, scalable architecture with PostgreSQL and Alembic migrations.

## 🏗️ Project Structure

```
your_project/
├── alembic/                      # Alembic's directory for migrations
│   ├── versions/
│   └── env.py
│
├── app/                          # The main application package
│   ├── __init__.py
│   ├── api/                      # API layer (routers/endpoints)
│   │   ├── __init__.py
│   │   ├── deps.py               # FastAPI dependencies
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── users.py          # Endpoints for /users
│   │       ├── assessments.py    # Endpoints for /assessments
│   │       ├── items.py          # Endpoints for /items
│   │       └── auth.py           # Authentication endpoints
│   │
│   ├── core/                     # Core application logic and config
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic settings management
│   │   ├── database.py           # SQLAlchemy engine and Base
│   │   └── security.py           # Security utilities
│   │
│   ├── models/                   # Data Access Layer (SQLAlchemy models)
│   │   ├── __init__.py           # All models imported here for Alembic
│   │   ├── user.py
│   │   ├── assessment.py
│   │   └── item.py
│   │
│   ├── schemas/                  # Pydantic schemas (data validation)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── assessment.py
│   │   ├── item.py
│   │   └── token.py
│   │
│   ├── services/                 # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── assessment_service.py
│   │   └── item_service.py
│   │
│   └── main.py                   # Main FastAPI app entry point
│
├── tests/                        # Directory for tests
├── .env                          # Environment variables
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Project dependencies and metadata
└── docker-compose.yml            # Docker services
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd leader-assessment-api
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   # or for development
   pip install -e ".[dev]"
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Set up PostgreSQL**
   
   **Option A: Using Docker (Recommended)**
   ```bash
   docker-compose up -d postgres
   ```
   
   **Option B: Local PostgreSQL**
   ```bash
   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE leader_db;
   CREATE USER leadership WITH PASSWORD 'lead123';
   GRANT ALL PRIVILEGES ON DATABASE leader_db TO leadership;
   \q
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🧪 Testing

### Database Setup Test
```bash
python test_db_setup.py
```

### Run Tests
```bash
pytest
```

## 📊 5Cs Assessment API

The application includes specialized endpoints for the ROI Leadership Journey: 5Cs Assessment:

### Endpoints

- `GET /api/v1/assessments/5cs/questions` - Get assessment questions
- `POST /api/v1/assessments/5cs/submit` - Submit assessment responses
- `GET /api/v1/assessments/5cs/results/{user_id}` - Get user results

### Features

- **25 Questions**: 5 questions per category (Clarity, Consistency, Connection, Courage, Curiosity)
- **Likert Scale**: 1-5 rating system
- **Personalized Results**: Growth Focus and Intentional Advantage analysis
- **Recommendations**: Actionable insights based on scores

## 🔧 Development

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Adding New Features

1. **Models**: Add to `app/models/` and import in `app/models/__init__.py`
2. **Schemas**: Add to `app/schemas/`
3. **Services**: Add to `app/services/`
4. **Routers**: Add to `app/api/routers/`
5. **Update main.py**: Include new routers

## 🐳 Docker

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production
```bash
# Build image
docker build -t leader-assessment-api .

# Run container
docker run -p 8000:8000 leader-assessment-api
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://leadership:lead123@localhost:5432/leader_db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `DEBUG` | Debug mode | `true` |
| `ENVIRONMENT` | Environment name | `development` |

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS middleware
- Trusted host middleware
- Environment variable validation

## 📈 Performance

- Connection pooling
- Async database operations
- Efficient query patterns
- PostgreSQL optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the troubleshooting section in the documentation
