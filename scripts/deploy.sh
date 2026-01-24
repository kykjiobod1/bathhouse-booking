#!/bin/bash
set -euo pipefail

SERVER_HOST="${1:-178.20.44.147}"
SERVER_USER="root"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519_bathhouse}"
PROJECT_DIR="/opt/bathhouse-booking"

echo "Deploying to ${SERVER_USER}@${SERVER_HOST}..."

ssh -i "${SSH_KEY}" "${SERVER_USER}@${SERVER_HOST}" << EOF
set -euo pipefail

cd "${PROJECT_DIR}"

if [ ! -f .env ]; then
  echo "ERROR: .env not found in ${PROJECT_DIR}. Create it first."
  exit 1
fi

echo "Pulling latest changes..."
git pull --ff-only

echo "Running init..."
make init

echo "Deployment completed successfully!"
EOF

echo "Done."
