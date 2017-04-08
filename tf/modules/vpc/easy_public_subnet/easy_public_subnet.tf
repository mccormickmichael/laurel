variable "vpc_id" {
  type = "string"
}

variable "route_table_id" {
  type = "string"
}

variable "cidr_block" {
  type = "string"
}

variable "prefix" {
  type = "string"
}

variable "suffix" {
  type = "string"
}

variable "stack" {
  type = "string"
}

resource "aws_subnet" "subnet" {
  vpc_id = "${var.vpc_id}"
  cidr_block = "${var.cidr_block}"
  tags {
    Name = "${var.prefix}Subnet${var.suffix}"
    Terraform = "${var.stack}"
  }
}

resource "aws_route_table_association" "rta" {
  subnet_id = "${aws_subnet.subnet.id}"
  route_table_id = "${var.route_table_id}"
}

output "subnet_id" {
  value = "${aws_subnet.subnet.id}"
}
