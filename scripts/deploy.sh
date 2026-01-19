#!/bin/bash
set -e

# Deployment script for bathhouse-booking
# Usage: ./scripts/deploy.sh [server_host]

SERVER_HOST="${1:-178.20.44.147}"
PROJECT_DIR="/opt/bathhouse-booking"

echo "Deploying to ${SERVER_HOST}..."

# SSH to server and execute deployment commands
ssh "${SERVER_HOST}" << EOF
set -e
cd "${PROJECT_DIR}"

echo "Pulling latest changes..."
git pull

echo "Running initialization..."
make init

echo "Restarting services..."
docker compose restart web bot

echo "Deployment completed successfully!"
EOF

echo "Deployment to ${SERVER_HOST} finished."