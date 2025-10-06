#!/bin/sh
source .venv/bin/activate
if [ -z "$PORT" ]; then
  python -u -m flask --app my-intranet/app/app run --debug
else
  python -u -m flask --app my-intranet/app/app run -p $PORT --debug
fi