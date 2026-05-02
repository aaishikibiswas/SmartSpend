locals {
  impl2_enabled = var.enable_implementation2
}

# ------------------------------------------------------------
# Implementation 2: Serverless + Container-Based Architecture
# ------------------------------------------------------------

resource "random_id" "impl2_suffix" {
  count       = local.impl2_enabled ? 1 : 0
  byte_length = 4
}

# S3 bucket for static frontend (serverless path)
resource "aws_s3_bucket" "impl2_frontend" {
  count  = local.impl2_enabled ? 1 : 0
  bucket = "${var.project_name}-impl2-frontend-${random_id.impl2_suffix[0].hex}"

  tags = {
    Name        = "${var.project_name}-impl2-frontend"
    Project     = var.project_name
    Environment = "student-project"
    Pattern     = "implementation2"
  }
}

resource "aws_s3_bucket_public_access_block" "impl2_frontend" {
  count  = local.impl2_enabled ? 1 : 0
  bucket = aws_s3_bucket.impl2_frontend[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "impl2_frontend" {
  count  = local.impl2_enabled ? 1 : 0
  bucket = aws_s3_bucket.impl2_frontend[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_website_configuration" "impl2_frontend" {
  count  = local.impl2_enabled ? 1 : 0
  bucket = aws_s3_bucket.impl2_frontend[0].id

  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_object" "impl2_index" {
  count        = local.impl2_enabled ? 1 : 0
  bucket       = aws_s3_bucket.impl2_frontend[0].id
  key          = "index.html"
  source       = "${path.module}/${var.serverless_frontend_index_file}"
  etag         = filemd5("${path.module}/${var.serverless_frontend_index_file}")
  content_type = "text/html"
}

# DynamoDB session store
resource "aws_dynamodb_table" "impl2_sessions" {
  count        = local.impl2_enabled ? 1 : 0
  name         = "${var.project_name}-impl2-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-impl2-sessions"
    Project     = var.project_name
    Environment = "student-project"
    Pattern     = "implementation2"
  }
}

# Lambda execution role
data "aws_iam_policy_document" "impl2_lambda_assume" {
  count = local.impl2_enabled ? 1 : 0

  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "impl2_lambda_exec" {
  count              = local.impl2_enabled ? 1 : 0
  name               = "${var.project_name}-impl2-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.impl2_lambda_assume[0].json

  tags = {
    Name        = "${var.project_name}-impl2-lambda-role"
    Project     = var.project_name
    Environment = "student-project"
  }
}

resource "aws_iam_role_policy_attachment" "impl2_lambda_basic" {
  count      = local.impl2_enabled ? 1 : 0
  role       = aws_iam_role.impl2_lambda_exec[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "impl2_lambda_dynamodb" {
  count = local.impl2_enabled ? 1 : 0

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [aws_dynamodb_table.impl2_sessions[0].arn]
  }
}

resource "aws_iam_role_policy" "impl2_lambda_dynamodb" {
  count  = local.impl2_enabled ? 1 : 0
  name   = "${var.project_name}-impl2-lambda-dynamodb"
  role   = aws_iam_role.impl2_lambda_exec[0].id
  policy = data.aws_iam_policy_document.impl2_lambda_dynamodb[0].json
}

data "archive_file" "impl2_lambda_zip" {
  count       = local.impl2_enabled ? 1 : 0
  type        = "zip"
  source_file = "${path.module}/lambda/session_handler.py"
  output_path = "${path.module}/lambda/session_handler.zip"
}

resource "aws_lambda_function" "impl2_api" {
  count            = local.impl2_enabled ? 1 : 0
  function_name    = "${var.project_name}-impl2-session-api"
  role             = aws_iam_role.impl2_lambda_exec[0].arn
  handler          = "session_handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.impl2_lambda_zip[0].output_path
  source_code_hash = data.archive_file.impl2_lambda_zip[0].output_base64sha256
  timeout          = 15
  memory_size      = 256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.impl2_sessions[0].name
    }
  }

  tags = {
    Name        = "${var.project_name}-impl2-session-api"
    Project     = var.project_name
    Environment = "student-project"
    Pattern     = "implementation2"
  }
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "impl2_http" {
  count         = local.impl2_enabled ? 1 : 0
  name          = "${var.project_name}-impl2-http"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "impl2_lambda" {
  count                  = local.impl2_enabled ? 1 : 0
  api_id                 = aws_apigatewayv2_api.impl2_http[0].id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.impl2_api[0].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "impl2_proxy" {
  count     = local.impl2_enabled ? 1 : 0
  api_id    = aws_apigatewayv2_api.impl2_http[0].id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.impl2_lambda[0].id}"
}

resource "aws_apigatewayv2_route" "impl2_root" {
  count     = local.impl2_enabled ? 1 : 0
  api_id    = aws_apigatewayv2_api.impl2_http[0].id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.impl2_lambda[0].id}"
}

resource "aws_apigatewayv2_stage" "impl2_default" {
  count       = local.impl2_enabled ? 1 : 0
  api_id      = aws_apigatewayv2_api.impl2_http[0].id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "impl2_apigw_invoke" {
  count         = local.impl2_enabled ? 1 : 0
  statement_id  = "AllowHttpApiInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.impl2_api[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.impl2_http[0].execution_arn}/*/*"
}

# CloudFront: S3 frontend + API Gateway path routing
resource "aws_cloudfront_origin_access_control" "impl2_oac" {
  count                             = local.impl2_enabled ? 1 : 0
  name                              = "${var.project_name}-impl2-oac"
  description                       = "OAC for SmartSpend serverless frontend bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "impl2" {
  count   = local.impl2_enabled ? 1 : 0
  enabled = true

  origin {
    domain_name              = aws_s3_bucket.impl2_frontend[0].bucket_regional_domain_name
    origin_id                = "s3-impl2-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.impl2_oac[0].id
  }

  origin {
    domain_name = replace(aws_apigatewayv2_api.impl2_http[0].api_endpoint, "https://", "")
    origin_id   = "apigw-impl2"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_root_object = "index.html"

  default_cache_behavior {
    target_origin_id       = "s3-impl2-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "apigw-impl2"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type"]
      cookies {
        forward = "all"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  price_class = "PriceClass_100"

  tags = {
    Name        = "${var.project_name}-impl2-cloudfront"
    Project     = var.project_name
    Environment = "student-project"
    Pattern     = "implementation2"
  }
}

data "aws_iam_policy_document" "impl2_frontend_bucket_policy" {
  count = local.impl2_enabled ? 1 : 0

  statement {
    sid     = "AllowCloudFrontRead"
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.impl2_frontend[0].arn}/*"
    ]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.impl2[0].arn]
    }
  }
}

resource "aws_s3_bucket_policy" "impl2_frontend" {
  count  = local.impl2_enabled ? 1 : 0
  bucket = aws_s3_bucket.impl2_frontend[0].id
  policy = data.aws_iam_policy_document.impl2_frontend_bucket_policy[0].json
}

# ECS/Fargate container path (service intentionally starts with 0 tasks for cost control)
resource "aws_ecs_cluster" "impl2" {
  count = local.impl2_enabled ? 1 : 0
  name  = "${var.project_name}-impl2-cluster"

  tags = {
    Name        = "${var.project_name}-impl2-cluster"
    Project     = var.project_name
    Environment = "student-project"
    Pattern     = "implementation2"
  }
}

data "aws_iam_policy_document" "impl2_ecs_task_assume" {
  count = local.impl2_enabled ? 1 : 0

  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "impl2_ecs_execution" {
  count              = local.impl2_enabled ? 1 : 0
  name               = "${var.project_name}-impl2-ecs-exec-role"
  assume_role_policy = data.aws_iam_policy_document.impl2_ecs_task_assume[0].json
}

resource "aws_iam_role_policy_attachment" "impl2_ecs_exec_policy" {
  count      = local.impl2_enabled ? 1 : 0
  role       = aws_iam_role.impl2_ecs_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_security_group" "impl2_ecs" {
  count       = local.impl2_enabled ? 1 : 0
  name        = "${var.project_name}-impl2-ecs-sg"
  description = "Security group for Implementation 2 ECS service."
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
}

resource "aws_ecs_task_definition" "impl2" {
  count                    = local.impl2_enabled ? 1 : 0
  family                   = "${var.project_name}-impl2-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.impl2_ecs_execution[0].arn

  container_definitions = jsonencode([
    {
      name      = "smartspend-impl2-microservice"
      image     = "public.ecr.aws/docker/library/nginx:stable-alpine"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
    }
  ])
}

resource "aws_ecs_service" "impl2" {
  count           = local.impl2_enabled ? 1 : 0
  name            = "${var.project_name}-impl2-service"
  cluster         = aws_ecs_cluster.impl2[0].id
  task_definition = aws_ecs_task_definition.impl2[0].arn
  desired_count   = 0
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.impl2_ecs[0].id]
    assign_public_ip = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}

# Optional Aurora Serverless v2
resource "aws_rds_cluster" "impl2_aurora" {
  count                        = local.impl2_enabled && var.enable_aurora_serverless ? 1 : 0
  cluster_identifier           = "${var.project_name}-impl2-aurora"
  engine                       = "aurora-mysql"
  engine_version               = "8.0.mysql_aurora.3.07.1"
  database_name                = "smartspendaurora"
  master_username              = "adminuser"
  master_password              = "SmartSpend123!"
  db_subnet_group_name         = aws_db_subnet_group.smartspend_rds_subnet_group.name
  vpc_security_group_ids       = [aws_security_group.rds.id]
  skip_final_snapshot          = true
  storage_encrypted            = true
  backup_retention_period      = 1
  deletion_protection          = false
  preferred_backup_window      = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 1.0
  }
}

resource "aws_rds_cluster_instance" "impl2_aurora_writer" {
  count              = local.impl2_enabled && var.enable_aurora_serverless ? 1 : 0
  identifier         = "${var.project_name}-impl2-aurora-writer"
  cluster_identifier = aws_rds_cluster.impl2_aurora[0].id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.impl2_aurora[0].engine
  engine_version     = aws_rds_cluster.impl2_aurora[0].engine_version
}
