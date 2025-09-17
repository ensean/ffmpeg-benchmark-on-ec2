# Terraform configuration for FFmpeg benchmark instances

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for instances"
  type        = string
  default     = "ap-northeast-1"
}

variable "key_pair_name" {
  description = "EC2 Key Pair name"
  type        = string
}

# Security Group
resource "aws_security_group" "ffmpeg_benchmark" {
  name_prefix = "ffmpeg-benchmark-"
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["129.0.0.0/8"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# x86 Instances
resource "aws_instance" "c5_instance" {
  ami           = "ami-0d52744d6551d851e" # Ubuntu 24.04 LTS x86_64
  instance_type = "c5.xlarge"
  key_name      = var.key_pair_name
  
  vpc_security_group_ids = [aws_security_group.ffmpeg_benchmark.id]
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    architecture = "x86_64"
  }))
  
  tags = {
    Name = "ffmpeg-benchmark-c5-xlarge"
    Type = "FFmpeg-Benchmark"
    Arch = "x86_64"
  }
}

resource "aws_instance" "c7i_instance" {
  ami           = "ami-0d52744d6551d851e" # Ubuntu 24.04 LTS x86_64
  instance_type = "c7i.xlarge"
  key_name      = var.key_pair_name
  
  vpc_security_group_ids = [aws_security_group.ffmpeg_benchmark.id]
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    architecture = "x86_64"
  }))
  
  tags = {
    Name = "ffmpeg-benchmark-c7i-xlarge"
    Type = "FFmpeg-Benchmark"
    Arch = "x86_64"
  }
}

resource "aws_instance" "c7a_instance" {
  ami           = "ami-0d52744d6551d851e" # Ubuntu 24.04 LTS x86_64
  instance_type = "c7a.xlarge"
  key_name      = var.key_pair_name
  
  vpc_security_group_ids = [aws_security_group.ffmpeg_benchmark.id]
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    architecture = "x86_64"
  }))
  
  tags = {
    Name = "ffmpeg-benchmark-c7a-xlarge"
    Type = "FFmpeg-Benchmark"
    Arch = "x86_64"
  }
}

# Graviton Instance
resource "aws_instance" "c8g_instance" {
  ami           = "ami-0f36dcfcc94112ea1" # Ubuntu 24.04 LTS ARM64
  instance_type = "c8g.xlarge"
  key_name      = var.key_pair_name
  
  vpc_security_group_ids = [aws_security_group.ffmpeg_benchmark.id]
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    architecture = "arm64"
  }))
  
  tags = {
    Name = "ffmpeg-benchmark-c8g-xlarge"
    Type = "FFmpeg-Benchmark"
    Arch = "arm64"
  }
}

# Outputs
output "instance_ips" {
  value = {
    c5_xlarge  = aws_instance.c5_instance.public_ip
    c7i_xlarge = aws_instance.c7i_instance.public_ip
    c7a_xlarge = aws_instance.c7a_instance.public_ip
    c8g_xlarge = aws_instance.c8g_instance.public_ip
  }
}

output "connection_commands" {
  value = {
    c5_xlarge  = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_instance.c5_instance.public_ip}"
    c7i_xlarge = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_instance.c7i_instance.public_ip}"
    c7a_xlarge = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_instance.c7a_instance.public_ip}"
    c8g_xlarge = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_instance.c8g_instance.public_ip}"
  }
}