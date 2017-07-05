variable "vpc_id" {
  type = "string"
}

variable "igw_id" {
  type = "string"
}


variable "prefix" {
  type = "string"
}

variable "stack" {
  type = "string"
}

resource "aws_route_table" "rt" {
  vpc_id = "${var.vpc_id}"
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${var.igw_id}"
  }
  tags {
    Name = "${var.prefix}PublicRouteTable"
    Terraform = "${var.stack}"
  }
}

output "rt_id" {
  value = "${aws_route_table.rt.id}"
}
