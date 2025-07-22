#!/usr/bin/env bash
# exit on error
set -o errexit

# Install backend dependencies
pip install -r requirements.txt

# Start the backend server (replace with your actual command)
gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:10000