#!/bin/bash
set -euo pipefail

TERRAFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/terraform" && pwd)"

if [ ! -f "${TERRAFORM_DIR}/terraform.tfvars" ]; then
  echo "ERROR: terraform/terraform.tfvars not found."
  echo "       Copy terraform/terraform.tfvars.example and fill in your values."
  exit 1
fi

cd "${TERRAFORM_DIR}"

echo "==> Initializing Terraform..."
terraform init -upgrade -input=false

echo "==> Planning..."
terraform plan -input=false -out=tfplan

echo ""
read -r -p "Apply the plan above? [y/N] " confirm
if [[ ! "${confirm}" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  rm -f tfplan
  exit 0
fi

echo "==> Applying..."
terraform apply -input=false tfplan
rm -f tfplan

echo ""
echo "==> Deploy complete. Outputs:"
terraform output
