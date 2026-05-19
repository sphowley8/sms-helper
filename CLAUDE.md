# CLAUDE.md — Session Context

## What This Is
SMS → GitHub notes helper. User texts a command from their phone → AWS Pinpoint receives the SMS → publishes to SNS → triggers Lambda → Lambda parses the command and commits to a markdown file in a GitHub repo → Lambda sends a reply SMS via Pinpoint.

The core motivation: use the native SMS app (distraction-free) as a quick capture tool instead of opening other apps.

## Architecture
```
Your phone
    │ SMS
    ▼
Amazon Pinpoint (toll-free number)
    │ publishes inbound SMS event
    ▼
SNS Topic: sms-notes-inbound
    │ triggers
    ▼
Lambda: sms-notes-helper
    ├── parses command
    ├── calls GitHub Contents API → commits to sphowley8/sean-brain (main)
    └── calls Pinpoint → sends SMS reply
```

## SMS Command Format
```
{function} {action}/{target} -{item1} -{item2} -{item3}
```
Example:
```
notes add/todo -water plants -safeway -send email
```
- `function`: `notes` (only MVP function; future: `calendar`, `strava`)
- `action`: `add` (future: `clean`, `get`)
- `target`: filename without `.md` extension (e.g., `todo` → `todo.md` in sean-brain repo)
- `items`: each prefixed with ` -`, parsed as markdown list items

## Key Design Decisions
- **Pinpoint not pure SNS**: AWS two-way SMS (inbound + outbound) requires Pinpoint for the phone number and SMS channel. SNS is used only as the event bus between Pinpoint and Lambda.
- **Toll-free number**: Chosen over 10DLC long code to avoid brand/campaign registration fees (~$10-15/month). Toll-free just needs a one-time verification form.
- **No external Python dependencies**: Lambda uses only stdlib (`urllib`, `base64`, `json`, `hmac`) + `boto3` (built into Lambda runtime). No packaging step needed beyond a simple zip.
- **Sender allowlist**: Lambda checks `AUTHORIZED_PHONE` env var and silently drops messages from any other number.
- **GitHub target**: `sphowley8/sean-brain`, branch `main`. Notes files stored at root as `{target}.md`.
- **Append with timestamp**: Each SMS append adds a UTC timestamp HTML comment above the new items so the file is human-readable and auditable without checking git history.

## Environment Variables (Lambda)
| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT with `repo` scope (write access to sphowley8/sean-brain) |
| `PINPOINT_APP_ID` | Pinpoint project/application ID (from Pinpoint console) |
| `PINPOINT_ORIGINATION_NUMBER` | Your toll-free number in E.164 format (e.g., `+18005551234`) |
| `AUTHORIZED_PHONE` | Your mobile number in E.164 format (e.g., `+15551234567`) |

## Repo Structure
```
sms-helper/
├── terraform/
│   ├── main.tf                   # Lambda, SNS topic, subscription, Lambda permission
│   ├── iam.tf                    # IAM role and policies
│   ├── variables.tf              # Input variable definitions
│   ├── outputs.tf                # SNS topic ARN, Lambda ARN
│   ├── terraform.tfvars.example  # Template — copy to terraform.tfvars
│   └── terraform.tfvars          # Secrets — gitignored
├── lambda/
│   ├── handler.py          # Lambda entrypoint; SNS event parsing; Pinpoint reply
│   ├── sms_parser.py       # Parses SMS body into {function, action, target, items}
│   └── github_client.py    # GitHub Contents API: get/create/append markdown files
├── .gitignore
├── CLAUDE.md               # This file — keep updated each session
├── README.md               # Full user-facing docs
├── TESTING.md              # Test TODO list and test documentation
└── manifest.md             # Original product spec — do not alter
```

## Infrastructure (Terraform-managed)
| Resource | Name/ID |
|----------|---------|
| Lambda function | `sms-notes-helper` |
| IAM role | `sms-notes-lambda-role` |
| SNS topic | `sms-notes-inbound` |
| Pinpoint project | Created manually (see README USAGE) |

Deploy: `cd terraform && terraform apply`
Destroy: `cd terraform && terraform destroy`

## Pinpoint Setup (Manual — One-Time)
1. AWS Console → Amazon Pinpoint → Create project
2. Enable SMS channel in project settings
3. Request a toll-free number under "Phone numbers"
4. Submit toll-free verification form (approval: 1–5 business days)
5. Enable two-way SMS on the number → set SNS topic to `sms-notes-inbound` ARN
6. Copy App ID and phone number → set as Lambda env vars

## Session Log
### Session 1 — 2026-04-30
- Initial build: MVP notes function (add action only)
- Stack: Pinpoint → SNS → Lambda → GitHub API → Pinpoint reply
- Files created: `lambda/handler.py`, `lambda/sms_parser.py`, `lambda/github_client.py`, `CLAUDE.md`, `README.md`, `TESTING.md`
- Decided against Twilio (user prefers centralized AWS billing); decided against 10DLC (toll-free simpler for single user)
- Restructured from `deploy.sh` to Terraform: `terraform/main.tf`, `iam.tf`, `variables.tf`, `outputs.tf`
- AWS profile: `prod` (account 527658263602), region `us-east-1`
- Lambda code packaged via Terraform `archive_file` data source — no manual zip step
- Moved from classic Pinpoint API to SMS Voice V2 (`aws_pinpointsmsvoicev2_phone_number`): no Pinpoint project needed, phone number provisions via Terraform, two-way SMS wired to SNS automatically
- Lambda handler updated: `boto3.client('pinpoint-sms-voice-v2')` + `send_text_message`, `PINPOINT_APP_ID` removed
- IAM policy updated: `mobiletargeting:SendMessages` → `sms-voice:SendTextMessage`
- SNS topic policy added: allows `sms-voice.amazonaws.com` to publish inbound SMS events
- Deployment is now fully automated — no manual console steps, no waiting period
- Switched from AWS SMS Voice V2 to Twilio: toll-free number stuck in Pending/registration rejected
- SNS topic removed entirely — Twilio POSTs directly to Lambda Function URL
- Lambda handler rewrote: Twilio webhook format (form-encoded POST), TwiML reply, HMAC-SHA1 signature validation
- IAM SMS send policy removed (no longer needed — reply is TwiML, not an outbound API call)
- New env vars: `TWILIO_AUTH_TOKEN` (replaces `PINPOINT_ORIGINATION_NUMBER`)
- New Terraform resource: `aws_lambda_function_url` (public HTTPS endpoint for Twilio webhook)
- `pinpoint.tf` deleted
- test_sms.py updated: builds Twilio-format Lambda Function URL event, mocks signature validation
