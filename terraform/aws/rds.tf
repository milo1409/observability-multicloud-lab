resource "random_password" "db" {
  count   = var.enable_rds ? 1 : 0
  length  = 24
  special = true
}

resource "aws_db_subnet_group" "main" {
  count = var.enable_rds ? 1 : 0

  name = "${var.project_name}-db-subnets"
  subnet_ids = [
    aws_subnet.private_a[0].id,
    aws_subnet.private_b[0].id
  ]
}

resource "aws_db_instance" "postgres" {
  count = var.enable_rds ? 1 : 0

  identifier = "${var.project_name}-postgres"

  engine         = "postgres"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 20
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db[0].result

  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  vpc_security_group_ids = [aws_security_group.rds[0].id]

  publicly_accessible = false
  multi_az            = false

  backup_retention_period = 0
  skip_final_snapshot      = true
  deletion_protection      = false

  apply_immediately = true
}
