#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Navigating to the project directory..."
# Assumes the project is in a directory named 'goat-system' in the user's home folder.
# If your path is different, please update it here.
APP_DIR="/var/www/goat-system"
cd "$APP_DIR"

echo "Pulling latest changes from the main branch..."
git pull origin main

echo "Building and restarting Docker containers in detached mode..."
# Using `docker compose` is the modern syntax for `docker-compose`.
# The `--build` flag rebuilds the image if the Dockerfile or context has changed.
# The `-d` flag runs the services in the background. Docker Compose ensures that containers
# are only swapped once the new ones are healthy, providing near-zero downtime.
docker compose up --build -d

echo "Cleaning up old, unused Docker images to save disk space..."
# The -f flag forces the removal without prompting for confirmation.
docker image prune -f

echo "✅ Deployment successful!"
