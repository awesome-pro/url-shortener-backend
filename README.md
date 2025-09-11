# URL Shortener Backend  -- [🔗 Swagger Docs](https://shorturl.abhinandan.pro/docs) -- [🔗 Live Link](https://shortenurl.abhinandan.pro)
## [Frontend GitHub Link 🚀](https://github.com/awesome-pro/url-shortener-frontend)


<img width="400" height="225" alt="Screenshot 2025-09-11 at 8 16 15 AM" src="https://github.com/user-attachments/assets/ba9bbae8-647e-4c3b-9680-2fb75b7a91b3" />
<img  width="400" height="225" alt="Screenshot 2025-09-11 at 8 16 31 AM" src="https://github.com/user-attachments/assets/9ce2dbae-21cc-43a6-b629-bf7e00d3bc0a" />
<img  width="400" height="225" alt="Screenshot 2025-09-11 at 8 04 51 AM" src="https://github.com/user-attachments/assets/bd026335-d351-40e7-b043-7af50d43917e" />
<img  width="400" height="225" alt="Screenshot 2025-09-11 at 8 05 58 AM" src="https://github.com/user-attachments/assets/6d2399ec-f57a-4892-9cb4-7d2f7a7150ef" />
<img  width="400" height="225" alt="Screenshot 2025-09-11 at 8 06 04 AM" src="https://github.com/user-attachments/assets/00a06e62-3895-4517-bb60-ab61887a760e" />
<img  width="400" height="225" alt="Screenshot 2025-09-11 at 8 06 25 AM" src="https://github.com/user-attachments/assets/afc2a4ff-e8e5-4e0c-ae93-66bff022493f" />



A high-performance URL shortener API built with FastAPI, PostgreSQL, and Redis.

## Features

- 🔐 JWT Authentication
- 🔗 URL Shortening with custom codes
- 📊 Real-time Analytics
- ⚡ Redis Caching for fast redirects
- 🗄️ PostgreSQL for reliable data storage
- 📱 RESTful API
- 🚀 Async/await support

## Tech Stack

- **FastAPI** - Modern, fast web framework
- **PostgreSQL** - Reliable relational database
- **Redis** - High-performance caching
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Alembic** - Database migration tool
- **JWT** - Secure authentication
- **Pydantic** - Data validation

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+

### Installation

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   # Create database
   createdb shortener_db
   
   # Run migrations
   alembic upgrade head
   ```

6. **Start Redis** (if not already running)
   ```bash
   redis-server
   ```

7. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Configuration

Edit `.env` file with your settings:

```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/shortener_db

# Redis (Local)
REDIS_URL=redis://localhost:6379/0

# Redis (Upstash - Production)
# REDIS_URL=redis://default:your_password@your_upstash_url:port

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
BASE_URL=http://localhost:8000
DEBUG=True
```

## API Endpoints

### Authentication
- `POST /api/auth/sign-up` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### URL Management
- `POST /api/urls/` - Create short URL
- `GET /api/urls/` - Get user's URLs (paginated)
- `GET /api/urls/{id}` - Get specific URL
- `PUT /api/urls/{id}` - Update URL
- `DELETE /api/urls/{id}` - Delete URL

### Analytics
- `GET /api/urls/{id}/analytics` - Get URL analytics
- `GET /api/urls/{id}/analytics/daily` - Get daily click data
- `GET /api/urls/{id}/analytics/referrers` - Get top referrers
- `GET /api/analytics/dashboard` - Get dashboard stats

### Redirect
- `GET /{short_code}` - Redirect to original URL

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Development

### Running Tests
```bash
pytest
```

### Code Style
```bash
# Format code
black app/

# Check imports
isort app/
```

## Deployment

### Production Checklist

1. **Environment Variables**
   - Set strong `JWT_SECRET_KEY`
   - Configure production database URL
   - Set up Upstash Redis URL
   - Set `DEBUG=False`

2. **Database**
   - Run migrations: `alembic upgrade head`
   - Set up database backups

3. **Redis**
   - Configure Upstash Redis or production Redis instance
   - Set appropriate cache TTL values

4. **Security**
   - Configure CORS origins
   - Set up SSL/TLS
   - Use environment variables for secrets

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Performance Considerations

- **Redis Caching**: URLs are cached for fast redirects
- **Async Operations**: Click tracking is non-blocking
- **Database Indexing**: Optimized queries with proper indexes
- **Connection Pooling**: Efficient database connections

## Architecture

```
├── app/
│   ├── core/           # Configuration, security, dependencies
│   ├── database/       # Database connection and setup
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   ├── routers/        # API routes
│   └── utils/          # Utility functions
├── alembic/            # Database migrations
└── tests/              # Test files
```

## License

MIT License
