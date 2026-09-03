output "bucket_name" {
  value       = aws_s3_bucket.results.bucket
  description = "Name of the S3 bucket created for pipeline results"
}

output "bucket_arn" {
  value       = aws_s3_bucket.results.arn
  description = "ARN of the S3 bucket"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.scrnaseq.repository_url
  description = "Push your CI-built image here"
}

output "worker_instance_id" {
  value       = aws_instance.scrnaseq_worker.id
  description = "Instance ID — self-terminates after one run"
}

output "results_s3_path" {
  value       = "s3://${aws_s3_bucket.results.bucket}/${var.results_prefix}"
  description = "Where pipeline outputs land after a run"
}