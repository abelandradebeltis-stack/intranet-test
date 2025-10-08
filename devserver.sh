#!/bin/bash
set -e

# Unset DATABASE_URL to force fallback to SQLite
unset DATABASE_URL

export FLASK_APP=my_intranet.app:create_app

# Activate virtual environment
source .venv/bin/activate

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Create admin user
echo "Creating admin user..."
flask create-admin

# Grant full access to admin
echo "Granting full access to admin..."
flask grant-full-access

# Start Flask server
echo "Starting Flask server..."
flask run --host=0.0.0.0 --port=8084
