#!/bin/bash -xe

terraform refresh
NAT_ID=$(terraform output | grep "nat_instance_id" | awk '{print $3}')
aws ec2 start-instances --instance-ids ${NAT_ID} --region us-west-2
