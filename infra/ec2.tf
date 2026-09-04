resource "aws_s3_object" "input_data" {
  count  = var.upload_test_data ? 1 : 0
  bucket = aws_s3_bucket.results.id
  key    = "${var.input_prefix}pbmc3k_test.h5ad"
  source = var.input_data_local_path
  etag   = filemd5(var.input_data_local_path)
}

# No inbound access needed for a batch job that runs once and shuts itself
# down. SSH is opened only if you pass a key_name, for debugging.
resource "aws_security_group" "scrnaseq_worker" {
  name        = "scrnaseq-worker-sg"
  description = "Security group for the scRNA-seq pipeline worker instance"

  dynamic "ingress" {
    for_each = var.key_name != "" ? [1] : []
    content {
      description = "SSH for debugging"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.ssh_allowed_cidr]
    }
  }

  egress {
    description = "Allow all outbound (ECR pull, S3, package installs)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = "scrnaseq-devops-project"
  }
}

resource "aws_instance" "scrnaseq_worker" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.scrnaseq_worker.name
  vpc_security_group_ids = [aws_security_group.scrnaseq_worker.id]
  key_name               = var.key_name != "" ? var.key_name : null


  instance_initiated_shutdown_behavior = "terminate"

  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    aws_region     = var.aws_region
    ecr_repo_url   = aws_ecr_repository.scrnaseq.repository_url
    image_tag      = var.image_tag
    bucket_name    = aws_s3_bucket.results.bucket
    input_prefix   = var.input_prefix
    results_prefix = var.results_prefix
  })

  user_data_replace_on_change = true


  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    delete_on_termination = true
  }

  tags = {
    Name    = "scrnaseq-worker"
    Project = "scrnaseq-devops-project"
  }

  depends_on = [aws_iam_role_policy.scrnaseq_s3_access, aws_iam_role_policy.scrnaseq_ecr_pull]
}


resource "aws_launch_template" "scrnaseq_worker" {
  name_prefix = "scrnaseq-worker-"

  image_id      = data.aws_ami.al2023.id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.scrnaseq_worker.name
  }

  vpc_security_group_ids = [
    aws_security_group.scrnaseq_worker.id
  ]

  key_name = var.key_name != "" ? var.key_name : null

  instance_initiated_shutdown_behavior = "terminate"

  user_data = base64encode(templatefile("${path.module}/user_data.sh.tpl", {
    aws_region     = var.aws_region
    ecr_repo_url   = aws_ecr_repository.scrnaseq.repository_url
    image_tag      = var.image_tag
    bucket_name    = aws_s3_bucket.results.bucket
    input_prefix   = var.input_prefix
    results_prefix = var.results_prefix

  }))

  metadata_options {
    http_endpoint          = "enabled"
    http_tokens            = "required"
    instance_metadata_tags = "enabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_type           = "gp3"
      volume_size           = 8
      delete_on_termination = true
    }
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name    = "scrnaseq-worker"
      Project = "scrnaseq-devops-project"
    }
  }
  depends_on = [
    aws_iam_role_policy.scrnaseq_s3_access,
    aws_iam_role_policy.scrnaseq_ecr_pull
  ]
}