"""Delivery gate: every shipped artifact arrives whole through its declared handlers.

The name is the #205 measurement's; what it checks is ADR 0059's shape. There is no shared
core page and no size budget on a role page any more: a page larger than one hook output is
emitted across as many ordered handler calls as `hooks/hooks.json` declares, and the parts
concatenate to the file's exact bytes. What is still capped is one part's complete context,
and the failure this gate exists to catch is the hook degrading to an instructed read —
runtime behaviour, never a permitted CI state.

The gate drives the shipped handler commands themselves, so a page that outgrows its declared
handlers fails here rather than losing its tail in a session.
"""

import json
import os
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ROLE_PAGES = ('reference/orchestrator.md', 'reference/worker.md')
NORMATIVE = '**DevStandard is your operating instruction.'
ARTIFACTS = {'orchestrator': 'reference/orchestrator.md', 'codex': 'reference/harness-codex.md'}
# Which artifacts each host is delivered on a startup source; the Codex adapter is suppressed
# on Claude by the hook itself, and this gate asserts that rather than assuming it.
DELIVERED = {'claude': ('orchestrator',), 'codex': ('orchestrator', 'codex')}

hook_source = (ROOT / 'hooks/session-start').read_text()
cap = int(re.search(r'^INLINE_CAP_BYTES=(\d+)$', hook_source, re.M)[1])

for page in ROLE_PAGES:
    assert (ROOT / page).is_file(), f'missing role page: {page}'
    assert NORMATIVE in (ROOT / page).read_text(), \
        f'{page}: the normative declaration must be carried by every role page'
assert not (ROOT / 'core.md').exists(), 'core.md was deleted; a role page carries the workflow now'

# The declared handlers, read from what ships: artifact, part index and declared total per call.
groups = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
declared = {}
for group in groups:
    for handler in group['hooks']:
        words = shlex.split(handler['command'])
        artifact, index, total = words[1], int(words[2]), int(words[3])
        assert artifact in ARTIFACTS, f'unknown delivered artifact: {artifact}'
        assert handler.get('additionalContextLimit', 0) >= cap, (
            f'{artifact} part {index}: additionalContextLimit below the inline cap')
        declared.setdefault(artifact, []).append((index, total))
for artifact, calls in declared.items():
    totals = {total for _, total in calls}
    assert totals == {len(calls)}, (
        f'{artifact}: {len(calls)} declared handlers but they announce {sorted(totals)} parts')
    assert sorted(index for index, _ in calls) == list(range(1, len(calls) + 1)), (
        f'{artifact}: declared part numbers are not 1..{len(calls)}')

env = {k: v for k, v in os.environ.items()
       if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}
for harness in ('claude', 'codex'):
    host_env = dict(env, CLAUDE_PLUGIN_DATA='test')
    if harness == 'codex':
        host_env['PLUGIN_DATA'] = 'test'
    for artifact in ARTIFACTS:
        calls = sorted(declared[artifact])
        sizes = []
        payload = ''
        for index, total in calls:
            output = subprocess.check_output(
                [str(ROOT / 'hooks/session-start'), artifact, str(index), str(total)],
                input=b'{"source":"startup"}', env=host_env, cwd='/tmp', timeout=60)
            emitted = json.loads(output)
            context = emitted.get('hookSpecificOutput', {}).get('additionalContext', '')
            name = ARTIFACTS[artifact]
            assert len(context.encode()) <= cap, f'{name} part {index}: context exceeds the cap'
            # A page carries the words "IN FULL" itself, so the degraded mode is read from the
            # hook's own system message, which only that branch writes.
            assert 'requires an IN FULL read' not in emitted.get('systemMessage', ''), (
                f'{name} part {index}: the hook fell back to the instructed read — the page needs '
                f'more than the {len(calls)} handlers hooks.json declares, or carries a line longer '
                'than one part. Runtime behaviour, never a permitted CI state.')
            if context:
                head, blank, body = context.partition('\n\n')
                assert blank, f'{name} part {index}: emitted context carries no part header'
                sizes.append(len(context.encode()))
                payload += body
        if artifact not in DELIVERED[harness]:
            assert not sizes, f'{harness}: {ARTIFACTS[artifact]} must not be delivered here'
            print(f'{harness} {ARTIFACTS[artifact]}: suppressed, as this host requires')
            continue
        page_bytes = (ROOT / ARTIFACTS[artifact]).read_bytes()
        assert payload.encode() == page_bytes, (
            f'{harness} {ARTIFACTS[artifact]}: the delivered parts do not reconstruct the page')
        print(f'{harness} {ARTIFACTS[artifact]}: {len(page_bytes)} bytes arrive whole in '
              f'{len(sizes)} of {len(calls)} declared parts, contexts {sizes} (cap {cap})')

print('One page per role, delivered whole; no instructed-read fallback in any shipped artifact')
