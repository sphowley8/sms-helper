import base64
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_OWNER = 'sphowley8'
GITHUB_REPO = 'sean-brain'
GITHUB_BRANCH = 'main'
_API_BASE = 'https://api.github.com'

# Section names for the todo target
_SECTION_NAMES = {
    'today': 'Today',
    'soon': 'Soon',
    None: 'Unlabeled',
}

_TODO_TEMPLATE = "# Todo\n\n## Today\n\n## Soon\n\n## Unlabeled\n"


def _request(method, path, body=None):
    url = f"{_API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        body_text = e.read().decode()
        raise RuntimeError(f"GitHub API {e.code}: {body_text}") from e


def _get_file(path):
    return _request('GET', f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}")


def _put_file(path, content, sha=None, message="sms update"):
    body = {
        'message': message,
        'content': base64.b64encode(content.encode()).decode(),
        'branch': GITHUB_BRANCH,
    }
    if sha:
        body['sha'] = sha
    return _request('PUT', f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}", body)


def _insert_into_section(content, section_title, block):
    """
    Insert block under the ## section_title heading.
    If the section doesn't exist it is appended at the end.
    """
    lines = content.splitlines()
    header = f"## {section_title}"

    sec_idx = next((i for i, l in enumerate(lines) if l.strip() == header), None)

    if sec_idx is None:
        tail = '' if content.endswith('\n') else '\n'
        return content + tail + f"\n## {section_title}\n{block}\n"

    # Find the start of the next section or end of file
    next_sec = next(
        (i for i in range(sec_idx + 1, len(lines)) if lines[i].startswith('## ')),
        len(lines)
    )

    # Insert after the last non-empty line in the section, or right after header
    insert_at = sec_idx + 1
    for i in range(next_sec - 1, sec_idx, -1):
        if lines[i].strip():
            insert_at = i + 1
            break

    lines[insert_at:insert_at] = block.splitlines()
    return '\n'.join(lines) + '\n'


def _extract_section_items(content, section_title):
    """Return bullet items from a ## section, skipping comment lines."""
    lines = content.splitlines()
    header = f"## {section_title}"
    sec_idx = next((i for i, l in enumerate(lines) if l.strip() == header), None)
    if sec_idx is None:
        return []
    next_sec = next(
        (i for i in range(sec_idx + 1, len(lines)) if lines[i].startswith('## ')),
        len(lines)
    )
    return [l.strip()[2:] for l in lines[sec_idx + 1:next_sec]
            if l.strip().startswith('- ')]


def get_notes(target, section=None):
    """
    Read notes from {target}.md and return a formatted SMS-ready string.
    For todo: returns items per section. For other targets: returns all bullets.
    """
    path = f"{target}.md"
    file_data = _get_file(path)
    if not file_data:
        return f"No {target}.md file found yet."

    content = base64.b64decode(file_data['content']).decode()

    if target == 'todo':
        if section:
            section_title = _SECTION_NAMES.get(section, section.title())
            items = _extract_section_items(content, section_title)
            if not items:
                return f"Nothing in todo/{section} yet."
            reply = f"{section_title}: " + ", ".join(items)
        else:
            parts = []
            for title in ('Today', 'Soon', 'Unlabeled'):
                items = _extract_section_items(content, title)
                if items:
                    parts.append(f"{title}: " + ", ".join(items))
            reply = " | ".join(parts) if parts else "Todo is empty."

    elif target == 'gifts':
        if section:
            section_title = section.title()
            items = _extract_section_items(content, section_title)
            if not items:
                return f"Nothing in gifts/{section} yet."
            reply = f"{section_title}: " + ", ".join(items)
        else:
            # Extract all ## sections
            parts = []
            for line in content.splitlines():
                if line.startswith('## '):
                    title = line[3:].strip()
                    items = _extract_section_items(content, title)
                    if items:
                        parts.append(f"{title}: " + ", ".join(items))
            reply = " | ".join(parts) if parts else "Gifts is empty."

    else:
        items = [l.strip()[2:] for l in content.splitlines() if l.strip().startswith('- ')]
        if not items:
            return f"Nothing in {target} yet."
        reply = ", ".join(items)

    # Truncate to stay within safe SMS limits
    if len(reply) > 1500:
        reply = reply[:1497] + "..."
    return reply


def append_notes(target, items, action, section=None):
    """
    Append markdown list items to {target}.md in the GitHub repo.

    For the 'todo' target, items are inserted under the appropriate section
    (Today / Soon / Unlabeled). Unrecognized sections fall back to Unlabeled.
    For all other targets, items are appended at the end of the file.

    Returns a dict with:
        section_used      — section title actually written to (e.g. 'Today')
        section_recognized — False if the requested section wasn't known
    """
    path = f"{target}.md"
    file_data = _get_file(path)

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    new_lines = '\n'.join(f"- {item}" for item in items)
    block = f"<!-- {timestamp} -->\n{new_lines}"

    if target == 'todo':
        section_recognized = section is None or section in _SECTION_NAMES
        section_title = _SECTION_NAMES.get(section, 'Unlabeled')

        if file_data:
            existing = base64.b64decode(file_data['content']).decode()
            updated = _insert_into_section(existing, section_title, block)
            _put_file(path, updated, sha=file_data['sha'],
                      message=f"sms: add to todo/{section_title.lower()}")
        else:
            updated = _insert_into_section(_TODO_TEMPLATE, section_title, block)
            _put_file(path, updated, message="sms: create todo")

        return {'section_used': section_title, 'section_recognized': section_recognized}

    elif target == 'gifts':
        if not section:
            raise ValueError("A name is required for gifts. Format: notes add/gifts/<name> -item1 -item2")

        section_title = section.title()

        if file_data:
            existing = base64.b64decode(file_data['content']).decode()
            updated = _insert_into_section(existing, section_title, block)
            _put_file(path, updated, sha=file_data['sha'],
                      message=f"sms: add to gifts/{section_title.lower()}")
        else:
            updated = _insert_into_section("# Gifts\n", section_title, block)
            _put_file(path, updated, message="sms: create gifts")

        return {'section_used': section_title, 'section_recognized': True}

    else:
        new_block = f"\n<!-- {timestamp} -->\n{new_lines}\n"
        if file_data:
            existing = base64.b64decode(file_data['content']).decode()
            updated = existing.rstrip('\n') + new_block
            _put_file(path, updated, sha=file_data['sha'], message=f"sms: {action} to {target}")
        else:
            updated = f"# {target.title()}\n{new_block}"
            _put_file(path, updated, message=f"sms: create {target}")

        return {'section_used': None, 'section_recognized': True}
