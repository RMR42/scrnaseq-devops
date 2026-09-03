data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scrnaseq_worker" {
  name               = "scrnaseq-worker-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = {
    Project = "scrnaseq-devops-project"
  }
}

data "aws_iam_policy_document" "scrnaseq_s3_access" {
  statement {
    sid       = "ListBucket"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.results.arn]
  }

  statement {
    sid       = "ReadInputData"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.results.arn}/${var.input_prefix}*"]
  }

  statement {
    sid       = "WriteResults"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.results.arn}/${var.results_prefix}*"]
  }
}

resource "aws_iam_role_policy" "scrnaseq_s3_access" {
  name   = "scrnaseq-s3-access"
  role   = aws_iam_role.scrnaseq_worker.id
  policy = data.aws_iam_policy_document.scrnaseq_s3_access.json
}

data "aws_iam_policy_document" "scrnaseq_ecr_pull" {
  statement {
    sid       = "ECRAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "ECRPull"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchCheckLayerAvailability",
    ]
    resources = [aws_ecr_repository.scrnaseq.arn]
  }
}

resource "aws_iam_role_policy" "scrnaseq_ecr_pull" {
  name   = "scrnaseq-ecr-pull"
  role   = aws_iam_role.scrnaseq_worker.id
  policy = data.aws_iam_policy_document.scrnaseq_ecr_pull.json
}

resource "aws_iam_instance_profile" "scrnaseq_worker" {
  name = "scrnaseq-worker-profile"
  role = aws_iam_role.scrnaseq_worker.name
}