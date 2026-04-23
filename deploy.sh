#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- Starting EC2 Setup for FastAPI Template ---"

# 1. Update System and Install Prerequisites
echo "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# 2. Install Docker
echo "Installing Docker..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker and enable it on boot
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (requires logout to take effect, 
# but we use 'sudo' for the final command in this script to be safe)
sudo usermod -aG docker $USER

# 3. Gather Git Credentials
echo "--- Repository Configuration ---"
read -p "Is the repository private? (y/n) [n]: " IS_PRIVATE
IS_PRIVATE=${IS_PRIVATE:-n}

read -p "Enter Repository URL (e.g., github.com/org/repo): " REPO_URL
read -p "Enter branch name [dev]: " BRANCH_NAME
BRANCH_NAME=${BRANCH_NAME:-dev}

if [[ "$IS_PRIVATE" =~ ^[Yy]$ ]]; then
    # Private Logic: Requires Username and PAT
    read -p "Enter GitHub Username: " GITHUB_USER
    read -p "Enter GitHub Personal Access Token (PAT): " GITHUB_PAT
    
    echo "Cloning private repository (branch: $BRANCH_NAME)..."
    git clone -b "$BRANCH_NAME" --single-branch "https://${GITHUB_USER}:${GITHUB_PAT}@${REPO_URL}" app_code
else
    # Public Logic: No credentials needed
    echo "Cloning public repository (branch: $BRANCH_NAME)..."
    # Ensure URL has https:// if the user didn't type it
    if [[ ! $REPO_URL =~ ^http ]]; then
        REPO_URL="https://$REPO_URL"
    fi
    git clone -b "$BRANCH_NAME" --single-branch "$REPO_URL" app_code
fi

cd app_code

# # 3. Gather Git Credentials
# echo "--- Repository Configuration ---"
# read -p "Enter GitHub Username: " GITHUB_USER
# read -p "Enter GitHub Personal Access Token (PAT): " GITHUB_PAT
# read -p "Enter Repository URL (e.g., github.com/org/repo): " REPO_URL

# # Clone the repository
# # Using the format: https://username:token@github.com/user/repo
# echo "Cloning repository..."
# # git clone "https://${GITHUB_USER}:${GITHUB_PAT}@${REPO_URL}" app_code
# # New version (clones the 'dev' branch specifically)
# git clone -b dev --single-branch "https://${GITHUB_USER}:${GITHUB_PAT}@${REPO_URL}" app_code
# cd app_code

# 4. Interactive .env Creation
echo "--- Environment Variable Configuration ---"
echo "Please provide values for your .env file:"

read -p "Environment (local, staging, production) [local]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-local}

read -p "Project Name [Open Cities Lab FastAPI Template]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-"Open Cities Lab FastAPI Template"}

read -p "Stack Name [City of Tshwane APIs]: " STACK_NAME
STACK_NAME=${STACK_NAME:-"City of Tshwane APIs"}

read -p "Backend CORS Origins [http://localhost,https://localhost]: " BACKEND_CORS_ORIGINS
BACKEND_CORS_ORIGINS=${BACKEND_CORS_ORIGINS:-"http://localhost,https://localhost"}

read -p "Secret Key (for JWT/Security): " SECRET_KEY
read -p "Superuser Email [admin@example.com]: " FIRST_SUPERUSER
FIRST_SUPERUSER=${FIRST_SUPERUSER:-admin@example.com}

read -p "Superuser Password: " FIRST_SUPERUSER_PASSWORD

read -p "Postgres Server [db-dev]: " POSTGRES_SERVER
POSTGRES_SERVER=${POSTGRES_SERVER:-db-dev}

read -p "Postgres Port [5432]: " POSTGRES_PORT
POSTGRES_PORT=${POSTGRES_PORT:-5432}

read -p "Postgres DB Name [app]: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-app}

read -p "Postgres User [postgres]: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-postgres}

read -p "Postgres Password: " POSTGRES_PASSWORD

read -p "Seed SQL file name (e.g., init.sql): " SEED_FILE
read -p "SMTP User (Email sender address): " SMTP_USER
read -p "SMTP Host [somehost.com]: " SMTP_HOST
SMTP_HOST=${SMTP_HOST:-somehost.com}

read -p "SMTP Password: " SMTP_PASSWORD
read -p "SMTP Port [587]: " SMTP_PORT
SMTP_PORT=${SMTP_PORT:-587}

read -p "Use SMTP TLS? (True/False) [True]: " SMTP_TLS
SMTP_TLS=${SMTP_TLS:-True}

read -p "Default Sender Name: " SMTP_DEFAULT_SENDER

read -p "Log Level (INFO, DEBUG, ERROR) [ERROR]: " LOG_LEVEL
LOG_LEVEL=${LOG_LEVEL:-ERROR}

read -p "OCPO Base URL [http://<ss-address>:8080/r1/<service-id>/<backend-path>]: " OCPO_BASE_URL
OCPO_BASE_URL=${OCPO_BASE_URL:-'http://host.docker.internal:8000/api/v1'}

read -p "X-Road Client Name: " XROAD_CLIENT
read -p "X-Road Service Name: " XROAD_SERVICE
read -p "Poetry Version [1.8.3]: " POETRY_VERSION
POETRY_VERSION=${POETRY_VERSION:-1.8.3}

# Writing to .env
cat <<EOF > .env
ENVIRONMENT=$ENVIRONMENT
PROJECT_NAME="$PROJECT_NAME"
STACK_NAME="$STACK_NAME"
BACKEND_CORS_ORIGINS="$BACKEND_CORS_ORIGINS"
SECRET_KEY=$SECRET_KEY
FIRST_SUPERUSER=$FIRST_SUPERUSER
FIRST_SUPERUSER_PASSWORD=$FIRST_SUPERUSER_PASSWORD
POSTGRES_SERVER=$POSTGRES_SERVER
POSTGRES_PORT=$POSTGRES_PORT
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
SEED_FILE=$SEED_FILE
SMTP_USER='$SMTP_USER'
SMTP_HOST='$SMTP_HOST'
SMTP_PASSWORD='$SMTP_PASSWORD'
SMTP_PORT=$SMTP_PORT
SMTP_TLS=$SMTP_TLS
SMTP_DEFAULT_SENDER='$SMTP_DEFAULT_SENDER'
LOG_LEVEL="$LOG_LEVEL"
OCPO_BASE_URL='$OCPO_BASE_URL'
XROAD_CLIENT='$XROAD_CLIENT'
XROAD_SERVICE='$XROAD_SERVICE'
POETRY_VERSION=$POETRY_VERSION
EOF

echo ".env file created successfully."


# 5. Launch the API
echo "--- Launching Docker Containers ---"
sudo docker network create xroad-network || true
sudo docker compose --profile dev up --build -d

echo "--- Deployment Complete ---"
echo "The API should be live shortly."