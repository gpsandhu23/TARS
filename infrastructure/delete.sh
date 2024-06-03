#!/bin/bash
# Script to delete the CloudFormation stack

# Command to delete the specified CloudFormation stack
echo "Deleting the CloudFormation Stack..."
aws cloudformation delete-stack --stack-name MyEKSStack

# Notification that stack deletion has been initiated
echo "Stack deletion initiated. Monitor the AWS Management Console for status."
