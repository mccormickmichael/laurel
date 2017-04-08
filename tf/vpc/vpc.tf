variable "vpc_cidr_block" {
  type = "string"
}

variable "public_subnet_a_cidr_block" {
  type = "string"
}
variable "public_subnet_b_cidr_block" {
  type = "string"
}
variable "public_subnet_c_cidr_block" {
  type = "string"
}

variable "private_subnet_a_cidr_block" {
  type = "string"
}
variable "private_subnet_b_cidr_block" {
  type = "string"
}
variable "private_subnet_c_cidr_block" {
  type = "string"
}


variable "prefix" {
  type = "string"
}

variable "stack" {
  type = "string"
}

module "vpc" {
  source = "../modules/vpc/easy_vpc"
  vpc_cidr_block = "${var.vpc_cidr_block}"
  prefix = "${var.prefix}"
  stack = "${var.stack}"
}

module "public" {
  source = "../modules/vpc/public"
  vpc_id = "${module.vpc.vpc_id}"
  igw_id = "${module.vpc.igw_id}"
  cidr_block = "${cidrsubnet("${var.vpc_cidr_block}", 1, 1)}"
  prefix = "${var.prefix}Public"
  stack = "${var.stack}"
}  
