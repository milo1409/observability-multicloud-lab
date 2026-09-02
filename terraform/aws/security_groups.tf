resource "aws_security_group" "sandbox" {
  name        = "${var.project_name}-sandbox-sg"
  description = "Low-cost sandbox security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP service-a sandbox"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = [var.service_a_allowed_cidr]
  }

  ingress {
    description = "service-b internal VPC"
    from_port   = 8002
    to_port     = 8002
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    description = "data-service internal VPC"
    from_port   = 8003
    to_port     = 8003
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  count  = var.enable_rds ? 1 : 0
  name   = "${var.project_name}-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.sandbox.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
