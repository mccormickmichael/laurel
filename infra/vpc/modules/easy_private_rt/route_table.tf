variable "vpc_id" {
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

  # The Private Route Table ships with no routes. Another module or external process should attach routes as appropriate.

  tags {
    Name = "${var.prefix}PrivateRouteTable"
    Terraform = "${var.stack}"
  }
}

output "rt_id" {
  value = "${aws_route_table.rt.id}"
}
