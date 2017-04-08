variable "vpc_id" {
  type = "string"
}

variable "vpc_cidr_block" {
  type = "string"
}

variable "subnets" {
  type = "list"
}

variable "prefix" {
  type = "string"
}

variable "stack" {
  type = "string"
}

resource "aws_network_acl" "public" {
  vpc_id = "${var.vpc_id}"
  subnet_ids = ["${var.subnets}"]

  tags {
    Name = "${var.prefix}NaclPublic"
    Terraform = "${var.stack}"
  }
}

resource "aws_network_acl_rule" "any_out" {
  network_acl_id = "${aws_network_acl.public.id}"
  rule_number = 100
  egress = true
  protocol = -1
  rule_action = "allow"
  cidr_block = "0.0.0.0/0"
  from_port = 0
  to_port = 65535
}

resource "aws_network_acl_rule" "ssh_in" {
  network_acl_id = "${aws_network_acl.public.id}"
  rule_number = 100
  egress = false
  protocol = 6
  rule_action = "allow"
  cidr_block = "0.0.0.0/0"
  from_port = 22
  to_port = 22
}

resource "aws_network_acl_rule" "http_in" {
  network_acl_id = "${aws_network_acl.public.id}"
  rule_number = 101
  egress = false
  protocol = 6
  rule_action = "allow"
  cidr_block = "0.0.0.0/0"
  from_port = 80
  to_port = 80
}

resource "aws_network_acl_rule" "https_in" {
  network_acl_id = "${aws_network_acl.public.id}"
  rule_number = 102
  egress = false
  protocol = 6
  rule_action = "allow"
  cidr_block = "0.0.0.0/0"
  from_port = 443
  to_port = 443
}

resource "aws_network_acl_rule" "gossip_in" {
  network_acl_id = "${aws_network_acl.public.id}"
  rule_number = 150
  egress = false
  protocol = 17
  rule_action = "allow"
  cidr_block = "${var.vpc_cidr_block}"
  from_port = 1024
  to_port = 65535
}

resource "aws_network_acl_rule" "ephemeral_in" {
  network_acl_id = "${aws_network_acl.public.id}"
  rule_number = 200
  egress = false
  protocol = 6
  rule_action = "allow"
  cidr_block = "0.0.0.0/0"
  from_port = 1024
  to_port = 65535
}

output "nacl_id" {
  value = "${aws_network_acl.public.id}"
}
