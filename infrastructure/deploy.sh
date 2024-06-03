#!/bin/bash
# Script to deploy the CloudFormation stack

echo "Deploying the CloudFormation Stack..."
aws cloudformation create-stack \
  --stack-name MyEKSStack \
  --template-body file://eks_setup.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

echo "Deployment initiated. Check the AWS Console for stack status."
