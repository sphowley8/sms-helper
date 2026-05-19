terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  profile = "prod"
  region  = var.region
}

# ---------------------------------------------------------------------------
# Lambda packaging
# ---------------------------------------------------------------------------
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda"
  output_path = "${path.module}/lambda.zip"
  excludes    = ["__pycache__", "*.pyc"]
}

# ---------------------------------------------------------------------------
# Lambda function
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "sms_notes" {
  function_name    = "sms-notes-helper"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      GITHUB_TOKEN      = var.github_token
      AUTHORIZED_PHONE  = var.authorized_phone
      TWILIO_AUTH_TOKEN = var.twilio_auth_token
    }
  }
}

# ---------------------------------------------------------------------------
# API Gateway v2 (HTTP API) — public endpoint for Twilio webhook
# ---------------------------------------------------------------------------
resource "aws_apigatewayv2_api" "sms_notes" {
  name          = "sms-notes-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "sms_notes" {
  api_id                 = aws_apigatewayv2_api.sms_notes.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.sms_notes.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "sms_notes" {
  api_id    = aws_apigatewayv2_api.sms_notes.id
  route_key = "POST /"
  target    = "integrations/${aws_apigatewayv2_integration.sms_notes.id}"
}

resource "aws_apigatewayv2_stage" "sms_notes" {
  api_id      = aws_apigatewayv2_api.sms_notes.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sms_notes.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.sms_notes.execution_arn}/*/*"
}
