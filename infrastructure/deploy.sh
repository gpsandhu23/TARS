#!/bin/bash
# Script to deploy the CloudFormation stack

# Displaying the deployment initiation message
echo "Deploying the CloudFormation Stack"

# Command to create the CloudFormation stack with specified capabilities
aws cloudformation create-stack \
  --stack-name MyEKSStack \
  --template-body file://eks_setup.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Notification that deployment has been initiated
echo "Deployment initiated. Check the AWS Console for stack status."