#!/bin/bash

# Set variables
CLUSTER_NAME="tars-test"
REGION="us-west-2"
NAMESPACE="default"
SECRET_NAME="tars-secrets"

# Create EKS cluster
eksctl create cluster --name $CLUSTER_NAME --region $REGION --nodes 2 --node-type t3.medium --managed

# Create namespace (if it doesn't exist)
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Check if the .env file exists
if [ -f .env ]; then
    # Create secrets from .env file
    kubectl create secret generic $SECRET_NAME --from-env-file=.env --namespace $NAMESPACE
    echo "Secrets created successfully from .env file."
else
    echo "Error: .env file not found. Secrets not created."
    exit 1
fi

echo "Infrastructure setup and secrets creation completed successfully!"