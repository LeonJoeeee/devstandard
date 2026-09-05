"""Current-contract packet boundary shared by assembly and dispatch (stdlib only)."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FORMAT = 'devstandard-review-packet-v1'
SLOT = re.compile(r'\{([A-Z_][A-Z_0-9]*)\}')
SHA = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def issue_contract(body):
    # Locate headings on a masked copy, then take values from the original text.
    # Fenced commands and nested headings are part of the issue's contract, not delimiters.
    masked = re.sub(r'<!--.*?-->', lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), body, flags=re.S)
    headings, offset, fence = [], 0, None
    for line in masked.splitlines(keepends=True):
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif fence is None:
            heading = re.match(r'^(#{1,6})\s+([^\n]+?)\s*#*\s*$', line)
            if heading:
                headings.append((offset, offset+len(line), len(heading[1]), heading[2].lower()))
        offset += len(line)
    fields = {}
    for i, (_, begin, level, name) in enumerate(headings):
        if name not in ('goal', 'bounds', 'done-check'):
            continue
        require(name not in fields, f'duplicate {name} section')
        end = next((h[0] for h in headings[i+1:] if h[2] <= level), len(body))
        value = body[begin:end].strip()
        require(value and not SLOT.fullmatch(value) and value not in ('TODO', 'TBD', '{field}'),
                f'missing or unresolved placeholder in {name}')
        fields[name] = value
    require(set(fields) == {'goal', 'bounds', 'done-check'}, 'missing issue goal, bounds, or done-check')
    return fields


def template():
    matches = re.findall(r'\n```\n(.*?)\n```\n',
                         (ROOT / 'reference/code-review-prompt.md').read_text(), re.S)
    require(len(matches) == 1, 'current reviewer contract must have exactly one prompt fence')
    return matches[0]


def predicate(text=None):
    if text is None:
        text = (ROOT / 'reference/in-repo-writes.md').read_text()
    begin = '<!-- BEGIN IN-REPO-WRITES PREDICATE -->'
    end = r'<!-- END IN-REPO-WRITES PREDICATE \((\d+) payload lines\) -->'
    require(text.count(begin) == 1 and len(re.findall(end, text)) == 1,
            'predicate requires exactly one start and counted end')
    match = re.search(re.escape(begin) + r'\n(.*?)\n' + end, text, re.S)
    require(match and len(match[1].split('\n')) == int(match[2]), 'predicate payload count mismatch')
    return match[0]


def validate(packet, identity=None):
    require(packet.get('format') == FORMAT, 'unknown review packet format')
    source = template()
    require(packet.get('template') == source, 'stale reviewer contract; assemble again')
    slots = dict(packet.get('slots', {}))
    require(set(slots) == set(SLOT.findall(source)), 'missing or unknown contract slots')
    if identity:
        slots['REVIEWER_IDENTITY'] = identity
    for key, value in slots.items():
        require(isinstance(value, str) and value.strip(), f'missing {key}')
        # Quoted evidence is opaque: only an entire slot still equal to a marker is unfilled.
        require(not SLOT.fullmatch(value.strip()) and value.strip() not in ('TODO', 'TBD', '{field}'),
                f'unresolved placeholder in {key}')
    for key in ('REVIEW_BASE_SHA', 'HEAD_SHA', 'CONVENTION_BASE_SHA'):
        require(SHA.fullmatch(slots[key]), f'{key} must be a full SHA')
    require(slots['ACCEPTED_SPEC_BLOB_SHA'] == 'NONE' or SHA.fullmatch(slots['ACCEPTED_SPEC_BLOB_SHA']),
            'ACCEPTED_SPEC_BLOB_SHA must be a full SHA or NONE')
    require(slots['ARCHITECTURE_LEVEL_FLAG'] in ('YES', 'NO'), 'architecture flag must be YES or NO')
    current = predicate()
    require(set(SLOT.findall(current)) <= {'CONVENTION_BASE_SHA', 'REVIEW_BASE_SHA'},
            'unknown predicate control slot')
    bound = SLOT.sub(lambda match: slots[match[1]], current)
    require(predicate(slots['IN_REPO_WRITES_PREDICATE']) in (current, bound), 'stale or altered predicate')
    slots['IN_REPO_WRITES_PREDICATE'] = bound
    return slots


def render(packet, identity=None):
    slots = validate(packet, identity)
    # A single substitution never treats braces or headings inside evidence as template syntax.
    result = SLOT.sub(lambda match: slots[match[1]], packet['template'])
    if packet.get('accepted_spec_contents') is not None:
        result += '\n\n## Accepted spec blob contents (pinned above)\n' + packet['accepted_spec_contents']
    if packet.get('rebase_result') is not None:
        result += ('\n\n## Rebuild 5 comparison result (evidence only; full review still applies)\n'
                   + json.dumps(packet['rebase_result'], indent=2) + '\n')
    for prior in packet.get('prior_verdicts', []):
        result += '\n\n## Prior returned verdict (historical evidence, verbatim)\n' + prior
    return result


def decode(text):
    if text.lstrip().startswith('{'):
        return json.loads(text)
    return None
