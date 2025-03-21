#!/bin/bash
set -e

# AI Tax Law Assistant Deployment Script
# This script deploys the Docker containers for the AI Tax Law Assistant to a local environment.

# Display script usage
display_usage() {
    echo "Usage: $0 [version_tag]"
    echo "If no version tag is provided, 'latest' will be used."
}

# Check if version tag is provided, otherwise use 'latest'
VERSION_TAG=${1:-latest}
echo "Deploying version: $VERSION_TAG"

# Define container registry and image prefix
CONTAINER_REGISTRY="ghcr.io"
REPO_NAME=$(echo $GITHUB_REPOSITORY | tr '[:upper:]' '[:lower:]')

if [ -z "$REPO_NAME" ]; then
    # If not running in GitHub Actions, extract from git remote
    REPO_NAME=$(git config --get remote.origin.url | sed 's/.*github.com[\/:]\(.*\)\.git/\1/' | tr '[:upper:]' '[:lower:]')
fi

# Check for required tools
which docker-compose > /dev/null 2>&1 || { echo "docker-compose is required but not installed. Aborting."; exit 1; }

# Create a temporary docker-compose override file
cat > docker-compose.override.yml << EOF
version: "3.8"
services:
  backend:
    image: ${CONTAINER_REGISTRY}/${REPO_NAME}/backend:${VERSION_TAG}
    restart: always
    volumes:
      - ./data:/app/data
    environment:
      - SPRING_PROFILES_ACTIVE=production
      - RAG_ENGINE_URL=http://rag-engine:5000
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}

  rag-engine:
    image: ${CONTAINER_REGISTRY}/${REPO_NAME}/rag-engine:${VERSION_TAG}
    restart: always
    volumes:
      - ./data:/app/data

  ai-agent:
    image: ${CONTAINER_REGISTRY}/${REPO_NAME}/ai-agent:${VERSION_TAG}
    restart: always
    volumes:
      - ./data:/app/data
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
EOF

echo "Created deployment configuration for version ${VERSION_TAG}"

# Stop any running containers
echo "Stopping existing containers..."
docker-compose down || true

# Pull the latest images
echo "Pulling latest images..."
docker-compose pull

# Start the containers
echo "Starting containers..."
docker-compose up -d

# Check if containers are running
echo "Checking container status..."
docker-compose ps

# Display logs
echo "Container logs:"
docker-compose logs --tail=20

echo "Deployment completed successfully!"
echo "Backend API is available at: http://localhost:8080/api"
echo "RAG Engine is available at: http://localhost:5000"

# Instructions for browser extension
echo "Browser Extension: You can load the extension from browser-extension/dist/ directory"
echo "Make sure to add your OPENAI_API_KEY to the environment if not already set"

exit 0
