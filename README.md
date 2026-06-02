# 🧬 NextAMR: Cloud-Native Genomic Assembler & AMR Detector
A high-performance hybrid pipeline for Short, Long, and Hybrid read assembly on AWS Batch.

![Nextflow](https://img.shields.io/badge/Nextflow-23.04+-brightgreen) ![AWS](https://img.shields.io/badge/AWS-Batch-orange) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)

NextAMR is a high-performance bioinformatics pipeline optimized for AWS Batch. It automates the transition from raw sequencing reads to fully annotated genomes and comprehensive Antimicrobial Resistance (AMR) profiles.

By utilizing a High-Storage EC2 Architecture, the pipeline provides a dedicated 200GB "scratch space" to handle heavy genomic databases, overcoming the storage limitations of standard serverless platforms.

---

## 🌟 Key Features
- **Tri-Mode Assembly:** Seamlessly handles Short-read (Illumina), Long-read (Nanopore/PacBio), and Hybrid (Short + Long) data.
- **AWS Batch Native:** Orchestrates EC2 instances across Spot and On-Demand compute for cost-efficiency and reliability.
- **Automated S3 Ingestion:** A custom Streamlit UI manages secure file transfers and manifest generation.

---

## 🌟 Architectural Design Patterns

**Stateless Control Plane:**
The Streamlit UI manages the workflow without storing genomic data, streaming 10GB+ files directly to S3 via Multipart Uploads.

**Decoupled Two-Tier Storage:**
- Static Tier: Persistent S3 bucket for 40GB+ reference databases (Bakta/AMRFinder) protected by Terraform `prevent_destroy` hooks.
- Compute Tier: Ephemeral S3 storage for intermediate files with an automated 7-day Lifecycle Deletion Policy to minimize costs.

**Instant-Start Execution:**
Utilizes Nextflow Fusion FS to stream data directly from S3 into containers, eliminating the 20-minute "data staging" delay typical in AWS Batch.

**Dual-Queue Compute Strategy:**
- EC2 Spot queue for short-lived jobs (FASTP, BAKTA, AMRFinder) — up to 70-90% cost savings.
- On-Demand EC2 queue for long-running assemblers (Unicycler, Flye, Medaka) — prevents costly Spot interruptions mid-assembly that would restart a 2+ hour job from scratch.

---

## 🏗️ The Pipeline Architecture

The workflow follows a modular design, ensuring each sample receives the optimal assembly logic based on its read type.

### 1. Preprocessing & Quality Control
- **Illumina:** FastP for adapter trimming and base correction.
- **Nanopore:** Filtlong for length-weighting and quality filtering.

### 2. Assembly Strategy
- **Short-Read Only:** Unicycler (Conservative Mode) for high-accuracy scaffolds.
- **Long-Read Only:** Flye followed by Medaka consensus polishing.
- **Hybrid (Gold Standard):** Unicycler uses short-reads to resolve the accuracy of long-read graphs, producing closed circularized chromosomes.

### 3. Polishing & Refinement
- **Pypolca & Polypolish:** Uses Illumina data to fix remaining indel errors in long-read sequences.
- **Dnaapler:** Automated reorientation of circular contigs to the dnaA start gene.

### 4. Annotation & AMR Profiling
- **Bakta:** Rapid functional annotation (tRNAs, tmRNAs, CDS).
- **AMRFinderPlus:** High-sensitivity resistance detection categorized by a Clinical Interpretive Layer:
  - 🚨 **CRITICAL:** Carbapenemases (blaNDM, blaKPC) and Colistin resistance (mcr).
  - ⚠️ **HIGH:** MRSA markers (mecA) and Vancomycin resistance (vanA/B).
  - 🧬 **GENE:** All other identified resistance determinants from the NCBI database.

---

## 🚀 Quick Start

### Prerequisites
- AWS Account with CLI configured.
- Nextflow (v23.04+)
- Python 3.10+
- Terraform (for infrastructure deployment).

### The Complete Setup Guide

#### Step 1: Infrastructure (Terraform)
Navigate to your terraform folder to build the AWS environment:

```bash
cd terraform
terraform init
terraform apply -auto-approve
```

Note: Once finished, Terraform will output the ARNs for your S3 Bucket, Batch Queues, and IAM Roles.

#### Step 2: Database Seeding (One-Time)
Sync your local reference databases to the Static S3 bucket:

```bash
aws s3 sync ./bakta_db/ s3://amr-flow-static-assets/databases/bakta_db/
aws s3 sync ./amr_db/   s3://amr-flow-static-assets/databases/amr_db/
```

#### Step 3: Seqera Platform Token
To use the Wave container service, users must generate an access token. This allows Nextflow to provision the exact software environments needed for each tool on the fly.

1. Go to [Seqera Platform](https://cloud.seqera.io).
2. Log in and navigate to **Your Settings > Tokens**.
3. Click **Add Token**, name it (e.g., `NextAMR Token`), and copy the string.

#### Step 4: Authentication (.env)
Create a `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID="your_access_key"
AWS_SECRET_ACCESS_KEY="your_secret_key"
AWS_DEFAULT_REGION="us-east-1"

# Infrastructure ARNs (Generated via Terraform)
AMR_EC2_QUEUE="arn:aws:batch:..."
AMR_ONDEMAND_QUEUE="arn:aws:batch:..."
AMR_STATIC_BUCKET="amr-flow-storage-xxxx-static"
AMR_COMPUTE_BUCKET="amr-flow-storage-xxxx-compute"
AMR_JOB_ROLE_ARN="arn:aws:iam::..."
AMR_SUBNETS="subnet-xxxx,subnet-yyyy"
AMR_SECURITY_GROUPS="sg-zzzz"
TOWER_ACCESS_TOKEN=""
```

#### Step 5: Local Environment
```bash
pip install -r requirements.txt
```

#### Step 6: Running the Pipeline
Start the UI:
```bash
streamlit run ui/app.py
```
Upload & Launch: Use the tabs in the browser to push your data and fire off the AWS Batch jobs.

---

## Step 7: Tearing Down the Infrastructure

To stop compute costs but keep your large reference databases:

```bash
cd terraform
terraform destroy -target=aws_batch_job_queue.amr_ec2_queue \
                  -target=aws_batch_job_queue.amr_ondemand_queue \
                  -target=aws_batch_compute_environment.amr_ec2_compute \
                  -target=aws_batch_compute_environment.amr_ondemand_compute \
                  -target=aws_s3_bucket.amr_compute_storage
```

> **Note:** The Static Bucket is protected by `prevent_destroy`. This ensures you don't lose your 40GB+ Bakta and AMRFinder databases. If you truly wish to delete everything, you must manually disable this protection in `main.tf` first.

### Redeploying:
```bash
cd terraform
terraform apply -auto-approve
```

---

## 📁 Full Project Directory

```
NextAMR/
├── .env                  # EXCLUDED FROM GIT: Contains AWS Keys & ARNs
├── .env.example          # Template for environment-based secrets
├── nextflow/
│   ├── modules/          # Atomic, reusable tool wrappers
│   ├── subworkflows/     # Logical groupings (e.g., Assembly vs Annotation)
│   ├── main.nf           # DSL2 workflow entry point
│   └── nextflow.config   # Multi-profile cloud configuration
├── ui/                   # Streamlit "Control Plane"
│   ├── app.py            # Dashboard entry point
│   ├── generator.py      # High-capacity S3 ingestion
│   ├── validator.py      # Pre-flight integrity guardrails
│   ├── runner.py         # Subprocess orchestrator
│   └── reporter.py       # Clinical insight & enrichment dashboard
├── terraform/            # Infrastructure as Code (IaC)
│   ├── main.tf           # Two-tier S3 & Batch Environments
│   ├── variables.tf      # Parameterized infra
│   └── outputs.tf        # Automated .env generation logic
└── .streamlit/
    └── config.toml
```

---

## 🔧 Troubleshooting

**Resume a failed run:** If the pipeline is interrupted, check the "Resume" box in the UI. Nextflow will skip finished steps using the S3 `work/` directory.

**Assembler interrupted mid-run:** Unicycler, Flye, and Medaka run on the On-Demand queue and will not be interrupted by Spot reclamation. If a job fails, rerun with `-resume` — Nextflow will skip completed steps.
