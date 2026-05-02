# ------------------------------------------------------------
# Advanced AWS Services for CA requirement (simple + safe)
# ------------------------------------------------------------

# Extra EBS volume (advanced service: AWS EBS)
# This gives a dedicated data disk for app artifacts/backups.
resource "aws_ebs_volume" "app_data" {
  availability_zone = aws_instance.app.availability_zone
  size              = var.ebs_data_volume_size
  type              = "gp3"

  tags = {
    Name        = "${var.project_name}-data-ebs"
    Project     = var.project_name
    Environment = "student-project"
    Purpose     = "Extra application data volume"
  }
}

# Attaches the EBS volume to the EC2 instance.
resource "aws_volume_attachment" "app_data_attach" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.app_data.id
  instance_id = aws_instance.app.id
}

# CloudWatch dashboard (advanced service: CloudWatch)
# Shows core EC2 health/performance metrics for presentation and monitoring.
resource "aws_cloudwatch_dashboard" "smartspend_ops" {
  dashboard_name = "${var.project_name}-ops-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "EC2 CPU Utilization"
          region = var.aws_region
          stat   = "Average"
          period = 300
          metrics = [
            ["AWS/EC2", "CPUUtilization", "InstanceId", aws_instance.app.id]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "EC2 Status Checks"
          region = var.aws_region
          stat   = "Maximum"
          period = 300
          metrics = [
            ["AWS/EC2", "StatusCheckFailed", "InstanceId", aws_instance.app.id]
          ]
        }
      }
    ]
  })
}

# Alarm when CPU is high for sustained duration.
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.project_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 75
  alarm_description   = "Alarm if EC2 CPU stays high for 10 minutes."
  dimensions = {
    InstanceId = aws_instance.app.id
  }
}

# Alarm when instance reachability checks fail.
resource "aws_cloudwatch_metric_alarm" "status_check_failed" {
  alarm_name          = "${var.project_name}-status-check-failed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Maximum"
  threshold           = 1
  alarm_description   = "Alarm if EC2 status checks fail."
  dimensions = {
    InstanceId = aws_instance.app.id
  }
}
