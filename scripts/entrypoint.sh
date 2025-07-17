#!/bin/bash
set -e

echo "Starting CSV Processing API..."

# Function to wait for database
wait_for_db() {
    echo "Waiting for MySQL database..."
    /app/wait-for-it.sh $DB_HOST:$DB_PORT --timeout=60 --strict
    echo "MySQL is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    /app/wait-for-it.sh $REDIS_HOST:$REDIS_PORT --timeout=30 --strict
    echo "Redis is ready!"
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    python manage.py migrate --noinput
    echo "Migrations completed!"
}

# Function to collect static files
collect_static() {
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
    echo "Static files collected!"
}

# Function to create superuser
create_superuser() {
    echo "Creating superuser..."
    python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gmail.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f'Superuser {email} created successfully!')
else:
    print(f'Superuser {email} already exists.')
"
}

# Function to show startup info
show_info() {
    echo ""
    echo "RAVID CSV Processing API is starting..."
    echo "API Documentation: http://localhost:8000/swagger/"
    echo "Admin Panel: http://localhost:8000/admin/"
    echo "Default Admin: admin@ravid.cloud / admin123"
    echo ""
}

# Main execution
main() {
    # Set default environment variables if not provided
    export DB_HOST=${DB_HOST:-db}
    export DB_PORT=${DB_PORT:-3306}
    export REDIS_HOST=${REDIS_HOST:-redis}
    export REDIS_PORT=${REDIS_PORT:-6379}
    
    # Wait for dependencies
    wait_for_db
    wait_for_redis
    
    # Run Django setup
    run_migrations
    collect_static
    create_superuser
    
    # Show startup information
    show_info
    
    # Execute the main command
    exec "$@"
}

# Run main function
main "$@" 