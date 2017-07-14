variable  "vpc_id" {
  type = "string"
}

variable "cidr_block" {
  type = "string"
}

variable "vpc_cidr_block" {
  type = "string"
}

variable "route_table_id" {
  type = "string"
}

variable "az" {
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
  availability_zone = "${var.az}"
  map_public_ip_on_launch = true
  tags {
    Name = "${var.prefix}Public${var.suffix}"
    Terraform = "${var.stack}"
  }
}

resource "aws_network_acl" "nacl" {
  vpc_id = "${var.vpc_id}"
  subnet_ids = [ "${aws_subnet.subnet.id}" ]
  egress {
    rule_no  = 100
    protocol = "all"
    from_port = 0
    to_port = 0
    cidr_block = "0.0.0.0/0"
    action = "allow"
  }
  ingress {  # HTTPS from public
    rule_no = 100
    protocol = "tcp"
    from_port = 443
    to_port = 443
    cidr_block = "0.0.0.0/0"
    action = "allow"
  }
  ingress { # OpenVPN from public
    rule_no = 101
    protocol = "tcp"
    from_port = 943
    to_port = 943
    cidr_block = "0.0.0.0/0"
    action = "allow"
  }

  ingress { # Ephemeral return
    rule_no = 150
    protocol = "tcp"
    from_port = 1024
    to_port = 65535
    cidr_block = "0.0.0.0/0"
    action = "allow"
  }
  ingress { # UDP Gossip
    rule_no = 200
    protocol = "udp"
    from_port = 1024
    to_port = 65535
    cidr_block = "${var.vpc_cidr_block}"
    action = "allow"
  }
  ingress { # TCP Internal
    rule_no = 250
    protocol = "tcp"
    from_port = 0
    to_port = 65535
    cidr_block = "${var.vpc_cidr_block}"
    action = "allow"
  }    
  ingress { # Temp SSH
    rule_no = 300
    protocol = "tcp"
    from_port = 22
    to_port = 22
    cidr_block = "0.0.0.0/0"
    action = "allow"
  }
  tags {
    Name = "${var.prefix}Public${var.suffix}"
    Terraform = "${var.stack}"
  }
}

resource "aws_route_table_association" "rt_assoc" {
  subnet_id = "${aws_subnet.subnet.id}"
  route_table_id = "${var.route_table_id}"
}

output "subnet_id" {
  value = "${aws_subnet.subnet.id}"
}
