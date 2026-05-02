# This policy document allows EC2 to assume the IAM role.
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# This IAM role is attached to the EC2 instance.
# It allows the instance to use AWS services without storing credentials in code.
resource "aws_iam_role" "smartspend_ec2_role" {
  name               = "${var.project_name}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = {
    Name        = "${var.project_name}-ec2-role"
    Project     = var.project_name
    Environment = "student-project"
  }
}

# This attaches AmazonS3FullAccess to the EC2 role.
# It keeps the setup simple for a beginner project.
resource "aws_iam_role_policy_attachment" "smartspend_s3_access" {
  role       = aws_iam_role.smartspend_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# This instance profile is what EC2 actually uses to receive the IAM role.
resource "aws_iam_instance_profile" "smartspend_ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.smartspend_ec2_role.name
}
