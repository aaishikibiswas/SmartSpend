locals {
  scalability_enabled = var.enable_scalability_stack
}

# Security group for the public Application Load Balancer.
resource "aws_security_group" "alb" {
  count       = local.scalability_enabled ? 1 : 0
  name        = "${var.project_name}-alb-sg"
  description = "Allow public HTTP traffic to SmartSpend ALB."
  vpc_id      = aws_vpc.smartspend.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-alb-sg"
    Project     = var.project_name
    Environment = "student-project"
    Purpose     = "ALB ingress"
  }
}

# Security group for EC2 instances launched by Auto Scaling Group.
resource "aws_security_group" "asg_instances" {
  count       = local.scalability_enabled ? 1 : 0
  name        = "${var.project_name}-asg-sg"
  description = "Allow traffic from ALB to Auto Scaling instances."
  vpc_id      = aws_vpc.smartspend.id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb[0].id]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-asg-sg"
    Project     = var.project_name
    Environment = "student-project"
    Purpose     = "ASG web tier ingress"
  }
}

# Public ALB across two subnets for higher availability.
resource "aws_lb" "smartspend" {
  count              = local.scalability_enabled ? 1 : 0
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name        = "${var.project_name}-alb"
    Project     = var.project_name
    Environment = "student-project"
    Purpose     = "Load balancing"
  }
}

# Target group for ASG instances.
resource "aws_lb_target_group" "smartspend" {
  count       = local.scalability_enabled ? 1 : 0
  name        = "${var.project_name}-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.smartspend.id
  target_type = "instance"

  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.project_name}-tg"
    Project     = var.project_name
    Environment = "student-project"
    Purpose     = "ALB target group"
  }
}

# Listener forwards HTTP traffic to target group.
resource "aws_lb_listener" "http" {
  count             = local.scalability_enabled ? 1 : 0
  load_balancer_arn = aws_lb.smartspend[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.smartspend[0].arn
  }
}

# Launch template defines how ASG EC2 instances are created.
resource "aws_launch_template" "smartspend" {
  count         = local.scalability_enabled ? 1 : 0
  name_prefix   = "${var.project_name}-lt-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = var.asg_instance_type
  key_name      = var.key_name
  user_data     = base64encode(templatefile("${path.module}/user_data_asg.sh.tpl", {}))

  iam_instance_profile {
    name = aws_iam_instance_profile.smartspend_ec2_profile.name
  }

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.asg_instances[0].id]
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.project_name}-asg-instance"
      Project     = var.project_name
      Environment = "student-project"
      Purpose     = "Auto scaling web tier"
    }
  }
}

# Auto Scaling Group enables dynamic scaling during traffic spikes.
resource "aws_autoscaling_group" "smartspend" {
  count                     = local.scalability_enabled ? 1 : 0
  name                      = "${var.project_name}-asg"
  min_size                  = var.asg_min_size
  desired_capacity          = var.asg_desired_capacity
  max_size                  = var.asg_max_size
  health_check_type         = "ELB"
  health_check_grace_period = 180
  vpc_zone_identifier       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  target_group_arns         = [aws_lb_target_group.smartspend[0].arn]

  launch_template {
    id      = aws_launch_template.smartspend[0].id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-asg-instance"
    propagate_at_launch = true
  }
}

# Target tracking policy automatically scales based on average EC2 CPU.
resource "aws_autoscaling_policy" "cpu_target_tracking" {
  count                  = local.scalability_enabled ? 1 : 0
  name                   = "${var.project_name}-cpu-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.smartspend[0].name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 60.0
  }
}
