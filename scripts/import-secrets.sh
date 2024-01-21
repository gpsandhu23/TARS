#!/bin/bash

# Set the Kubernetes secret name
SECRET_NAME=tars-secrets-prod

# Delete the existing secret (if any)
kubectl delete secret $SECRET_NAME --ignore-not-found

# Create the secret from the .env file
kubectl create secret generic $SECRET_NAME --from-env-file=../.env.prod