An experiment in building a VPC and NAT instance using Terraform.

3 private subnets
3 public subnets
3 NAT instances, each guarded by an ASG, attaching themselves to the appropriate ENI on startup.