import base64
import hashlib
import hmac
import logging
import os
import urllib.parse

from github_client import append_notes, get_notes
from sms_parser import ParseError, parse_sms

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AUTHORIZED_PHONE = os.environ['AUTHORIZED_PHONE']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']

FAILURE_PREFIX = "Dah, something got messed up. Some details are below:"


def _twiml(message):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/xml'},
        'body': f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{message}</Message></Response>',
    }


def _validate_twilio_signature(auth_token, url, params, signature):
    s = url + ''.join(f"{k}{v}" for k, v in sorted(params.items()))
    mac = hmac.new(auth_token.encode(), s.encode(), hashlib.sha1)
    computed = base64.b64encode(mac.digest()).decode()
    return hmac.compare_digest(computed, signature)


def _build_success_msg(parsed, result):
    items_str = ', '.join(parsed['items'])
    target = parsed['target']
    section = parsed.get('section')
    section_used = result.get('section_used')

    destination = f"{target}/{section_used.lower()}" if section_used else target

    if not result.get('section_recognized'):
        return (
            f"'{section}' isn't a recognized label. "
            f"Added {items_str} to {destination} instead."
        )

    return f"Got it, added {items_str} to {destination}"


def lambda_handler(event, context):
    # Decode body (Lambda Function URL may base64-encode it)
    body_str = event.get('body', '')
    if event.get('isBase64Encoded'):
        body_str = base64.b64decode(body_str).decode()

    params = dict(urllib.parse.parse_qsl(body_str))

    # Reconstruct request URL for Twilio signature validation
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    host = headers.get('host', '')
    path = event.get('rawPath', '/')
    query = event.get('rawQueryString', '')
    url = f"https://{host}{path}" + (f"?{query}" if query else "")

    signature = headers.get('x-twilio-signature', '')
    s_debug = url + ''.join(f"{k}{v}" for k, v in sorted(params.items()))
    import hashlib, hmac as _hmac
    mac_debug = _hmac.new(TWILIO_AUTH_TOKEN.encode(), s_debug.encode(), hashlib.sha1)
    computed_debug = base64.b64encode(mac_debug.digest()).decode()
    logger.info("DEBUG url=%s sig_received=%s sig_computed=%s", url, signature, computed_debug)
    # Signature validation temporarily disabled for debugging
    # if not _validate_twilio_signature(TWILIO_AUTH_TOKEN, url, params, signature):
    #     logger.warning("Invalid Twilio signature — request rejected")
    #     return {'statusCode': 403, 'body': 'Forbidden'}

    sender = params.get('From', '')
    sms_body = params.get('Body', '').strip()

    logger.info("Inbound SMS from %s", sender)

    if sender != AUTHORIZED_PHONE:
        logger.warning("Rejected message from unauthorized number: %s", sender)
        return {'statusCode': 200, 'body': ''}

    try:
        parsed = parse_sms(sms_body)
    except ParseError as e:
        return _twiml(f"{FAILURE_PREFIX}\n{e}")

    try:
        if parsed['function'] == 'notes':
            if parsed['action'] == 'add':
                if not parsed['items']:
                    return _twiml(f"{FAILURE_PREFIX}\nNo items found. Prefix each item with ' -'.")
                result = append_notes(parsed['target'], parsed['items'], parsed['action'], parsed.get('section'))
                return _twiml(_build_success_msg(parsed, result))
            elif parsed['action'] == 'get':
                reply = get_notes(parsed['target'], parsed.get('section'))
                return _twiml(reply)
            else:
                return _twiml(f"{FAILURE_PREFIX}\nUnknown action '{parsed['action']}'. Try: add, get")
        else:
            return _twiml(f"{FAILURE_PREFIX}\nUnknown function '{parsed['function']}'. Try: notes")
    except Exception as e:
        logger.exception("Error processing command")
        return _twiml(f"{FAILURE_PREFIX}\n{e}")
