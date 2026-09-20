"""Delivery gate: every shipped artifact arrives whole through its declared handlers.

The name is the #205 measurement's; what it checks is ADR 0059's shape. There is no shared
core page and no size budget on a role page any more: a page larger than one hook output is
emitted across as many ordered handler calls as `hooks/hooks.json` declares, and the parts
concatenate to the file's exact bytes. What is still capped is one part's complete context,
and the failure this gate exists to catch is the hook degrading to an instructed read —
runtime behaviour, never a permitted CI state.

That cap is the HOST's (#415), so the gate is run once per host: Codex's configurable limit
admits every shipped artifact in ONE part, Claude's fixed persistence boundary does not. Each
host's handler set is declared separately and must stay silent on the other host — delivering a
page twice is as wrong as delivering it in halves — so every declared handler is driven on both
hosts and the gate checks which of them speaks.

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
CAPS = {host: int(re.search(rf'^{host.upper()}_CAP_BYTES=(\d+)$', hook_source, re.M)[1])
        for host in ('claude', 'codex')}

for page in ROLE_PAGES:
    assert (ROOT / page).is_file(), f'missing role page: {page}'
    assert NORMATIVE in (ROOT / page).read_text(), \
        f'{page}: the normative declaration must be carried by every role page'
assert not (ROOT / 'core.md').exists(), 'core.md was deleted; a role page carries the workflow now'

# The declared handlers, read from what ships: artifact, part index, declared total and the host
# the declaration serves, per call.
groups = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
declared = {host: {} for host in CAPS}
for group in groups:
    for handler in group['hooks']:
        words = shlex.split(handler['command'])
        assert len(words) == 5, f'a SessionStart handler does not name its host: {words}'
        artifact, index, total, host = words[1], int(words[2]), int(words[3]), words[4]
        assert artifact in ARTIFACTS, f'unknown delivered artifact: {artifact}'
        assert host in CAPS, f'{artifact} part {index}: unknown declared host {host}'
        # Codex truncates an unlimited hook context at its own default and drops the middle, so a
        # Codex-host handler must raise the key to that host's cap. A Claude-host handler carries
        # it too: it delivers nothing on Codex, but the key is what would protect it if it did.
        assert handler.get('additionalContextLimit', 0) >= CAPS[host], (
            f'{artifact} part {index}: additionalContextLimit below the {host} cap')
        declared[host].setdefault(artifact, []).append((index, total))
for host, artifacts in declared.items():
    for artifact, calls in artifacts.items():
        totals = {total for _, total in calls}
        assert totals == {len(calls)}, (
            f'{host} {artifact}: {len(calls)} declared handlers but they announce '
            f'{sorted(totals)} parts')
        assert sorted(index for index, _ in calls) == list(range(1, len(calls) + 1)), (
            f'{host} {artifact}: declared part numbers are not 1..{len(calls)}')

env = {k: v for k, v in os.environ.items()
       if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}


def emit(host_env, artifact, index, total, host):
    """One shipped handler call, run as the given host would run it."""
    return json.loads(subprocess.check_output(
        [str(ROOT / 'hooks/session-start'), artifact, str(index), str(total), host],
        input=b'{"source":"startup"}', env=host_env, cwd='/tmp', timeout=60))



for harness in CAPS:
    cap = CAPS[harness]
    host_env = dict(env, CLAUDE_PLUGIN_DATA='test')
    if harness == 'codex':
        host_env['PLUGIN_DATA'] = 'test'
    for artifact in ARTIFACTS:
        calls = sorted(declared[harness].get(artifact, []))
        others = sorted((host, index, total) for host, artifacts in declared.items()
                        for index, total in artifacts.get(artifact, []) if host != harness)
        sizes = []
        payload = ''
        name = ARTIFACTS[artifact]
        # The other host's handlers run here too, and owe silence: a second set that spoke would
        # deliver this page twice over.
        for host, index, total in others:
            assert emit(host_env, artifact, index, total, host) == {}, (
                f'{harness}: the {host}-host handler for {name} part {index} delivered here')
        for index, total in calls:
            emitted = emit(host_env, artifact, index, total, harness)
            context = emitted.get('hookSpecificOutput', {}).get('additionalContext', '')
            assert len(context.encode()) <= cap, f'{name} part {index}: context exceeds the cap'
            # A page carries the words "IN FULL" itself, so the degraded mode is read from the
            # hook's own system message, which only that branch writes.
            assert 'requires an IN FULL read' not in emitted.get('systemMessage', ''), (
                f'{name} part {index}: the hook fell back to the instructed read — the page needs '
                f'more than the {len(calls)} handlers hooks.json declares for {harness}, or '
                'carries a line longer than one part. Runtime behaviour, never a permitted CI '
                'state.')
            if context:
                head, blank, body = context.partition('\n\n')
                assert blank, f'{name} part {index}: emitted context carries no part header'
                sizes.append(len(context.encode()))
                payload += body
        if artifact not in DELIVERED[harness]:
            assert not sizes, f'{harness}: {name} must not be delivered here'
            print(f'{harness} {name}: suppressed, as this host requires')
            continue
        page_bytes = (ROOT / name).read_bytes()
        assert payload.encode() == page_bytes, (
            f'{harness} {name}: the delivered parts do not reconstruct the page')
        shape = 'one part' if len(sizes) == 1 else f'{len(sizes)} of {len(calls)} declared parts'
        print(f'{harness} {name}: {len(page_bytes)} bytes arrive whole in '
              f'{shape}, contexts {sizes} (cap {cap})')

print('One page per role, delivered whole; no instructed-read fallback in any shipped artifact')
