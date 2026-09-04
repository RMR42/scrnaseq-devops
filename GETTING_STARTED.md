# Getting Started & Project Journey

## Overview

This project provides two ways to run the scRNA-seq analysis pipeline:

1. **Local / research use** — run the pipeline using Docker without needing AWS.
2. **AWS / DevOps deployment** — run the same containerized pipeline on
   ephemeral EC2 workers using Terraform, ECR, S3, IAM, and GitHub Actions.

The AWS path is an optional deployment layer around the analysis pipeline;
an AWS account is not required to use the pipeline itself.

---

### Run Locally with Docker

The recommended way to run the pipeline locally is with Docker. This keeps the Python, Scanpy, and other bioinformatics dependencies isolated from the user's host environment.

The pipeline accepts an `.h5ad` AnnData file and produces a processed AnnData object along with analysis outputs.

#### 1. Build the Docker image

From the repository root:

```bash
docker build -f docker/Dockerfile -t scrnaseq-analysis .
```

#### 2. Prepare an output directory

```bash
mkdir -p results
```

#### 3. Run the pipeline

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/matplotlib \
  -v "/path/to/input:/data:ro" \
  -v "$(pwd)/results:/results" \
  scrnaseq-analysis:latest \
  --input /data/raw.h5ad \
  --output /results/processed.h5ad \
  --plot-dir /results/figures
```

Replace `/path/to/input` and `raw.h5ad` with the location and filename of your input `.h5ad` file.

The `--user` option ensures that output files are owned by the local user rather than the container user. `MPLCONFIGDIR` provides Matplotlib with a writable cache directory inside the container.

### Optional Biological Inputs

The pipeline also supports optional files for cluster annotation and marker-gene visualization:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/matplotlib \
  -v "/path/to/input:/data:ro" \
  -v "$(pwd)/results:/results" \
  scrnaseq-analysis:latest \
  --input /data/raw.h5ad \
  --output /results/processed.h5ad \
  --clusters /data/cluster_mapping.json \
  --markers /data/marker_genes.json \
  --plot-dir /results/figures
```

The `--clusters` file can provide a mapping between clusters and cell types, while `--markers` can provide marker genes used for visualization.

The pipeline also generates its own `markers.csv` containing ranked marker genes for the identified clusters.

### Analysis Steps

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

### Main Outputs

A typical run produces:

```text
results/
├── processed.h5ad
├── markers.csv
└── figures/
    └── <plots>
```

The processed `.h5ad` retains the analysis results for further exploration in tools such as Scanpy. The marker-gene table can be used to inspect genes associated with individual clusters, while the figures provide visual summaries of the analysis.

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
docker build -f docker/Dockerfile -t scrnaseq-analysis .
```

Authenticate with ECR:

```bash
aws ecr get-login-password --region <aws-region> | \
docker login --username AWS --password-stdin <account-id>.dkr.ecr.<aws-region>.amazonaws.com
```

Tag and push the image:

```bash
docker tag scrnaseq-analysis:latest <account-id>.dkr.ecr.<aws-region>.amazonaws.com/scrnaseq-analysis:latest

docker push <account-id>.dkr.ecr.<aws-region>.amazonaws.com/scrnaseq-analysis:latest
```

GitHub Actions automatically builds, tests, and publishes the image to GHCR. The image must currently be copied/promoted to the project ECR repository before it can be used by the EC2 worker.

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

This approach helped separate the scientific workflow from the infrastructure required for cloud-based and potentially parallel execution.

The main lesson was that deployment is not simply about connecting AWS
services. Small details such as file paths, permissions, container
arguments, resource configuration, logging, and job assignment all have to
work together.

