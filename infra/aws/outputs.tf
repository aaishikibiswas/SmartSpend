output "public_ip" {
  value       = aws_instance.app.public_ip
  description = "Public IP of the SmartSpend EC2 instance."
}

output "frontend_url" {
  value       = "http://${aws_instance.app.public_ip}"
  description = "Frontend URL after deployment."
}

output "backend_health_url" {
  value       = "http://${aws_instance.app.public_ip}:8001/health"
  description = "Backend health endpoint."
}


# This output shows the generated S3 bucket name.
output "s3_bucket_name" {
  value       = aws_s3_bucket.smartspend_assets.bucket
  description = "Name of the SmartSpend S3 bucket."
}

# This output shows the RDS endpoint you can use in the app later.
output "rds_endpoint" {
  value       = aws_db_instance.smartspend_db.endpoint
  description = "Endpoint of the SmartSpend MySQL RDS instance."
}

output "ebs_volume_id" {
  value       = aws_ebs_volume.app_data.id
  description = "ID of the extra EBS data volume."
}

output "cloudwatch_dashboard_name" {
  value       = aws_cloudwatch_dashboard.smartspend_ops.dashboard_name
  description = "CloudWatch dashboard name for SmartSpend operations."
}

output "cloudwatch_cpu_alarm_name" {
  value       = aws_cloudwatch_metric_alarm.high_cpu.alarm_name
  description = "CloudWatch alarm name for high CPU."
}

output "cloudwatch_status_alarm_name" {
  value       = aws_cloudwatch_metric_alarm.status_check_failed.alarm_name
  description = "CloudWatch alarm name for EC2 status check failures."
}

output "impl2_cloudfront_domain" {
  value       = var.enable_implementation2 ? aws_cloudfront_distribution.impl2[0].domain_name : null
  description = "CloudFront domain for Implementation 2 serverless frontend."
}

output "impl2_s3_static_website_url" {
  value       = var.enable_implementation2 ? "http://${aws_s3_bucket_website_configuration.impl2_frontend[0].website_endpoint}" : null
  description = "Public S3 static website endpoint for Implementation 2 frontend bucket."
}

output "impl2_api_gateway_url" {
  value       = var.enable_implementation2 ? aws_apigatewayv2_api.impl2_http[0].api_endpoint : null
  description = "API Gateway HTTP API endpoint for Implementation 2 Lambda backend."
}

output "impl2_lambda_name" {
  value       = var.enable_implementation2 ? aws_lambda_function.impl2_api[0].function_name : null
  description = "Lambda function name used by Implementation 2."
}

output "impl2_dynamodb_table" {
  value       = var.enable_implementation2 ? aws_dynamodb_table.impl2_sessions[0].name : null
  description = "DynamoDB table used for Implementation 2 session storage."
}

output "impl2_ecs_cluster_name" {
  value       = var.enable_implementation2 ? aws_ecs_cluster.impl2[0].name : null
  description = "ECS cluster name for Implementation 2 container path."
}

output "impl2_aurora_endpoint" {
  value       = var.enable_implementation2 && var.enable_aurora_serverless ? aws_rds_cluster.impl2_aurora[0].endpoint : null
  description = "Aurora Serverless endpoint (optional) for Implementation 2."
}

output "scalability_alb_dns" {
  value       = var.enable_scalability_stack ? aws_lb.smartspend[0].dns_name : null
  description = "Public DNS of ALB used for scalability demonstration."
}

output "scalability_alb_url" {
  value       = var.enable_scalability_stack ? "http://${aws_lb.smartspend[0].dns_name}" : null
  description = "Public ALB URL for load balancing and auto scaling demo."
}

output "scalability_asg_name" {
  value       = var.enable_scalability_stack ? aws_autoscaling_group.smartspend[0].name : null
  description = "Auto Scaling Group name for SmartSpend scalable web tier."
}
