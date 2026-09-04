# AWS Containerized scRNA-seq Analysis Pipeline

A DevOps deployment project for running a reproducible containerized
single-cell RNA-seq analysis workflow on AWS. The project packages the
analysis environment with Docker, stores inputs/results in Amazon S3,
provisions infrastructure with Terraform, and uses an ephemeral EC2
worker launched from an AWS Launch Template.

## Project Overview

This project demonstrates how a bioinformatics workflow can be moved
from a local execution environment to a reproducible cloud-based
architecture.

``` text
Input .h5ad
    |
    v
Amazon S3 (input-data/)
    |
    v
EC2 Worker (Launch Template)
    |
    v
Docker Container (Scanpy)
    |
    v
Amazon S3 (results/)
    |
    v
EC2 self-terminates
```

Each `.h5ad` file is treated as an independent job. The worker receives
the S3 object key through an EC2 `JobInputKey` tag and retrieves that
value using the EC2 Instance Metadata Service (IMDSv2).

## Technologies Used

### Cloud & Infrastructure

-   AWS EC2
-   Amazon S3
-   Amazon ECR
-   AWS IAM
-   EC2 Launch Templates
-   EC2 Instance Metadata Service (IMDSv2)
-   AWS Security Groups

### Infrastructure as Code

-   Terraform

### Containers

-   Docker
-   Micromamba
-   Conda environment management

### Bioinformatics

-   Python
-   Scanpy
-   AnnData
-   Single-cell RNA-seq analysis

### Automation / DevOps

-   Git
-   GitHub Actions
-   Bash
-   Reproducible containerized execution

## Pipeline

The analysis container executes a Scanpy workflow:

1.  Load an `.h5ad` input file.
2.  Perform quality-control filtering.
3.  Identify highly variable genes.
4.  Perform PCA.
5.  Construct the neighborhood graph.
6.  Perform Leiden clustering.
7.  Identify marker genes.
8.  Generate a UMAP visualization.
9.  Write the processed `.h5ad` file.
10. Save marker genes and analysis figures.

Example output structure:

``` text
results/
└── <timestamp>/
    └── <sample>/
        ├── processed.h5ad
        ├── markers.csv
        ├── figures/
        │   └── umap.png
        ├── run.log
        └── status.txt
```

## Infrastructure Architecture

Terraform provisions the core AWS resources required by the worker:

``` text
Terraform
   |
   +-- S3 bucket
   +-- ECR repository
   +-- IAM role + policies
   +-- Security group
   +-- EC2 Launch Template
```

The Launch Template contains the worker configuration, including: -
Amazon Linux 2023 AMI - EC2 instance type - IAM instance profile -
Security group - 8 GB gp3 root volume - IMDSv2 configuration - Instance
metadata tags - Worker user-data script - Automatic instance termination
after shutdown

## Job Assignment

The worker does not have a hard-coded sample name.

Instead, the specific S3 object key is assigned to the EC2 instance as a
tag:

``` text
JobInputKey = input-data/sample2.h5ad
```

At startup, the worker:

1.  Requests an IMDSv2 token.
2.  Reads its own `JobInputKey` instance tag.
3.  Extracts the sample name.
4.  Downloads that specific `.h5ad` file from S3.
5.  Runs the Dockerized analysis.
6.  Uploads the results to a timestamped S3 directory.
7.  Shuts down, causing the ephemeral EC2 instance to terminate.

This separates the reusable worker infrastructure from the job-specific
input.

## Reproducibility

The analysis environment is defined in a version-controlled environment
file and built into a Docker image.

The Docker image is stored in Amazon ECR and executed by the EC2 worker.

This provides: - Consistent software dependencies - Reproducible
execution - Version-controlled infrastructure - Isolated analysis
environments - Separation of compute and storage - Ephemeral compute
resources

## CI/CD

The project uses GitHub Actions to build and publish the Docker image to
Amazon ECR.

``` text
GitHub repository
       |
       v
GitHub Actions
       |
       +-- Build Docker image
       +-- Authenticate to ECR
       +-- Push image
              |
              v
          Amazon ECR
              |
              v
          EC2 worker
```

## Security Considerations

The AWS deployment follows several security best practices:

- IAM instance profile: EC2 uses an IAM role with temporary AWS
  credentials instead of storing long-lived access keys on the instance.
- Scoped IAM permissions: The worker can read input objects from the
  `input-data/` prefix, write results to the `results/` prefix, and pull
  images from the project ECR repository.
- IMDSv2: Instance metadata access requires IMDSv2 tokens.
- Controlled metadata access: EC2 instance metadata tags are explicitly
  enabled because the worker uses the `JobInputKey` tag for runtime job
  assignment.
- Restricted inbound access: The worker does not require inbound SSH
  during normal operation. SSH is enabled only when explicitly configured
  for debugging and restricted to a specified CIDR range.
- No long-lived credentials in code: AWS credentials are not embedded in
  the Docker image or user-data script.
- Environment-specific configuration: Resource-specific values such as
  the S3 bucket name are kept outside the committed Terraform source.

## Example Manual Test

The Launch Template can be tested by assigning a specific S3 object key
when launching an instance:

``` bash
aws ec2 run-instances   --launch-template LaunchTemplateId=<launch-template-id>   --tag-specifications 'ResourceType=instance,Tags=[{Key=JobInputKey,Value=input-data/sample2.h5ad}]'   --region ap-south-1
```

The worker then discovers its assigned input from the EC2 tag rather
than receiving the value through a Terraform variable.

## Repository Structure

``` text
.
├── analysis/
│   └── pipeline.py
├── docker/
│   └── environment.yml
├── infra/
│   ├── ec2.tf
│   ├── iam.tf
│   ├── s3.tf
│   ├── ecr.tf
│   ├── variables.tf
│   └── user_data.sh.tpl
├── tests/
│   └── data/
├── Dockerfile
└── README.md
```

## Why This Project

The project applies DevOps principles to a computational biology
workload by separating:

-   **Application** --- Scanpy analysis
-   **Environment** --- Docker/Micromamba
-   **Infrastructure** --- Terraform
-   **Artifact storage** --- Amazon ECR
-   **Data storage** --- Amazon S3
-   **Compute** --- ephemeral EC2 workers
-   **Job configuration** --- EC2 instance metadata/tags
-   **Automation** --- GitHub Actions and planned event-driven AWS
    orchestration

The goal is to make a bioinformatics analysis workflow reproducible,
portable, and suitable for automated cloud execution.
