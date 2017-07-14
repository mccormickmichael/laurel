#!/bin/bash

aws cloudformation create-stack --region us-west-2 --capabilities CAPABILITY_IAM --stack-name DevService --template-body file://service.yaml
