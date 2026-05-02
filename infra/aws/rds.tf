# This extra public subnet is added only to satisfy the RDS requirement
# that a DB subnet group must span at least 2 Availability Zones.
resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.smartspend.id
  cidr_block              = "10.20.2.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}b"

  tags = {
    Name        = "${var.project_name}-public-b"
    Project     = var.project_name
    Environment = "student-project"
  }
}

# This associates the second subnet with the existing public route table.
resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# This subnet group tells RDS which subnets it can use.
# We are keeping it simple and using the existing public subnet for this student project.
resource "aws_db_subnet_group" "smartspend_rds_subnet_group" {
  name       = "${var.project_name}-rds-subnet-group"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name        = "${var.project_name}-rds-subnet-group"
    Project     = var.project_name
    Environment = "student-project"
  }
}

# This security group allows MySQL access to the RDS database.
# For simplicity, it is open publicly. For real production, this should be restricted.
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Allow MySQL traffic for SmartSpend RDS"
  vpc_id      = aws_vpc.smartspend.id

  ingress {
    from_port   = 3306
    to_port     = 3306
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
    Name        = "${var.project_name}-rds-sg"
    Project     = var.project_name
    Environment = "student-project"
  }
}

# This is a free-tier-style MySQL database for SmartSpend.
# Use simple credentials first, then change them later if needed.
resource "aws_db_instance" "smartspend_db" {
  identifier              = "${var.project_name}-db"
  allocated_storage       = 20
  engine                  = "mysql"
  engine_version          = "8.0"
  instance_class          = "db.t3.micro"
  db_name                 = "smartspend"
  username                = "adminuser"
  password                = "SmartSpend123!"
  db_subnet_group_name    = aws_db_subnet_group.smartspend_rds_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  publicly_accessible     = true
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 0
  multi_az                = false

  tags = {
    Name        = "${var.project_name}-db"
    Project     = var.project_name
    Environment = "student-project"
    Purpose     = "SmartSpend MySQL database"
  }
}
