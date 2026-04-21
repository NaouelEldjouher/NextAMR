output "env_config" {
  value = <<EOT
AMR_S3_BUCKET=${aws_s3_bucket.amr_storage.id}
AMR_BATCH_QUEUE=${aws_batch_job_queue.amr_queue.arn}
AMR_JOB_ROLE_ARN=${aws_iam_role.amr_job_role.arn}
AMR_SUBNETS=${join(",", var.subnet_ids)}
AMR_SECURITY_GROUPS=${aws_security_group.amr_sg.id}
AWS_DEFAULT_REGION=${var.region}
EOT
}