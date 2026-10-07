terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = "test"
  secret_key = "test"

  # AWS Config
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  # Calling LocalStack
  endpoints {
    s3 = "http://localhost:4566"
  }
}

resource "aws_s3_bucket" "bronze" {
  bucket = "weather-bronze"
}

resource "aws_s3_bucket" "silver" {
  bucket = "weather-silver"
}

resource "aws_s3_bucket" "gold" {
  bucket = "weather-gold"
}