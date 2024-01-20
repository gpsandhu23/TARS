#!/bin/bash

# Ensure the script stops if an error occurs
set -e

# Optional: Pull the latest changes from your Git repository
# git pull origin main

# Set Docker to use Minikube's Docker daemon
eval $(minikube docker-env)

# Build the Docker image with the 'latest' tag
docker build -t tars:latest .

# Run the script to import secrets into Minikube
./import-secrets.sh

# Apply the Kubernetes deployment
kubectl apply -f deployment.yaml

# Optional: Wait for the deployment to be rolled out
kubectl rollout status deployment/tars-deployment

echo "Deployment completed successfully!"