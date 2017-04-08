variable "vpc_id" {
  type = "string"
}

variable "igw_id" {
  type = "string"
}

variable "cidr_block" {
  type = "string"
}

variable "prefix" {
  type = "string"
}

variable "stack" {
  type = "string"
}

data "aws_availability_zones" "azs" {}

module "public_rt" {
  source = "../easy_public_rt"
  vpc_id = "${var.vpc_id}"
  igw_id = "${var.igw_id}"
  prefix = "${var.prefix}"
  stack = "${var.stack}"
}
# module.public_rt.rt_id

resource "aws_subnet" "subnet" {
  count = 3  # TODO: we're committing to 3 subnets; rename module accordingly
  vpc_id = "${var.vpc_id}"
  cidr_block = "${cidrsubnet("${var.cidr_block}", 2, "${count.index}")}"
  availability_zone = "${data.aws_availability_zones.azs.names[count.index]}"
  tags {
    Name = "${var.prefix}Subnet${count.index}"
    Terraform = "${var.stack}"
  }
}

resource "aws_route_table_association" "rta" {
  count = 3
  subnet_id = "${element(aws_subnet.subnet.*.id, count.index)}"
  route_table_id = "${module.public_rt.rt_id}"
}

module "public_nacl" {
  source = "../easy_public_nacl"
  vpc_id = "${var.vpc_id}"
  vpc_cidr_block = "${var.cidr_block}"
  prefix = "${var.prefix}"
  stack = "${var.stack}"
  subnets = [ "${aws_subnet.subnet.*.id}" ]
}

output "nacl_id" {
  value = "${module.public_nacl.nacl_id}"
}
output "rt_id" {
  value = "${module.public_rt.rt_id}"
}
output "subnet_ids" {
  value = ["${aws_subnet.subnet.*.id}"]
}
