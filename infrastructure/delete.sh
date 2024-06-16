#!/bin/bash

# Set variables
CLUSTER_NAME="tars-test"
NAMESPACE="default"
SECRET_NAME="tars-secrets"

# Delete secrets (if they exist)
kubectl delete secret $SECRET_NAME --namespace $NAMESPACE --ignore-not-found

# Check if the EKS cluster exists
eksctl get cluster --name $CLUSTER_NAME >/dev/null 2>&1
if [ $? -eq 0 ]; then
    # Delete EKS cluster if it exists
    eksctl delete cluster --name $CLUSTER_NAME
    echo "EKS cluster '$CLUSTER_NAME' deleted successfully."
else
    echo "EKS cluster '$CLUSTER_NAME' does not exist. Skipping deletion."
fi

echo "Infrastructure and resources deleted successfully!"