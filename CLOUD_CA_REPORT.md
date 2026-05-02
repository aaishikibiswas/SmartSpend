# SmartSpend AWS Cloud Architecture Report
## INT330 - Managing Cloud Solutions (CA 2)

## 1. Project Title
**SmartSpend: Design and Deployment of a Scalable AWS-Based AI Financial Analytics Platform**

## 2. Scenario
SmartSpend is an AI-powered personal finance platform that processes uploaded statements, predicts spending, shows recurring liabilities, and provides intelligent financial guidance.  
The platform must stay available under variable user activity, keep data secure, and remain cost-effective for student-level cloud deployment.

## 3. Problem Statement
Design and deploy a simple AWS architecture for SmartSpend that demonstrates:
- cloud-based compute, storage, database, networking, and security,
- scalable and reliable operation,
- monitoring and operational visibility,
- cost-aware deployment suitable for a student project.

## 4. Objectives
1. Deploy SmartSpend using core AWS services (EC2, S3, IAM, VPC, RDS).
2. Integrate at least two advanced AWS services from the CA list.
3. Ensure secure access controls and network-level isolation.
4. Provide monitoring support for performance and reliability.
5. Keep the architecture simple, understandable, and budget-conscious.

## 5. Implemented AWS Services

### 5.1 Basic Services (Required)
- **Amazon EC2**: Hosts SmartSpend frontend and backend.
- **Amazon S3**: Stores project assets/uploads (bucket provisioned and secured).
- **AWS IAM**: EC2 role + instance profile for controlled AWS access.
- **AWS VPC**: Isolated network with public subnets, route table, internet gateway.
- **Amazon RDS (MySQL)**: Managed relational database endpoint for persistent data.

### 5.2 Advanced Services (At least two)
- **Amazon CloudWatch**:
  - Operational dashboard for CPU and health metrics.
  - High-CPU alarm.
  - Instance status-check failure alarm.
- **AWS EBS**:
  - Additional dedicated gp3 EBS data volume attached to EC2.

## 6. Architecture Summary
- A VPC contains public subnets and routing via internet gateway.
- EC2 instance serves the web application.
- RDS MySQL provides managed database capability.
- S3 provides object storage.
- IAM instance profile grants EC2 secure access to AWS APIs.
- CloudWatch dashboard and alarms provide observability.
- EBS adds data volume separation from root disk.

## 7. Terraform Implementation Files
- `infra/aws/main.tf` -> VPC, subnet, route table, SG, EC2
- `infra/aws/s3.tf` -> S3 + public access block
- `infra/aws/iam.tf` -> IAM role + profile
- `infra/aws/rds.tf` -> RDS + DB subnet group + DB SG
- `infra/aws/advanced.tf` -> EBS + CloudWatch dashboard + alarms
- `infra/aws/outputs.tf` -> public URLs and cloud resource outputs
- `infra/aws/variables.tf` -> configurable project parameters
- `infra/aws/versions.tf` -> provider versions

## 8. Deployment Steps (Executed)
1. Configure AWS CLI credentials.
2. Run Terraform:
   - `terraform init`
   - `terraform apply`
3. Provisioned resources were created in AWS account.
4. EC2 deployment was completed and services were started via systemd.
5. Production troubleshooting was performed (OOM/reachability/import mismatch issues).
6. Final verification done through live endpoint checks.

## 9. Final Deployment Status
- **Application URL**: `http://13.126.236.250`
- **Frontend health**: `http://13.126.236.250/api/health`
- **Backend health (internal)**: `http://127.0.0.1:8001/health` from EC2 host

## 10. Rubric Mapping

### 10.1 Scalability (15)
- EC2 size chosen for low-cost baseline.
- App supports modular evolution to ASG/ELB path.
- Heavy tasks handled with controlled resource strategy (swap + tuned build/runtime).

### 10.2 Availability (15)
- EC2 service managed by `systemd` with auto-restart.
- Route health and service health endpoints tested.
- Recovery operations executed (instance reboot/stop-start and service restart procedures).

### 10.3 Security Measures (10)
- IAM role-based access for EC2 (no hardcoded cloud credentials in app runtime).
- Security groups control inbound ports.
- S3 public access blocked by default.
- Temporary wide SSH access used only during debugging and revoked immediately.

### 10.4 Performance (10)
- Production build served through optimized Next.js output.
- Backend served through FastAPI/Uvicorn.
- Upload and dashboard APIs validated with real data.
- CloudWatch CPU metric visualization and alarm for pressure detection.

### 10.5 Monitoring and Cost Management (10)
- CloudWatch dashboard for operational visibility.
- CloudWatch alarms for CPU and status failure.
- Cost-conscious choices:
  - `t3.micro` EC2
  - `db.t3.micro` RDS
  - modest EBS sizing
  - simple architecture without unnecessary premium services

### 10.6 Documentation (15)
- This report documents architecture, services, deployment, and rubric linkage.
- Terraform files are commented for beginner understanding.

### 10.7 Presentation (25)
- Architecture can be presented as:
  1. Problem + requirements
  2. AWS service mapping
  3. Deployment workflow
  4. Live verification
  5. Rubric-aligned outcomes

## 11. Issues Encountered and Fixes
- **Instance reachability/health impairment** -> recovered with stop/start.
- **Build OOM on EC2** -> added swap and tuned build path.
- **API 404 cascade** -> fixed backend import mismatch and restarted service.
- **Feature drift between local and cloud** -> synced latest frontend/backend modules and rebuilt.
- **Temporary SSH exposure during recovery** -> revoked after completion.

## 12. Screenshots Checklist (for report submission)
- EC2 instance details
- VPC and subnet view
- Security group rules
- IAM role + instance profile
- S3 bucket details
- RDS instance and endpoint
- CloudWatch dashboard
- CloudWatch alarms
- Terraform apply success output
- Live SmartSpend app URL and health endpoint

## 13. Conclusion
SmartSpend now satisfies the CA architecture requirement with required basic services and at least two advanced services integrated, while remaining simple, demonstrable, and cost-aware.  
The deployment is live, monitored, and documented, with clear evidence for evaluation across scalability, availability, security, performance, and operations.
