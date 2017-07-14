
variable "vpc_id" {
  type = "string"
}

variable "vpc_cidr_block" {
  type = "string"
}

variable "nat_subnet_id" {
  type = "string"
}

variable "private_rt_id" {
  type = "string"
}

variable "prefix" {
  type = "string"
}

variable "stack" {
  type = "string"
}
  
resource "aws_iam_role" "nat_role" {
  name               = "${var.prefix}NATInstanceRole"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [ {
    "Action": "sts:AssumeRole",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Effect": "Allow"
  } ]
}
EOF
}

resource "aws_iam_role_policy" "nat_policy" {
  name   = "${var.prefix}NATInstancePolicy"
  role   = "${aws_iam_role.nat_role.id}"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [ {
    "Effect": "Allow",
    "Resource": ["arn:aws:ec2:*"],
    "Action": [ "ec2:CreateRoute", "ec2:DeleteRoute", "ec2:ModifyInstanceAttribute" ]
  } ]
}
EOF
}

resource "aws_iam_instance_profile" "nat_profile" {
  name = "${var.prefix}NATInstanceProfile"
  role = "${aws_iam_role.nat_role.id}"
}

resource "aws_security_group" "nat_sg" {
  name   = "${var.prefix}NATSecurityGroup"
  vpc_id = "${var.vpc_id}"
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [ "${var.vpc_cidr_block}" ]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [ "0.0.0.0/0" ]
  }
  tags {
    Name = "${var.prefix}NAT"
    Terraform = "${var.stack}"
  }
}

resource "aws_instance" "nat" {
  ami                    = "ami-8bfce8f2"  # Note only good for us-west-2
  instance_type          = "t2.micro"
  vpc_security_group_ids = [ "${aws_security_group.nat_sg.id}" ]
  subnet_id              = "${var.nat_subnet_id}"
  source_dest_check      = false
  iam_instance_profile   = "${aws_iam_instance_profile.nat_profile.id}"
  user_data = <<EOF
#!/bin/bash
yum update -y && yum install -y yum-cron && chkconfig yum-cron on
INS_ID=`curl http://169.254.169.254/latest/meta-data/instance-id`
aws ec2 delete-route --destination-cidr-block 0.0.0.0/0 --route-table-id ${var.private_rt_id} --region us-west-2
aws ec2 create-route --route-table-id ${var.private_rt_id} --destination-cidr-block 0.0.0.0/0 --instance-id $INS_ID --region us-west-2
EOF
  tags {
    Name = "${var.prefix}NAT"
    Terraform = "${var.stack}"
  }

}

output "nat_id" {
  value = "${aws_instance.nat.id}"
}
