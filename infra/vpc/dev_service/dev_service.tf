
variable "cidr_block" {
  description = "CIDR block to reserve for the VPC"
  type        = "string"
}

variable "prefix" {
  description = "Prefix to use when naming resources"
  type        = "string"
}

variable "stack" {
  description = "Name to use for tagging resources"
  type        = "string"
}

# variable "domain" {
#   description = "Domain name for the associated hosted zone"
#   type        = "string"
# }

variable "_availability_zones" {
  type = "list"
  default = ["a", "b", "c"]
}

variable "_region" {
  type = "string"
  default = "us-west-2"
}

module "vpc" {
  source     = "../modules/easy_vpc"
  cidr_block = "${var.cidr_block}"
  prefix     = "${var.prefix}"
  stack      = "${var.stack}"
}

module "public_rt" {
  source = "../modules/easy_public_rt"
  vpc_id = "${module.vpc.vpc_id}"
  igw_id = "${module.vpc.igw_id}"
  prefix = "${var.prefix}"
  stack  = "${var.stack}"
}

module "public_subnet" {
  source         = "../modules/easy_public_subnet"
  vpc_id         = "${module.vpc.vpc_id}"
  cidr_block     = "${cidrsubnet("${var.cidr_block}", 3, 0)}"
  vpc_cidr_block = "${var.cidr_block}"
  az             = "${var._region}${var._availability_zones[1]}"
  route_table_id = "${module.public_rt.rt_id}"
  prefix         = "${var.prefix}"
  suffix         = "${upper("${var._availability_zones[1]}")}"
  stack          = "${var.stack}"
}

# TODO: future public subnets A and C use cidr subnet indexes 0 and 2

module "private_rt" {
  source        = "../modules/easy_private_rt"
  vpc_id        = "${module.vpc.vpc_id}"
  prefix        = "${var.prefix}"
  stack         = "${var.stack}"
}

## AARGH! Modules don't support `count`, so we make all 3 private subnets here manually.

module "private_subnet_a" {
  source         = "../modules/easy_private_subnet"
  vpc_id         = "${module.vpc.vpc_id}"
  cidr_block     = "${cidrsubnet("${var.cidr_block}", 3, 4)}"
  vpc_cidr_block = "${var.cidr_block}"
  az             = "${var._region}${var._availability_zones[0]}"
  route_table_id = "${module.private_rt.rt_id}"
  prefix         = "${var.prefix}"
  suffix         = "${upper("${var._availability_zones[0]}")}"
  stack          = "${var.stack}"
}

module "private_subnet_b" {
  source         = "../modules/easy_private_subnet"
  vpc_id         = "${module.vpc.vpc_id}"
  cidr_block     = "${cidrsubnet("${var.cidr_block}", 3, 5)}"
  vpc_cidr_block = "${var.cidr_block}"
  az             = "${var._region}${var._availability_zones[1]}"
  route_table_id = "${module.private_rt.rt_id}"
  prefix         = "${var.prefix}"
  suffix         = "${upper("${var._availability_zones[1]}")}"
  stack          = "${var.stack}"
}

module "private_subnet_c" {
  source         = "../modules/easy_private_subnet"
  vpc_id         = "${module.vpc.vpc_id}"
  cidr_block     = "${cidrsubnet("${var.cidr_block}", 3, 6)}"
  vpc_cidr_block = "${var.cidr_block}"
  az             = "${var._region}${var._availability_zones[2]}"
  route_table_id = "${module.private_rt.rt_id}"
  prefix         = "${var.prefix}"
  suffix         = "${upper("${var._availability_zones[2]}")}"
  stack          = "${var.stack}"
}

module "nat" {
  source         = "../modules/easy_nat"
  vpc_id         = "${module.vpc.vpc_id}"
  vpc_cidr_block = "${var.cidr_block}"
  nat_subnet_id  = "${module.public_subnet.subnet_id}"
  private_rt_id  = "${module.private_rt.rt_id}"
  prefix         = "${var.prefix}"
  stack          = "${var.stack}"
}

# module "dns" {
#   source  = "../modules/easy_private_zone"
#   domain  = "${var.domain}"
#   vpc_id  = "${module.vpc.vpc_id}"
#   prefix  = "${var.prefix}"
#   stack   = "${var.stack}"
# }

output "vpc_id" {
  value = "${module.vpc.vpc_id}"
}

output "public_subnet_id" {
  value = "${module.public_subnet.subnet_id}"
}

output "private_subnet_a_id" {
  value = "${module.private_subnet_a.subnet_id}"
}

output "private_subnet_b_id" {
  value = "${module.private_subnet_b.subnet_id}"
}

output "private_subnet_c_id" {
  value = "${module.private_subnet_c.subnet_id}"
}

output "private_rt_id" {
  value = "${module.private_rt.rt_id}"
}

output "nat_instance_id" {
  value = "${module.nat.nat_id}"
}

# output "hosted_zone_id" {
#   value = "${module.dns.zone_id}"
# }
