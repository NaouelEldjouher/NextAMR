provider "aws" { region = var.region }

# S3 Storage
resource "aws_s3_bucket" "amr_storage" {
  bucket = var.bucket_name
  force_destroy = true 
}

# IAM Role for Nextflow Jobs
resource "aws_iam_role" "amr_job_role" {
  name = "AMR-Flow-Job-Role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "s3_full" {
  role       = aws_iam_role.amr_job_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Batch Compute (Fargate)
resource "aws_batch_compute_environment" "amr_compute" {
  compute_environment_name = "amr-flow-fargate"
  type = "MANAGED"
  compute_resources {
    type = "FARGATE"
    max_vcpus = 16
    subnets = var.subnet_ids
    security_group_ids = [aws_security_group.amr_sg.id]
  }
}

# Batch Queue
resource "aws_batch_job_queue" "amr_queue" {
  name = "amr-flow-queue"
  state = "ENABLED"
  priority = 1
  compute_environments = [aws_batch_compute_environment.amr_compute.arn]
}

# Networking
resource "aws_security_group" "amr_sg" {
  name = "amr-flow-sg"
  vpc_id = var.vpc_id
  egress { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = ["0.0.0.0/0"] }
}