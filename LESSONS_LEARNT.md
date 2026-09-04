
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