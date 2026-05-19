#!/bin/bash
set -euo pipefail

TERRAFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/terraform" && pwd)"

cd "${TERRAFORM_DIR}"

echo "==> This will destroy all Terraform-managed resources:"
echo "      - Lambda: sms-notes-helper"
echo "      - SNS topic: sms-notes-inbound"
echo "      - IAM role: sms-notes-lambda-role"
echo ""
echo "    NOTE: Pinpoint project and phone number must be released manually"
echo "          in the AWS console to stop the ~\$2/month charge."
echo ""
read -r -p "Destroy all resources? [y/N] " confirm
if [[ ! "${confirm}" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

echo "==> Destroying..."
terraform destroy -auto-approve

echo ""
echo "==> Teardown complete."
