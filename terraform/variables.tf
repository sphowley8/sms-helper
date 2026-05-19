variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "github_token" {
  description = "GitHub Personal Access Token with repo write scope on sphowley8/sean-brain"
  type        = string
  sensitive   = true
}

variable "authorized_phone" {
  description = "Your mobile number in E.164 format — only messages from this number are processed"
  type        = string
  sensitive   = true
}

variable "twilio_auth_token" {
  description = "Twilio Auth Token — used to validate inbound webhook signatures"
  type        = string
  sensitive   = true
}
