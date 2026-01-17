#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
APP_DIR="/var/www/goat-system"
SYSTEMD_SERVICE="goat-system"

echo "--- Starting deployment ---"
cd "$APP_DIR"

echo "--- Pulling latest changes from git ---"
git fetch --all
git checkout main # Or the branch you want to deploy
git pull

echo "--- Activating virtual environment ---"
source venv/bin/activate

echo "--- Installing/updating dependencies ---"
pip install -r requirements.txt

echo "--- Running database migrations ---"
export FLASK_APP=run.py
flask db upgrade

echo "--- Restarting the application service ---"
sudo systemctl restart "$SYSTEMD_SERVICE"

echo "--- Deployment finished successfully! ---"
