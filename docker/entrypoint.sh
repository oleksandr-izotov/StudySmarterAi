#!/bin/bash
set -e

echo "=== Study Smart Entrypoint ==="
echo "Command: $@"

# Default command if none provided
if [ $# -eq 0 ]; then
    echo "No command provided, using default Gunicorn..."
    set -- gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --threads 2 \
        --worker-class gthread \
        --worker-tmp-dir /dev/shm \
        --access-logfile - \
        --error-logfile - \
        --capture-output \
        --enable-stdio-inheritance
fi

# Only run initialization steps if we are starting the web server (gunicorn)
# accessing $1 safely
if [[ "$1" == *"gunicorn"* ]]; then
    echo "Starting Web Server - Running Initialization..."

    # Wait for database to be ready
    echo "Waiting for database..."
    while ! python -c "
import socket
import os
host = os.environ.get('DATABASE_HOST', 'db')
port = int(os.environ.get('DATABASE_PORT', 5432))
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((host, port))
sock.close()
exit(0 if result == 0 else 1)
" 2>/dev/null; do
        echo "Database is unavailable - sleeping..."
        sleep 2
    done
    echo "Database is ready!"

    # Run migrations
    echo "Running migrations..."
    python manage.py migrate --noinput

    # Collect static files
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear

    # Compile locale messages
    echo "Compiling translations..."
    python manage.py compilemessages || echo "No messages to compile"

    # Initialize subscription plans
    echo "Initializing subscription plans..."
    python manage.py init_plans || echo "Plans already initialized"
else
    echo "Starting Auxiliary Service ($1) - Skipping Initialization..."
fi

echo "=== Executing Command ==="
exec "$@"
