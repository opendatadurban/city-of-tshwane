# OCL FastAPI Template

## Technology Stack

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) 
    - 🧰 [SQLAlchemy V2](https://docs.sqlalchemy.org/en/20/) for the Python SQL database interactions (ORM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
    - 🔐 JWT Authentication - JSON Web Token based authentication
- 🐋 [Docker Compose](https://www.docker.com) for development and container builds
- ✅ Tests with [Pytest](https://pytest.org).
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

## ✨ Features

- User authentication with JWT tokens
- Role-based access control (superuser and regular users)
- Full CRUD operations for users and items
- Secure password hashing
- Email uniqueness validation
- Self-service user management
- Administrative user management
- Item ownership and permissions
- Async database operations
- Input validation and error handling

## Configure

You can then update configs in the `.env` files to customize your configurations.

Before deploying it, make sure you change at least the values for:

- `POSTGRES_PASSWORD`

You can (and should) pass these as environment variables from secrets

## 🐋 Running with Docker
If requirements change build a new base image

``` 
docker buildx build -f Dockerfile -t ocl_base_image:latest .
```
Todo: Use poetry implementation?

Start the stack with Docker Compose:
```shell
./scripts/dev-local.sh
```

To seed data into the db. (Make sure to change the `SEED_FILE` variable in your .env)
```
docker exec -it <container_name> python app/seed_db.py
```

This will:
- Build the API container
- Start PostgreSQL
- Set up the database
- Start the FastAPI server

## 🧪 Testing

### Running Tests

Execute the test suite:
```shell
./scripts/test-local.sh
```

This will:
- Set up a test database
- Run the pytest suite

### Test Coverage

The project includes:
- Unit tests for CRUD operations
- Integration tests for API endpoints
- Fixture-based test setup
- Transaction rollback for test isolation
- Async test support

## 📚 API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`


## 📁 Project Structure
```shell
.
├── Dockerfile           # Main Dockerfile for the application
├── Dockerfile.base      # Base Dockerfile for common dependencies
├── README.md           # Project documentation
├── compose.yaml        # Docker Compose configuration
├── development.md      # Development guidelines and setup
├── requirements-dev.txt # Development dependencies
├── requirements.txt    # Production dependencies
├── scripts/           # Utility scripts
│   ├── create_alembic_revision.sh  # Database migration script
│   ├── dev-local.sh               # Local development startup
│   └── test-local.sh             # Test execution script
└── src/               # Source code root
    ├── alembic.ini    # Alembic configuration
    └── app/           # Main application package
        ├── alembic/   # Database migrations
        │   ├── README
        │   ├── env.py
        │   ├── script.py.mako
        │   └── versions/
        ├── api/       # API layer
        │   ├── deps.py           # FastAPI dependencies
        │   ├── main.py          # API configuration
        │   └── routes/         # API endpoints
        │       ├── items.py    # Item endpoints
        │       ├── login.py    # Authentication endpoints
        │       ├── users.py    # User endpoints
        │       └── utils.py    # Route utilities
        ├── core/      # Core functionality
        │   ├── config.py      # Application configuration
        │   ├── db.py         # Database connection
        │   └── security.py   # Security utilities
        ├── crud/      # Database operations
        │   ├── base.py      # Base CRUD operations
        │   ├── items.py     # Item CRUD operations
        │   └── users.py     # User CRUD operations
        ├── main.py    # Application entry point
        ├── models/    # Data models
        │   ├── api/         # API models (Pydantic)
        │   │   ├── generic.py
        │   │   ├── items.py
        │   │   └── users.py
        │   └── db/          # Database models (SQLAlchemy)
        │       ├── base.py
        │       ├── items.py
        │       └── users.py
        ├── pytest.ini  # Pytest configuration
        ├── tests/      # Test suite
        │   ├── api/          # API tests
        │   │   └── routes/
        │   │       ├── test_items.py
        │   │       ├── test_login.py
        │   │       └── test_users.py
        │   ├── conftest.py   # Test fixtures
        │   ├── crud/         # CRUD tests
        │   │   ├── test_item.py
        │   │   └── test_user.py
        │   └── utils/        # Test utilities
        │       ├── item.py
        │       ├── user.py
        │       └── utils.py
        └── utils.py    # General utilities
```