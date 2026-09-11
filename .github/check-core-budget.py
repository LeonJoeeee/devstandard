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

env = {k: v for k, v in os.environ.items() if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}
for harness in ('claude', 'codex'):
    delivered_env = dict(env, CLAUDE_PLUGIN_DATA='test')
    artifacts = [('core', 'core.md'), ('orchestrator', 'reference/orchestrator.md')]
    if harness == 'codex':
        delivered_env['PLUGIN_DATA'] = 'test'
        artifacts.append(('codex', 'reference/harness-codex.md'))
    for artifact, path in artifacts:
        output = subprocess.check_output([str(ROOT / 'hooks/session-start'), artifact],
                                         input=b'{"source":"startup"}', env=delivered_env, cwd='/tmp', timeout=5)
        context = json.loads(output)['hookSpecificOutput']['additionalContext']
        length = len(context.encode())
        assert length <= cap, f'{path}: complete hook context exceeds cap'
        inline = (ROOT / path).read_text().rstrip('\n') in context
        assert inline, (f'{path}: complete context crosses the {cap}-byte inline cap, so the hook falls '
                        'back to the instructed read — runtime behaviour, never a permitted CI state')
        print(f'{harness} {path}: inline, context {length} bytes (cap {cap})')
for path in ('reference/orchestrator.md', 'reference/worker.md'):
    assert (ROOT / path).is_file() and path in core, f'missing role pointer: {path}'
hooks = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
commands = [h['command'] for group in hooks if group['matcher'] == 'startup|clear|compact' for h in group['hooks']]
assert any(command.endswith('session-start"') for command in commands)
assert any(command.endswith('session-start" orchestrator') for command in commands)
print('Normative entry, role references and lifecycle carriers OK')
