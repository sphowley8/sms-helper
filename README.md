# sms-helper

Text commands from your phone → AWS processes them → updates files in GitHub. No frontend, no database, single user.

---

## PURPOSE

Reduce time spent clicking through apps by routing quick capture tasks through the native SMS app. SMS is fast to open and doesn't create dopamine rabbit holes. This system lets you text structured commands that automatically file notes into a GitHub repository, with SMS confirmation on success or failure.

**MVP scope:** notes only — append markdown list items to files in `sphowley8/sean-brain`.

**Future scope:** retrieve notes, clean notes, create Strava activities, add calendar events.

---

## REPO STRUCTURE

```
sms-helper/
├── terraform/
│   ├── main.tf                   # Lambda function + Lambda Function URL
│   ├── iam.tf                    # IAM role (basic execution only)
│   ├── variables.tf              # Input variable definitions
│   ├── outputs.tf                # webhook_url — paste into Twilio console
│   ├── terraform.tfvars.example  # Copy → terraform.tfvars and fill in secrets
│   └── terraform.tfvars          # Your secrets — gitignored, never committed
├── lambda/
│   ├── handler.py                # Twilio webhook handler: validates signature, parses, replies via TwiML
│   ├── sms_parser.py             # Converts SMS body → {function, action, target, section, items}
│   └── github_client.py          # GitHub Contents API: get/create/append .md files
├── test_sms.py                   # Local test harness — simulates inbound SMS without Twilio
├── deploy.sh                     # terraform init → plan → apply
├── teardown.sh                   # terraform destroy
├── .gitignore
├── CLAUDE.md                     # AI session context — updated each session
├── README.md                     # This file
├── TESTING.md                    # Test TODO list and documentation
└── manifest.md                   # Original product spec — do not alter
```

---

## ARCHITECTURE

```
Your phone
    │  SMS text
    ▼
Twilio (phone number)
    │  POST webhook with form-encoded body
    ▼
AWS Lambda Function URL (public HTTPS endpoint)
    │
    ├─ validates Twilio HMAC-SHA1 signature
    ├─ validates sender == AUTHORIZED_PHONE
    ├─ parses command body
    │     format: {function} {action}/{target}[/section] -{item1} -{item2}
    │     examples:
    │       notes add/todo/today  -water plants -safeway
    │       notes add/todo/soon   -plan vacation
    │       notes add/todo        -random thought
    │       notes add/gifts/mom   -flowers -book
    │
    ├─ calls GitHub Contents API
    │     GET /repos/sphowley8/sean-brain/contents/{target}.md
    │     PUT /repos/sphowley8/sean-brain/contents/{target}.md
    │
    └─ returns TwiML response → Twilio sends reply SMS
          recognized: "Got it, added {items} to {target/section}"
          unrecognized label: "'{label}' isn't a recognized label. Added ... to .../unlabeled instead."
          error: "Dah, something got messed up. Some details are below: {error}"
```

### AWS Resources (managed by Terraform)

| Resource | Name |
|----------|------|
| Lambda function | `sms-notes-helper` |
| Lambda Function URL | public HTTPS endpoint |
| IAM role | `sms-notes-lambda-role` |

### Cost Estimate

| Item | Monthly |
|------|---------|
| Twilio number | ~$1.15 |
| SMS received (50) | ~$0.38 |
| SMS sent/reply (50) | ~$0.38 |
| Lambda | ~$0.00 (free tier) |
| **Total** | **~$2/month** |

---

## USAGE

### Prerequisites
- [Terraform](https://developer.hashicorp.com/terraform/install) installed
- AWS CLI configured with a `prod` profile (`~/.aws/credentials`)
- GitHub Personal Access Token with `repo` scope on `sphowley8/sean-brain`
- Twilio account with a phone number

---

### First-time standup (~10 min)

**Step 1 — Create a GitHub Personal Access Token**
1. github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token, select `repo` scope
3. Copy the token

**Step 2 — Get your Twilio credentials**
1. Sign up at twilio.com and buy a number (~2 min, works immediately)
2. From the Twilio console home, copy your **Auth Token**

**Step 3 — Fill in `terraform/terraform.tfvars`**
```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

| Variable | Value |
|----------|-------|
| `github_token` | GitHub PAT from Step 1 |
| `authorized_phone` | Your mobile number in E.164 format (e.g. `+15551234567`) |
| `twilio_auth_token` | Twilio Auth Token from Step 2 |

**Step 4 — Deploy**
```bash
./deploy.sh
```

Note the `webhook_url` printed in the output.

**Step 5 — Wire Twilio to Lambda** *(manual — Twilio console)*

Twilio routes inbound SMS through a **Messaging Service**, so the webhook must be configured on the service, not directly on the phone number.

1. **Create a Messaging Service**
   - Twilio console → **Messaging** → **Services** → **Create Messaging Service**
   - Give it a name (e.g. `Sean Brain Lambda Hook`), select **Mixed** use case, click through to finish

2. **Add your phone number to the service**
   - Inside the Messaging Service → **Sender Pool** tab → **Add Senders**
   - Select your toll-free number and add it

3. **Set the webhook on the Messaging Service**
   - Inside the Messaging Service → **Integration** tab
   - Under **Incoming Messages**, select **Send a Webhook**
   - Set **Request URL** to the `webhook_url` from Step 4
   - Set method to **HTTP POST**
   - Click **Save**

4. **Point the phone number at the Messaging Service**
   - Twilio console → **Phone Numbers** → **Manage** → **Active Numbers** → click your number
   - Under **Messaging Configuration** → **Messaging Service** dropdown → select your service
   - Click **Save configuration**

5. **Verify your mobile number** *(trial accounts only)*
   - Twilio console → **Phone Numbers** → **Manage** → **Verified Caller IDs**
   - Add and verify your personal mobile number — trial accounts can only send SMS to verified numbers

**Step 6 — Send a test text**

Text your Twilio number:
```
notes add/todo/today -water plants -safeway -send email
```

Expected reply: `Got it, added water plants, safeway, send email to todo/today`

---

### Testing locally (no SMS cost)

```bash
# Dry run — mocks GitHub too, nothing written anywhere
python test_sms.py --dry-run "notes add/todo/today -water plants -safeway"

# Live run — real GitHub commit, no SMS sent
python test_sms.py "notes add/todo/today -water plants -safeway"
```

---

### Updating Lambda code

```bash
./deploy.sh
```

---

### Teardown

```bash
./teardown.sh
```

Release your Twilio number separately in the Twilio console to stop billing (~$1.15/month).

---

## Terraform State

State is stored locally in `terraform/terraform.tfstate` (gitignored). For a team setup this should be moved to an S3 backend, but for single-user personal use local state is fine.
