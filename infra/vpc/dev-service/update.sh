#!/bin/bash

aws cloudformation update-stack --region us-west-2 --capabilities CAPABILITY_IAM --stack-name DevService --template-body file://service.yaml
