# Getting Started & Project Journey

## Overview

This project provides two ways to run the scRNA-seq analysis pipeline:

1. **Local / research use** — run the pipeline using Docker or a local
   environment without needing AWS.
2. **AWS / DevOps deployment** — run the same containerized pipeline on
   ephemeral EC2 workers using Terraform, ECR, S3, IAM, and GitHub Actions.

The AWS path is an optional deployment layer around the analysis pipeline;
an AWS account is not required to use the pipeline itself.

---

## Getting Started

### Option 1: Run Locally

The pipeline accepts an `.h5ad` AnnData file and produces a processed
AnnData object along with analysis outputs.

Basic usage:

```bash
python analysis/pipeline.py   --input path/to/raw.h5ad   --output path/to/result.h5ad
```

The pipeline performs:

- Quality control and filtering
- Normalization
- Highly variable gene selection
- PCA and neighbour graph construction
- Cell clustering
- Marker-gene ranking
- Optional cluster annotation
- Visualization
- Saving of the processed `.h5ad` object

The pipeline also supports optional input files for biological
interpretation:

```bash
python analysis/pipeline.py   --input path/to/raw.h5ad   --output path/to/result.h5ad   --clusters path/to/cluster_mapping.json   --markers path/to/marker_genes.json   --plot-dir figures
```

The `--clusters` file can provide a mapping between clusters and cell types,
while `--markers` can provide marker genes used for visualization. The
pipeline also generates its own `markers.csv` containing ranked marker genes
for the identified clusters.

### Main Outputs

A typical run produces:

```text
results/
├── processed.h5ad
├── markers.csv
└── figures/
    └── <plots>
```

The processed `.h5ad` retains the analysis results for further exploration
in tools such as Scanpy. The marker-gene table can be used to inspect genes
associated with individual clusters, while the figures provide visual
summaries of the analysis.

---

## Option 2: AWS / DevOps Deployment

The AWS deployment packages the same analysis workflow into a Docker
container and runs it on temporary EC2 compute.

### 1. Configure and provision infrastructure

```bash
cd infra/
```

Create a local `terraform.tfvars` file:

```hcl
bucket_name = "<your-unique-s3-bucket-name>"
```

Then:

```bash
terraform init
terraform plan
terraform apply
```

This provisions the AWS resources required by the project, including S3,
ECR, IAM, the security group, monitoring resources, and the EC2 Launch Template.

### 2. Build and push the analysis image

From the repository root:

```bash
docker build -t scrnaseq-analysis .
```

Authenticate with ECR:

```bash
aws ecr get-login-password --region <aws-region> | \
docker login --username AWS --password-stdin \
<account-id>.dkr.ecr.<aws-region>.amazonaws.com
```

Tag and push the image:

```bash
docker tag scrnaseq-analysis:latest \
<account-id>.dkr.ecr.<aws-region>.amazonaws.com/scrnaseq-analysis:latest

docker push \
<account-id>.dkr.ecr.<aws-region>.amazonaws.com/scrnaseq-analysis:latest
```

GitHub Actions can also build and publish the image automatically when
changes are pushed.

### 3. Upload a sample and launch a worker

```bash
aws s3 cp sample.h5ad \
s3://<your-bucket-name>/input-data/
```

Launch an EC2 worker and assign its input:

```bash
aws ec2 run-instances \
  --launch-template LaunchTemplateId=<launch-template-id> \
  --tag-specifications \
  'ResourceType=instance,Tags=[{Key=JobInputKey,Value=input-data/sample.h5ad}]' \
  --region <aws-region>
```

The worker reads its assigned input through EC2 metadata, downloads the
sample, runs the containerized Scanpy pipeline, uploads the results, and
terminates itself.

### 4. Check the results

```bash
aws s3 ls s3://<your-bucket-name>/results/ --recursive
```

Results are stored under a timestamped, per-sample directory:

```text
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

### 5. Tear down

```bash
cd infra/
terraform destroy
```

The EC2 worker is designed to terminate after each job, so compute is not
intentionally left running between executions.

---

## Project Journey

The project started with a bioinformatics pipeline that could run locally.
The goal was to explore how the same workload could be packaged and
deployed in a reproducible cloud environment.

I built the infrastructure incrementally:

```text
Docker
  ↓
ECR
  ↓
S3
  ↓
Terraform
  ↓
IAM + EC2
  ↓
Ephemeral workers
  ↓
Dynamic job assignment
```

This approach helped separate the scientific workflow from the infrastructure
needed to run it at scale.

The main lesson was that deployment is not simply about connecting AWS
services. Small details such as file paths, permissions, container
arguments, resource configuration, logging, and job assignment all have to
work together.

---

## Lessons Learned

- **Build one layer at a time.** Testing Docker, AWS resources, and the
  worker separately made failures much easier to understand.

- **Temporary compute needs persistent results.** An EC2 worker can disappear
  after a job, so logs, status, and analysis outputs need to be saved to S3
  before shutdown.

- **Keep configuration separate from code.** Values such as bucket names
  belong in environment-specific configuration rather than reusable
  Terraform source files.

- **The same pipeline can serve different users.** A researcher can run the
  pipeline locally without AWS, while a DevOps deployment can use the same
  containerized workflow on cloud infrastructure.

- **Start with a reliable single-job workflow.** Making one sample run
  correctly provided a stable foundation before moving toward automatic
  event-driven execution and parallel processing.

---

## Current Status

### Completed

- [x] Containerized scRNA-seq analysis pipeline
- [x] Quality control and normalization
- [x] Highly variable gene selection
- [x] PCA, neighbours, and clustering
- [x] Marker-gene ranking and `markers.csv`
- [x] Optional cluster annotation
- [x] Optional marker-gene input for visualization
- [x] Docker environment
- [x] Amazon ECR
- [x] S3 input/output storage
- [x] Terraform-managed AWS infrastructure
- [x] IAM-controlled access
- [x] Ephemeral EC2 worker
- [x] EC2 Launch Template
- [x] Dynamic per-job input assignment
- [x] Persistent S3 logging and status
- [x] GitHub Actions CI/CD

### Next Step

The next planned improvement is to remove the manual EC2 launch step:

```text
S3 upload
    ↓
S3 event
    ↓
Lambda
    ↓
EC2 worker
```

This will make the AWS path event-driven while keeping the local execution
path available for users who simply want to run the bioinformatics pipeline.
