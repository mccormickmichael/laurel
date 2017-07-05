variable "cidr_block" {
  type = "string"
}

variable "prefix" {
  type = "string"
}

variable "stack" {
  type = "string"
}

resource "aws_vpc" "vpc" {
  cidr_block = "${var.cidr_block}"
  tags {
    Name = "${var.prefix}VPC"
    Terraform = "${var.stack}"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = "${aws_vpc.vpc.id}"
  tags {
    Name = "${var.prefix}VPC"
    Terraform = "${var.stack}"
  }
}

output "vpc_id" {
  value = "${aws_vpc.vpc.id}"
}

output "igw_id" {
  value = "${aws_internet_gateway.igw.id}"
}

