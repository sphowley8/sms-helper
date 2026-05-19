import re


class ParseError(ValueError):
    pass


_VALID_SLUG = re.compile(r'^[a-z0-9][a-z0-9\-]*$')

USAGE = (
    "Format: '{function} {action}/{target}[/section] -{item1} -{item2}'\n"
    "Examples:\n"
    "  notes add/todo/today -water plants -safeway\n"
    "  notes add/todo/future -plan vacation\n"
    "  notes add/todo -random thought\n"
    "  notes get/todo\n"
    "  notes get/todo/today"
)


def parse_sms(body):
    """
    Parse an SMS command body into its components.

    Expected format:
        {function} {action}/{target}[/section] -{item1} -{item2} ...

    Returns a dict with keys: function, action, target, section (or None), items.
    Raises ParseError on any malformed input.
    """
    parts = body.strip().split(None, 2)

    if len(parts) < 2:
        raise ParseError(f"Too few parts.\n{USAGE}")

    function = parts[0].lower()

    components = parts[1].split('/')
    if len(components) < 2:
        raise ParseError(f"Expected 'action/target', got '{parts[1]}'.\n{USAGE}")

    action = components[0].lower()
    target = components[1].lower()
    section = components[2].lower() if len(components) > 2 else None

    if not _VALID_SLUG.match(target):
        raise ParseError(f"Target '{target}' must be lowercase letters, digits, and hyphens only.")

    if section and not _VALID_SLUG.match(section):
        raise ParseError(f"Section '{section}' must be lowercase letters, digits, and hyphens only.")

    if len(parts) >= 3 and parts[2].strip():
        items = [item.strip() for item in parts[2].split('-') if item.strip()]
    else:
        items = []

    return {
        'function': function,
        'action': action,
        'target': target,
        'section': section,
        'items': items,
    }
