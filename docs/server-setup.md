# Server Setup and Deployment Guide

This guide provides step-by-step instructions for deploying the application on a Linux server.

## 1. Prerequisites

Ensure your server has the following software installed:

-   `git`
-   `python3`
-   `python3-venv`

You can install them on a Debian-based system (like Ubuntu) using:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv
```

## 2. Initial Server Setup

This script automates the initial cloning, environment creation, and dependency installation.

```bash
#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# The directory where the application will be installed.
APP_DIR="/var/www/goat-system"
# The git repository URL.
GIT_URL="https://github.com/alexzhelyapov1/goat-system.git" # <-- CHANGE THIS
# The user that will run the application.
APP_USER="www-data" # Or another dedicated user

# --- Setup ---
echo "--- Cloning repository ---"
git clone "$GIT_URL" "$APP_DIR"
cd "$APP_DIR"

echo "--- Creating Python virtual environment ---"
python3 -m venv venv

echo "--- Activating virtual environment ---"
source venv/bin/activate

echo "--- Installing dependencies ---"
# This list is based on project analysis. A requirements.txt file is recommended.
# pip install flask flask-login flask-migrate flask-sqlalchemy pydantic alembic gunicorn python-dotenv APScheduler
pip install -r requirements.txt

echo "--- Creating .env file for configuration ---"
# Generate a strong, random secret key
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
cat > .env << EOF
# This file contains environment-specific configuration.
# It should NOT be committed to git.

# A strong, random key for signing session cookies.
SECRET_KEY=${SECRET_KEY}

# The database connection URL. Defaults to a local SQLite database.
# For production, you could switch to PostgreSQL or MySQL, e.g.:
# DATABASE_URL="postgresql://user:password@localhost/dbname"
DATABASE_URL="sqlite:///app.db"
EOF

echo "--- Initializing the database ---"
# The FLASK_APP environment variable tells Flask where to find the application instance.
export FLASK_APP=run.py
flask db upgrade

echo "--- Setting ownership ---"
# Change ownership of the directory to the application user
sudo chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
# sudo chown -R www-data:www-data /var/www/goat-system

echo "--- Setup complete! ---"
echo "To run the application, activate the venv ('source venv/bin/activate') and run Gunicorn."
echo "Example Gunicorn command: gunicorn --workers 3 --bind 0.0.0.0:5000 run:app"

```

### How to Use

1.  Save the script above as `setup_server.sh`.
2.  **Important:** Change the `GIT_URL` variable in the script to your repository's URL.
3.  Make the script executable: `chmod +x setup_server.sh`.
4.  Run the script: `sudo ./setup_server.sh`. The `sudo` is used for the final `chown` command.

## 3. Running as a Systemd Service (Recommended)

To ensure the application runs automatically and restarts on failure, run it as a systemd service.

1.  Create a service file:

    ```bash
    sudo vim /etc/systemd/system/goat-system.service
    ```

2.  Add the following content. Be sure to adjust `User` and paths if you changed them in the setup script.

    ```ini
    [Unit]
    Description=Gunicorn instance to serve goat-system
    After=network.target

    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory=/var/www/goat-system
    Environment="PATH=/var/www/goat-system/venv/bin"
    ExecStart=/var/www/goat-system/venv/bin/gunicorn --workers 1 --bind unix:goat-system.sock -m 007 run:app

    [Install]
    WantedBy=multi-user.target
    ```

3.  Start and enable the service:

    ```bash
    sudo systemctl start goat-system
    sudo systemctl enable goat-system
    ```

## 4. Setting up a Reverse Proxy (Nginx)

You will need a web server like Nginx to act as a reverse proxy, directing traffic to Gunicorn.

1.  Install Nginx: `sudo apt-get install nginx`
2.  Create an Nginx configuration file:

    ```bash
    sudo vim /etc/nginx/sites-available/goat-system
    ```

3.  Add this configuration, replacing `your_domain.com`:

    ```nginx
    server {
        listen 80;
        server_name _;

        location / {
            include proxy_params;
            proxy_pass http://unix:/var/www/goat-system/goat-system.sock;
        }
    }
    ```

4.  Enable the site:

    ```bash
    sudo ln -s /etc/nginx/sites-available/goat-system /etc/nginx/sites-enabled
    sudo systemctl restart nginx
    sudo ufw allow 5000
    ```
