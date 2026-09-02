output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_a" {
  value = aws_subnet.public_a.id
}

output "public_subnet_b" {
  value = aws_subnet.public_b.id
}

output "security_group_id" {
  value = aws_security_group.sandbox.id
}

output "ecr_service_a" {
  value = aws_ecr_repository.service_a.repository_url
}

output "ecr_service_b" {
  value = aws_ecr_repository.service_b.repository_url
}

output "ecr_data_service" {
  value = aws_ecr_repository.data_service.repository_url
}

output "rds_endpoint" {
  value = var.enable_rds ? aws_db_instance.postgres[0].address : "RDS disabled"
}

output "flow_log_group" {
  value = var.enable_flow_logs ? aws_cloudwatch_log_group.flow_logs[0].name : "Flow Logs disabled"
}

output "security_hub_enabled" {
  value = var.enable_security_hub
}


output "ec2_instance_id" {
  value = var.enable_ec2 ? aws_instance.lab[0].id : "EC2 disabled"
}

output "ec2_public_ip" {
  value = var.enable_ec2 ? aws_instance.lab[0].public_ip : "EC2 disabled"
}

output "ec2_public_dns" {
  value = var.enable_ec2 ? aws_instance.lab[0].public_dns : "EC2 disabled"
}
