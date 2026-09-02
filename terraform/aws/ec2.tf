data "aws_ami" "amazon_linux_2023" {
  count       = var.enable_ec2 ? 1 : 0
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_iam_role" "ec2_ssm" {
  count = var.enable_ec2 ? 1 : 0

  name = "${var.project_name}-ec2-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  count = var.enable_ec2 ? 1 : 0

  role       = aws_iam_role.ec2_ssm[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  count = var.enable_ec2 ? 1 : 0

  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_ssm[0].name
}

resource "aws_instance" "lab" {
  count = var.enable_ec2 ? 1 : 0

  ami                    = data.aws_ami.amazon_linux_2023[0].id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public_a.id
  vpc_security_group_ids = [aws_security_group.sandbox.id]

  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.ec2[0].name

  user_data = <<-EOF
    #!/bin/bash
    set -e
    dnf update -y
    dnf install -y docker git
    systemctl enable --now docker
    usermod -aG docker ec2-user

    mkdir -p /opt/observability
    chown ec2-user:ec2-user /opt/observability

    cat >/etc/motd <<'MOTD'
    Observability Multicloud Lab
    Docker installed.
    Use AWS Systems Manager Session Manager for administration.
    MOTD
  EOF

  root_block_device {
    volume_type = "gp3"
    volume_size = 10
    encrypted   = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name = "${var.project_name}-lab"
  }
}
