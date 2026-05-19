#!/usr/bin/env python3
"""
Local test harness for sms-notes-helper.

Simulates an inbound Twilio SMS by calling the Lambda handler directly.
- Twilio signature validation is bypassed — no real Twilio account needed.
- GitHub commit is real — tests the full notes flow end to end.

Usage:
    python test_sms.py "notes add/todo/today -water plants -safeway"
    python test_sms.py --dry-run "notes add/todo/today -water plants -safeway"

Flags:
    --dry-run   Also mock the GitHub call — nothing is written anywhere.
"""
import os
import sys
import urllib.parse
from pathlib import Path
from unittest.mock import patch

LAMBDA_DIR = Path(__file__).parent / 'lambda'
TFVARS_PATH = Path(__file__).parent / 'terraform' / 'terraform.tfvars'


def read_tfvars():
    values = {}
    if TFVARS_PATH.exists():
        for line in TFVARS_PATH.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, _, val = line.partition('=')
                values[key.strip()] = val.strip().strip('"')
    return values


def build_event(sms_body, from_number):
    params = {'From': from_number, 'To': '+18005550000', 'Body': sms_body}
    return {
        'body': urllib.parse.urlencode(params),
        'isBase64Encoded': False,
        'rawPath': '/',
        'rawQueryString': '',
        'headers': {
            'host': 'test.lambda-url.us-east-1.on.aws',
            'x-twilio-signature': 'test-bypassed',
            'content-type': 'application/x-www-form-urlencoded',
        },
    }


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']

    if not args:
        print("Usage: python test_sms.py [--dry-run] \"<sms body>\"")
        print("Example: python test_sms.py \"notes add/todo/today -water plants -safeway\"")
        sys.exit(1)

    sms_body = args[0]

    tfvars = read_tfvars()
    authorized_phone = tfvars.get('authorized_phone', '')
    if not authorized_phone:
        print("ERROR: authorized_phone not found in terraform/terraform.tfvars")
        sys.exit(1)

    os.environ['AUTHORIZED_PHONE'] = authorized_phone
    os.environ['TWILIO_AUTH_TOKEN'] = tfvars.get('twilio_auth_token', 'test-token')
    os.environ['GITHUB_TOKEN'] = tfvars.get('github_token', '')
    os.environ.setdefault('AWS_REGION', 'us-east-1')

    sys.path.insert(0, str(LAMBDA_DIR))

    print(f"\nFrom : {authorized_phone}")
    print(f"Body : {sms_body}")
    print(f"Mode : {'dry-run (GitHub mocked)' if dry_run else 'live (real GitHub commit)'}")
    print()

    patches = [patch('handler._validate_twilio_signature', return_value=True)]
    if dry_run:
        patches.append(patch('github_client.append_notes', return_value={
            'section_used': None, 'section_recognized': True
        }))

    import contextlib
    import handler

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        response = handler.lambda_handler(build_event(sms_body, authorized_phone), None)

    # Extract reply text from TwiML
    body = response.get('body', '')
    if '<Message>' in body:
        reply = body.split('<Message>')[1].split('</Message>')[0]
    else:
        reply = body

    print(f"Status : {response.get('statusCode')}")
    print(f"Reply  : {reply}")


if __name__ == '__main__':
    main()
