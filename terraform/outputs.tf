output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.sms_notes.function_name
}

output "lambda_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.sms_notes.arn
}

output "webhook_url" {
  description = "Paste this as the webhook URL in your Twilio number settings"
  value       = aws_apigatewayv2_stage.sms_notes.invoke_url
}
