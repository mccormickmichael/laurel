provider "aws" {
  region = "us-west-2"
}

terraform {
  backend "s3" {
    bucket = "thousandleaves-artifacts"
    key    = "terraform/dev_service/vpc.tfstate"
    region = "us-west-2"
  }
}


