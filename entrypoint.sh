#!/usr/bin/env bash
set -e

echo "Starting Gunicorn with Flask application"
gunicorn --bind 0.0.0.0:8081 --chdir /home/bundlegenuser/bundlegen/bundlegen/rabbitmq app:app --daemon

bundlegen-rabbitmq -vv start
