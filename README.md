# 🚀 CSV Processing API

**Project Assessment for Backend Django Developer**  

## 📋 Overview

A comprehensive API system for CSV file upload, processing, and management with:
- 🔐 **JWT Authentication** (Registration & Login)
- 📤 **CSV File Upload** with validation
- ⚙️ **Background Processing** with Celery (Deduplication, Unique values, Filtering)
- 📊 **Task Status Tracking** with real-time updates
- 🐳 **Full Docker Integration** (Web, Database, Redis, Celery)
- 📖 **Interactive API Documentation** with Swagger UI

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   web    │  │  celery  │  │  redis   │  │  mysql   │ │
│  │ Django   │  │ worker   │  │ broker   │  │    db    │ │
│  │   API    │  │          │  │          │  │          │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼─────────────┼─────────────┼─────────────┼───────┘
        │             │             │             │
        └─────────────┼─────────────┼─────────────┘
                      │             │
                      └─────────────┘
```

### Limitations:
- File size is not restricted—very large CSVs may affect performance.
- Processed files are not automatically deleted; disk usage may grow over time.
- The system assumes all CSVs are UTF-8 and well-formed; unusual encodings may cause errors.
- No quota or cleanup policy is currently implemented.



## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git
- Make (optional, but recommended)

### 1. Clone & Start (3 Commands)

```bash
# Clone the repository
git clone <repository_url>
cd ravid

# Build and start all services
make build && make up

# Alternative without Make:
# docker-compose build && docker-compose up -d
```

### 2. Access the Application

- **🌐 API Documentation**: http://localhost:8000/swagger/
- **🔧 Admin Panel**: http://localhost:8000/admin/
- **👤 Default Admin**: `admin@ravid.cloud` / `admin123`

### 3. Verify Services

```bash
# Check container status
make status

# View logs
make logs

# Health check
make health
```

## 📡 API Endpoints

### Authentication
- `POST /api/register/` - User registration
- `POST /api/login/` - User login (returns JWT tokens)
- `POST /api/token/refresh/` - Refresh JWT token

### CSV Operations
- `POST /api/upload-csv/` - Upload CSV file
- `POST /api/perform-operation/` - Start CSV processing task
- `GET /api/task-status/` - Check task status and get results

## 🐳 Docker Commands

### Using Make (Recommended)
```bash
make help          # Show all available commands
make build          # Build Docker images
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make logs           # View logs
make status         # Check container status
make shell          # Access Django shell
make clean          # Clean up containers and volumes
make backup         # Backup database
make health         # Health check
```

### Using Docker Compose Directly
```bash
# Build and start
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Access Django shell
docker-compose exec web python manage.py shell

# Run migrations manually
docker-compose exec web python manage.py migrate

# Create superuser manually
docker-compose exec web python manage.py createsuperuser
```

## 🔧 Configuration

### Environment Variables
The application uses these environment variables (set in docker-compose.yml):

```env
# Database
DB_HOST=db
DB_PORT=3306
DB_NAME=ravid_db
DB_USER=ravid_user
DB_PASSWORD=ravid_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Django
DEBUG=True
DJANGO_SUPERUSER_EMAIL=admin@ravid.cloud
DJANGO_SUPERUSER_PASSWORD=admin123
```
## 📊 Monitoring & Debugging

### View Service Logs
```bash
# All services
make logs

# Specific services
make dev-logs-web
make dev-logs-celery
make dev-logs-db
make dev-logs-redis
```

### Check Container Health
```bash
# Container status
docker-compose ps

# Health check
make health

# Resource usage
docker stats
```

### Database Access
```bash
# MySQL shell
docker-compose exec db mysql -u ravid_user -pravid_password ravid_db

# Django database shell
docker-compose exec web python manage.py dbshell
```

## 🛠️ Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :3306
sudo lsof -i :6379

# Kill processes or change ports in docker-compose.yml
```

**2. Database Connection Issues**
```bash
# Check MySQL container logs
docker-compose logs db

# Restart database service
docker-compose restart db
```

**3. Celery Worker Not Processing**
```bash
# Check Celery logs
docker-compose logs celery

# Restart Celery worker
docker-compose restart celery
```

**4. Permission Denied Errors**
```bash
# Fix script permissions
chmod +x scripts/entrypoint.sh scripts/wait-for-it.sh

# Rebuild containers
make clean && make build && make up
```

**5. File Upload Issues**
```bash
# Check media directory permissions
docker-compose exec web ls -la /app/media/

# Create directories if missing
docker-compose exec web mkdir -p /app/media/csv_files /app/media/processed_csv
```

### Reset Everything
```bash
# Complete reset (WARNING: This will delete all data)
make clean
docker volume prune -f
make build && make up
```

## 📈 Development

### Adding New Features
1. Edit code locally
2. Rebuild container: `make build`
3. Restart services: `make restart`

### Database Migrations
```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

## 📝 Project Structure

```
ravid/
├── docker-compose.yml          # Multi-service Docker configuration
├── Dockerfile                  # Django application image
├── Makefile                   # Convenient command shortcuts
├── requirements.txt           # Python dependencies
├── .dockerignore             # Docker build exclusions
├── scripts/
│   ├── entrypoint.sh         # Container startup script
│   ├── wait-for-it.sh        # Service dependency management
│   └── init_db.sql          # Database initialization
├── ravid_project/            # Django project settings
├── csv_app/                  # Main application
│   ├── models.py            # Database models
│   ├── serializers.py       # API serializers
│   ├── views.py             # API endpoints
│   ├── urls.py              # URL routing
│   └── admin.py             # Admin interface
└── README.md                # This file
```

**🎉 Thank you for reviewing the CSV Processing API!**