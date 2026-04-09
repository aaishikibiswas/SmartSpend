output "public_ip" {
  value       = aws_instance.app.public_ip
  description = "Public IP of the SmartSpend EC2 instance."
}

output "frontend_url" {
  value       = "http://${aws_instance.app.public_ip}:3001"
  description = "Frontend URL after deployment."
}

output "backend_health_url" {
  value       = "http://${aws_instance.app.public_ip}:8001/health"
  description = "Backend health endpoint."
}
