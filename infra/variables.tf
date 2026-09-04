variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
  default     = "ap-south-1" # Mumbai region — closest to Pune
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name used for both input data and pipeline results. No default on purpose — set it in a local terraform.tfvars (gitignored)."
  type        = string
}

variable "input_prefix" {
  description = "S3 key prefix under which input data (e.g. the PBMC3k test fixture) is stored"
  type        = string
  default     = "input-data/"
}

variable "results_prefix" {
  description = "S3 key prefix under which pipeline results are uploaded, one subfolder per run"
  type        = string
  default     = "results/"
}

variable "ecr_repo_name" {
  description = "Name of the ECR repository holding the scRNA-seq analysis image"
  type        = string
  default     = "scrnaseq-analysis"
}

variable "image_tag" {
  description = "Tag of the image in ECR to run (pushed there by the GitHub Actions workflow)"
  type        = string
  default     = "latest"
}

variable "instance_type" {
  description = "EC2 instance type for running the analysis. t3.micro (1 GB RAM) is fine for the small PBMC3k test fixture and is the free-tier-eligible size. If you later run larger datasets and need more memory, you'll move outside free tier — bump this deliberately, not by accident."
  type        = string
  default     = "t3.micro"
}

variable "input_data_local_path" {
  description = "Local path (relative to where `terraform apply` is run) to the test fixture that gets uploaded to S3 as the pipeline input. Set upload_test_data = false to skip this and upload manually with `aws s3 cp` instead."
  type        = string
  default     = "../nf-scrnaseq-devops/tests/data/pbmc3k_test.h5ad"
}

variable "upload_test_data" {
  description = "Whether Terraform should upload input_data_local_path to S3 itself. If false, upload the fixture yourself before running the instance."
  type        = bool
  default     = false
}

variable "key_name" {
  description = "Optional existing EC2 key pair name, for SSH access while debugging. Leave blank to disable SSH access entirely."
  type        = string
  default     = ""
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to SSH into the instance. Only used if key_name is set. No default on purpose — if key_name is set but this is left blank, no SSH ingress rule is created at all, so you can't accidentally open port 22 to 0.0.0.0/0."
  type        = string
  default     = ""
}

variable "budget_alert_email" {
  description = "Email to notify if AWS spend approaches budget_monthly_limit_usd. Leave blank to skip creating the budget alert."
  type        = string
  default     = ""
}

variable "budget_monthly_limit_usd" {
  description = "Monthly spend threshold (USD) that triggers the budget alert email, only used if budget_alert_email is set"
  type        = number
  default     = 2
}
