provider "aws" {
  region = "us-west-2"
}

terraform {
  backend "s3" {
    bucket = "thousandleaves-artifacts"
    key    = "terraform/service/vpc.tfstate"
    region = "us-west-2"
  }
}

