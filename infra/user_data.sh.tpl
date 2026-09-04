#!/bin/bash
# Rendered by Terraform (templatefile) — variables below come from ec2.tf.
set -euxo pipefail

LOG_FILE=/var/log/scrnaseq-user-data.log
exec > >(tee "$LOG_FILE") 2>&1
echo "=== scRNA-seq job started at $(date -u) ==="

REGION="${aws_region}"
ECR_REPO_URL="${ecr_repo_url}"
IMAGE_TAG="${image_tag}"
BUCKET="${bucket_name}"
RESULTS_PREFIX="${results_prefix}"
TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"

# the specific input file is supplied at EC2 launch time
# through the instance tag "JobInputKey".
IMDS_TOKEN="$(curl -sS -X PUT \
  "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")"

JOB_INPUT_KEY="$(curl -sS \
  -H "X-aws-ec2-metadata-token: $IMDS_TOKEN" \
  "http://169.254.169.254/latest/meta-data/tags/instance/JobInputKey")"

if [ -z "$JOB_INPUT_KEY" ]; then
  echo "ERROR: JobInputKey instance tag was not provided" >&2
  exit 1
fi

SAMPLE_NAME="$(basename "$JOB_INPUT_KEY" .h5ad)"
echo "This worker's job: $JOB_INPUT_KEY (sample: $SAMPLE_NAME)"


on_exit() {
  local exit_code=$?
  set +e
  echo "=== job exiting with code $exit_code at $(date -u) ==="

  SAMPLE_RESULTS_PATH="s3://$BUCKET/$${RESULTS_PREFIX}$${TIMESTAMP}/$${SAMPLE_NAME}"

  if command -v aws >/dev/null 2>&1; then
    aws s3 cp "$LOG_FILE" "$SAMPLE_RESULTS_PATH/run.log" \
      || echo "WARNING: could not upload log"

    if [ "$exit_code" -eq 0 ]; then
      echo "SUCCESS" | aws s3 cp - "$SAMPLE_RESULTS_PATH/status.txt" \
        || echo "WARNING: could not upload status"
    else
      echo "FAILED (exit code $exit_code)" | aws s3 cp - "$SAMPLE_RESULTS_PATH/status.txt" \
        || echo "WARNING: could not upload status"
    fi
  else
    echo "WARNING: aws CLI unavailable, could not upload log/status"
  fi
  shutdown -h now
}
trap on_exit EXIT

dnf update -y
dnf install -y docker
systemctl enable --now docker

if ! command -v aws >/dev/null 2>&1; then
  dnf install -y unzip
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp
  /tmp/aws/install
fi

mkdir -p /opt/scrnaseq/data /opt/scrnaseq/results
chmod -R 777 /opt/scrnaseq/data /opt/scrnaseq/results

# --- Pull the analysis image from ECR ---
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ECR_REPO_URL"
docker pull "$ECR_REPO_URL:$IMAGE_TAG"

# --- Fetch exactly the one sample this worker was assigned, nothing else ---
LOCAL_INPUT_FILE="/opt/scrnaseq/data/$(basename "$JOB_INPUT_KEY")"
aws s3 cp "s3://$BUCKET/$JOB_INPUT_KEY" "$LOCAL_INPUT_FILE"

SAMPLE_OUT_DIR="/opt/scrnaseq/results/$TIMESTAMP/$SAMPLE_NAME"
mkdir -p "$SAMPLE_OUT_DIR"
chmod 777 "$SAMPLE_OUT_DIR"

# --- Run the pipeline in the container ---
docker run --rm \
  -v /opt/scrnaseq/data:/data \
  -v /opt/scrnaseq/results:/results \
  "$ECR_REPO_URL:$IMAGE_TAG" \
  --input "/data/$(basename "$LOCAL_INPUT_FILE")" \
  --output "/results/$TIMESTAMP/$SAMPLE_NAME/processed.h5ad" \
  --plot-dir "/results/$TIMESTAMP/$SAMPLE_NAME/figures"

# --- Push this sample's results back to S3 ---
aws s3 cp \
  "$SAMPLE_OUT_DIR" \
  "s3://$BUCKET/$${RESULTS_PREFIX}$${TIMESTAMP}/$${SAMPLE_NAME}/" \
  --recursive

echo "=== Job for sample $SAMPLE_NAME finished successfully at $(date -u) ==="
