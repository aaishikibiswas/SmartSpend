# This random ID helps us create a globally unique S3 bucket name.
resource "random_id" "s3_suffix" {
  byte_length = 4
}

# This S3 bucket can store uploaded statements, reports, or project artifacts.
# S3 bucket names must be globally unique across all AWS accounts.
resource "aws_s3_bucket" "smartspend_assets" {
  bucket = "${var.project_name}-assets-${random_id.s3_suffix.hex}"

  tags = {
    Name        = "${var.project_name}-assets"
    Project     = var.project_name
    Environment = "student-project"
    Purpose     = "SmartSpend file storage"
  }
}

# This keeps the bucket private by default, which is the safer default.
resource "aws_s3_bucket_public_access_block" "smartspend_assets" {
  bucket = aws_s3_bucket.smartspend_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
