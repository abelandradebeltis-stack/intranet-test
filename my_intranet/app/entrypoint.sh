#!/usr/bin/env bash
set -e
# Run migrations then start
if [ -f migrations/env.py ] || [ -d alembic ]; then
  flask db upgrade || true
fi
# create admin user if not exists (script will handle details)
python create_admin.py || true
exec "$@"
