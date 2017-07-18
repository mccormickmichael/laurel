variable "domain" {
  type = "string"
}

variable "vpc_id" {
  type = "string"
}

variable "prefix" {
  type = "string"
}

variable "stack" {
  type = "string"
}

resource "aws_route53_zone" "zone" {
  name = "${var.domain}"
  vpc_id = "${var.vpc_id}"
  tags {
    Name = "${var.prefix}"
    Terraform = "${var.stack}"
  }
}

output "zone_id" {
  value = "${aws_route53_zone.zone.id}"
}

output "nameservers" {
  value = "${aws_route53_zone.zone.name_servers.*}"
}
