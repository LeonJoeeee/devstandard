"""Core budget and real per-artifact hook output, derived from the #205 measurement."""

import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CORE_BYTE_BUDGET = 9000
CORE_TOKEN_BUDGET = 1800
core = (ROOT / 'core.md').read_text()
size = len(core.encode())
tokens = int(len(core.split()) * 1.35)
cap = int(re.search(r'^INLINE_CAP_BYTES=(\d+)$', (ROOT / 'hooks/session-start').read_text(), re.M)[1])
assert CORE_BYTE_BUDGET < cap
print(f'core.md {size} bytes (ceiling {CORE_BYTE_BUDGET}); ~{tokens} tokens (ceiling {CORE_TOKEN_BUDGET})')
assert size <= CORE_BYTE_BUDGET, 'core.md exceeds byte budget'
assert tokens <= CORE_TOKEN_BUDGET, 'core.md exceeds token proxy budget'
assert core.startswith('**DevStandard is your operating instruction.'), 'normative declaration must open core'

env = {k: v for k, v in os.environ.items() if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA')}
env['CLAUDE_PLUGIN_DATA'] = 'test'
for artifact, path in (('core', 'core.md'), ('orchestrator', 'reference/orchestrator.md')):
    output = subprocess.check_output([str(ROOT / 'hooks/session-start'), artifact],
                                     input=b'{"source":"startup"}', env=env, cwd='/tmp', timeout=5)
    context = json.loads(output)['hookSpecificOutput']['additionalContext']
    length = len(context.encode())
    assert length <= cap, f'{path}: complete hook context exceeds cap'
    inline = (ROOT / path).read_text().rstrip('\n') in context
    assert inline, (f'{path}: complete context crosses the {cap}-byte inline cap, so the hook falls '
                    'back to the instructed read — runtime behaviour, never a permitted CI state')
    print(f'{path}: inline, context {length} bytes (cap {cap})')
for path in ('reference/orchestrator.md', 'reference/worker.md'):
    assert (ROOT / path).is_file() and path in core, f'missing role pointer: {path}'
assert len((ROOT / 'reference/worker-brief.md').read_text().splitlines()) == 1
assert 'worker.md' in (ROOT / 'reference/worker-brief.md').read_text()
hooks = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
commands = [h['command'] for group in hooks if group['matcher'] == 'startup|clear|compact' for h in group['hooks']]
assert any(command.endswith('session-start"') for command in commands)
assert any(command.endswith('session-start" orchestrator') for command in commands)
print('Normative entry, role references, compatibility pointer and lifecycle carriers OK')
