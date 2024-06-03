#!/bin/bash
# Script to delete the CloudFormation stack

echo "Deleting the CloudFormation Stack..."
aws cloudformation delete-stack --stack-name MyEKSStack

echo "Stack deletion initiated. Monitor the AWS Management Console for status."
