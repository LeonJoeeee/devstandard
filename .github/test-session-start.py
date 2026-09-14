"""Exercise delivery: one page per role, whole, across as many handler calls as it takes.

A page above one hook output's cap is split on line boundaries and reconstructed by
concatenating the parts in part order, which is not the order a host appends them in (#396).
The boundary that still matters is one part's, and the
degraded mode — an instructed read — is now reached only when the page cannot be delivered
through the declared handlers at all. `BudgetGateTest` holds that to a red CI run.
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INLINE_CAP_BYTES = int(re.search(
    r'^INLINE_CAP_BYTES=(\d+)$', (ROOT / 'hooks/session-start').read_text(), re.M)[1])
ORCHESTRATOR = 'reference/orchestrator.md'
ADAPTER = 'reference/harness-codex.md'


class DeliveryTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='devstandard-hook-')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve()
        (self.root / 'hooks').mkdir()
        (self.root / 'reference').mkdir()
        shutil.copy2(ROOT / 'hooks/session-start', self.root / 'hooks/session-start')
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}
        self.env['CLAUDE_PLUGIN_DATA'] = 'test'

    def emit(self, artifact='orchestrator', payload=None, index=1, total=None):
        """The hook's raw output for one payload, whether or not it delivers anything."""
        total = index if total is None else total
        result = subprocess.run([str(self.root / 'hooks/session-start'), artifact,
                                 str(index), str(total)],
                                input=json.dumps(payload if payload is not None else {}),
                                capture_output=True, text=True, cwd='/tmp', env=self.env,
                                timeout=60, check=True)
        return json.loads(result.stdout)

    def run_hook(self, artifact='orchestrator', source='startup', index=1, total=None):
        output = self.emit(artifact, {'source': source}, index, total)
        self.assertEqual(output['hookSpecificOutput']['hookEventName'], 'SessionStart')
        context = output['hookSpecificOutput']['additionalContext']
        self.assertLessEqual(len(context.encode()), INLINE_CAP_BYTES)
        return output, context

    def deliver(self, artifact, total, source='startup'):
        """Every declared handler's output, and the page the parts reconstruct."""
        contexts = []
        for index in range(1, total + 1):
            output = self.emit(artifact, {'source': source}, index, total)
            context = output.get('hookSpecificOutput', {}).get('additionalContext', '')
            self.assertLessEqual(len(context.encode()), INLINE_CAP_BYTES)
            if context:
                contexts.append(context)
        return contexts, ''.join(c.split('\n\n', 1)[1] for c in contexts)

    def test_complete_small_artifacts_arrive_inline_independently(self):
        # Dropping one role, or escaping its content incorrectly, loses these tails. Claude's
        # compact source is the orchestrator page's one exception, covered by its own case below.
        (self.root / ORCHESTRATOR).write_text('Orchestrator contract. "quoted" \\ tab\t\n角色尾部\n')
        for source in ('startup', 'clear', ''):
            with self.subTest(source=source):
                output, context = self.run_hook('orchestrator', source)
                self.assertIn('角色尾部', context)
                self.assertIn('Orchestrator contract.', context)
                if source:
                    self.assertIn(f'(source: {source})', output['systemMessage'])

    def test_a_page_above_one_output_arrives_whole_across_numbered_parts(self):
        """The page is the concatenation of its parts, in part order, byte for byte — the
        property the whole delivery change rests on.

        Part order is not arrival order: Claude Code 2.1.270 runs the declared handlers
        concurrently and appends each context as its process finishes, putting the same
        three-part page in four different orders across four runs (#396). So each part must
        carry its own number AND say that the parts may appear in any order; that sentence is
        what tells a reader to reassemble by number, and it is asserted here.
        """
        page = self.root / ORCHESTRATOR
        # About one and a half parts, whatever the cap is, so this stays a two-part fixture.
        lines = (INLINE_CAP_BYTES * 3) // (2 * len(f'RULE_{0:05d} ' + 'x' * 40 + '\n'))
        body = ''.join(f'RULE_{number:05d} ' + 'x' * 40 + '\n' for number in range(lines))
        page.write_text('HEAD_MARKER\n' + body + 'TAIL_MARKER\n')
        contexts, rebuilt = self.deliver('orchestrator', 4)
        self.assertEqual(len(contexts), 2, 'fixture must need exactly two of the declared parts')
        self.assertEqual(rebuilt, page.read_text())
        self.assertEqual(rebuilt.encode(), page.read_bytes())
        for number, context in enumerate(contexts, start=1):
            self.assertIn(f'(part {number} of {len(contexts)})', context)
            self.assertIn('they may appear here in any order', context)
            self.assertIn('Concatenate the parts in part order', context)
        # A declared handler the page does not need stays silent rather than repeating a part.
        self.assertEqual(self.emit('orchestrator', {'source': 'startup'}, 3, 4), {})

    def test_a_page_needing_more_parts_than_declared_degrades_visibly(self):
        """Losing a page's tail in silence is the one outcome worse than asking for a read."""
        page = self.root / ORCHESTRATOR
        page.write_text(''.join(f'RULE_{n:05d} ' + 'x' * 40 + '\n' for n in range(700))
                        + 'UNREACHED_TAIL\n')
        output, context = self.run_hook('orchestrator', 'startup', index=1, total=1)
        self.assertIn('requires an IN FULL read', output['systemMessage'])
        self.assertNotIn('UNREACHED_TAIL', context)
        self.assertIn(str(self.root / ORCHESTRATOR), context)
        self.assertIn('before acting', context)
        # Stated once, by the first handler only.
        self.assertEqual(self.emit('orchestrator', {'source': 'startup'}, 2, 2), {})

    def test_a_line_longer_than_one_part_degrades_instead_of_splitting_a_line(self):
        """Parts split on line boundaries, so no part can carry a longer line; a page with one
        degrades rather than cutting mid-line (which would also cut a multibyte character)."""
        (self.root / ORCHESTRATOR).write_text('x' * (INLINE_CAP_BYTES * 2) + '\nTAIL\n')
        output, context = self.run_hook('orchestrator', 'startup', index=1, total=4)
        self.assertIn('requires an IN FULL read', output['systemMessage'])
        self.assertIn('IN FULL', context)

    def test_claude_compaction_asks_for_the_page_instead_of_delivering_it(self):
        """Claude Code 2.1.270 (issue #375): a native Agent child's compaction fires this hook
        carrying the root session's session_id and transcript_path, no agent_type and no agent_id —
        the same seven keys a root session's compaction carries. The source cannot prove it is a
        root orchestrator session, so the orchestrator's role page is not delivered on it. With one
        page per role there is no shared page left to carry the ask, so a short notice does."""
        (self.root / ORCHESTRATOR).write_text('ORCHESTRATOR_ROLE_PAGE')
        measured = {'session_id': '5df04eb0-bf30-48b9-af9d-e1dee7c45ca8',
                    'transcript_path': '/home/leon/.claude/projects/-tmp-ds375-probe/5df04eb0.jsonl',
                    'cwd': '/tmp/ds375-probe', 'prompt_id': '75dca786-0e37-4065-a10e-5a418ac057ae',
                    'hook_event_name': 'SessionStart', 'source': 'compact',
                    'model': 'claude-opus-5[1m]'}
        for payload in ({'source': 'compact'}, measured,
                        dict(measured, model='claude-sonnet-5')):
            with self.subTest(payload=payload):
                notice = self.emit('orchestrator', payload, 1, 3)
                context = notice['hookSpecificOutput']['additionalContext']
                self.assertNotIn('ORCHESTRATOR_ROLE_PAGE', context)
                self.assertIn('IN FULL', context)
                self.assertIn(str(self.root / ORCHESTRATOR), context)
                self.assertIn('dispatched worker or reviewer, do not read it', context)
                # One notice, not one per declared handler.
                for index in (2, 3):
                    self.assertEqual(self.emit('orchestrator', payload, index, 3), {})
        # An explicit role still suppresses it, and every other source still delivers the page.
        self.assertEqual(self.emit('orchestrator', {'source': 'compact',
                                                    'agent_type': 'devstandard:worker'}, 1, 3), {})
        for source in ('startup', 'clear'):
            context = self.emit('orchestrator', {'source': source}, 1, 3)['hookSpecificOutput']['additionalContext']
            self.assertIn('ORCHESTRATOR_ROLE_PAGE', context)

    def test_delivered_orchestrator_page_states_its_own_repeat_truthfully(self):
        """The injected text tells the reader when delivery comes back; on Claude the orchestrator
        page's does not come back on compaction, so it must not promise that it does."""
        (self.root / ORCHESTRATOR).write_text('ROLE')
        (self.root / ADAPTER).write_text('ADAPTER')
        _, orchestrator = self.run_hook('orchestrator', 'startup')
        self.assertNotIn('after clear or compaction', orchestrator)
        self.assertIn('after clear; on compaction a short notice asks for this page', orchestrator)
        self.env['PLUGIN_DATA'] = 'test'
        _, adapter = self.run_hook('codex', 'startup')
        self.assertIn('after clear or compaction', adapter)

    def test_exact_byte_boundary_is_one_output_and_one_more_byte_is_two_parts(self):
        path = self.root / ORCHESTRATOR
        path.write_text('X')
        _, short = self.run_hook()
        overhead = len(short.encode()) - 1
        want = INLINE_CAP_BYTES - overhead
        line = 'x' * 60 + '\n'
        body = line * (want // len(line) - 1)
        content = body + 'x' * (want - len(body) - 8) + 'TAIL205!'
        self.assertEqual(len(content), want)
        path.write_text(content)
        _, at_limit = self.run_hook()
        self.assertEqual(len(at_limit.encode()), INLINE_CAP_BYTES)
        self.assertIn(content, at_limit)
        self.assertNotIn('(part 1 of', at_limit)
        # One byte more no longer degrades: it is delivered in two parts that rebuild it exactly.
        path.write_text(content + '\nx')
        contexts, rebuilt = self.deliver('orchestrator', 3)
        self.assertEqual(len(contexts), 2)
        self.assertEqual(rebuilt, content + '\nx')

    def test_multibyte_content_is_measured_in_bytes_and_never_split_mid_character(self):
        line = '界' * 200 + '\n'
        page = line * (INLINE_CAP_BYTES // len(line.encode()) + 2) + 'UNICODE_TAIL\n'
        (self.root / ORCHESTRATOR).write_text(page)
        contexts, rebuilt = self.deliver('orchestrator', 3)
        self.assertGreater(len(contexts), 1)
        # Decoding every part already proves no character was cut: an invalid sequence would
        # have failed the hook's own JSON at `json.loads`.
        self.assertEqual(rebuilt, page)
        self.assertIn('UNICODE_TAIL', rebuilt)
        for context in contexts:
            self.assertLessEqual(len(context.encode()), INLINE_CAP_BYTES)

    def test_missing_role_reports_failure_instead_of_empty_delivery(self):
        output, context = self.run_hook('orchestrator')
        self.assertIn('not delivered', output['systemMessage'])
        self.assertIn('Stop', context)
        self.assertEqual(self.emit('orchestrator', {'source': 'startup'}, 2, 3), {})

    def test_unsupported_environments_deliver_no_method(self):
        (self.root / ORCHESTRATOR).write_text('MUST_NOT_DELIVER')
        for extra in ({}, {'CLAUDE_PLUGIN_DATA': ''}):
            self.env = {k: v for k, v in os.environ.items()
                        if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')} | extra
            output, context = self.run_hook()
            self.assertIn('unknown harness', output['systemMessage'])
            self.assertNotIn('MUST_NOT_DELIVER', context)
            self.assertNotIn(ORCHESTRATOR, context)

    def test_unrelated_inherited_plugin_data_preserves_claude_delivery(self):
        (self.root / ORCHESTRATOR).write_text('INHERITED_ENV_TAIL')
        self.env['PLUGIN_DATA'] = '/unrelated'
        _, context = self.run_hook()
        self.assertIn('INHERITED_ENV_TAIL', context)

    def test_codex_environment_delivers_each_shared_artifact(self):
        for extra in ({'PLUGIN_DATA': '/codex'},
                      {'PLUGIN_DATA': '/codex', 'CLAUDE_PLUGIN_DATA': '/codex'}):
            self.env.pop('CLAUDE_PLUGIN_DATA', None)
            self.env.update(extra)
            for artifact, path in (('orchestrator', ORCHESTRATOR), ('codex', ADAPTER)):
                (self.root / path).write_text('CODEX_ROLE_TAIL')
                for source in ('startup', 'resume', 'clear', 'compact'):
                    with self.subTest(environment=extra, artifact=artifact, source=source):
                        _, context = self.run_hook(artifact, source)
                        self.assertIn('CODEX_ROLE_TAIL', context)

    def test_dispatched_roles_do_not_receive_orchestrator_context(self):
        for harness in ('codex', 'claude'):
            self.env.pop('PLUGIN_DATA', None)
            self.env['CLAUDE_PLUGIN_DATA'] = '/' + harness
            if harness == 'codex':
                self.env['PLUGIN_DATA'] = '/codex'
            for role in ('worker', 'reviewer'):
                self.env['DEVSTANDARD_ROLE'] = role
                for artifact in ('orchestrator', 'codex'):
                    for index in (1, 2):
                        with self.subTest(harness=harness, role=role, artifact=artifact, part=index):
                            result = subprocess.run(
                                [str(self.root / 'hooks/session-start'), artifact, str(index), '3'],
                                input='{}', capture_output=True, text=True,
                                env=self.env, timeout=5, check=True)
                            self.assertEqual(json.loads(result.stdout), {})

    def test_idle_stdin_cannot_hang_delivery(self):
        (self.root / ORCHESTRATOR).write_text('IDLE_PIPE_TAIL')
        with subprocess.Popen([str(self.root / 'hooks/session-start'), 'orchestrator'],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=self.env) as process:
            process.wait(timeout=6)
            output = json.loads(process.stdout.read())
            self.assertEqual(process.returncode, 0)
            self.assertIn('IDLE_PIPE_TAIL', output['hookSpecificOutput']['additionalContext'])

    def test_claude_agent_session_does_not_receive_orchestrator_context(self):
        # Real Claude --agent carries a top-level agent_type on SessionStart.
        (self.root / ORCHESTRATOR).write_text('MAIN_ROLE_ONLY')
        for role in ('devstandard:worker', 'devstandard:reviewer', 'worker', 'reviewer'):
            for index in (1, 2):
                with self.subTest(role=role, part=index):
                    result = subprocess.run(
                        [str(self.root / 'hooks/session-start'), 'orchestrator', str(index), '3'],
                        input=json.dumps({'source': 'startup', 'agent_type': role}),
                        capture_output=True, text=True, env=self.env, timeout=5, check=True)
                    self.assertEqual(json.loads(result.stdout), {})
        for payload in ({'agent_type': None}, {'agent_type': 'default'},
                        {'unrelated': {'agent_type': 'devstandard:worker'}},
                        {'agent_type': ['worker']}, ['worker']):
            with self.subTest(payload=payload):
                result = subprocess.run([str(self.root / 'hooks/session-start'), 'orchestrator'],
                                        input=json.dumps(payload), capture_output=True, text=True,
                                        env=self.env, timeout=5, check=True)
                self.assertIn('MAIN_ROLE_ONLY', json.loads(result.stdout)
                              ['hookSpecificOutput']['additionalContext'])

    def test_codex_adapter_is_not_delivered_to_claude(self):
        result = subprocess.run([str(self.root / 'hooks/session-start'), 'codex', '1', '2'],
                                input='{}', capture_output=True, text=True,
                                env=self.env, timeout=5, check=True)
        self.assertEqual(json.loads(result.stdout), {})

    def test_an_unknown_artifact_or_part_is_a_hard_error(self):
        for argv in (['unknown'], ['orchestrator', 'x'], ['orchestrator', '0', '1'],
                     ['orchestrator', '3', '2']):
            with self.subTest(argv=argv):
                result = subprocess.run([str(self.root / 'hooks/session-start')] + argv,
                                        input='{}', capture_output=True, text=True,
                                        env=self.env, timeout=5)
                self.assertNotEqual(result.returncode, 0)


class BudgetGateTest(unittest.TestCase):
    """The gate refuses a page that cannot be delivered whole by the declared handlers."""

    GATE = '.github/check-core-budget.py'
    SOURCES = ('hooks/session-start', 'hooks/hooks.json',
               ORCHESTRATOR, 'reference/worker.md', ADAPTER)

    def install(self):
        """Copy every source the gate reads into a temporary plugin root it can be run from."""
        scratch = tempfile.TemporaryDirectory(prefix='devstandard-budget-')
        self.addCleanup(scratch.cleanup)
        root = Path(scratch.name).resolve()
        for name in self.SOURCES + (self.GATE,):
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, root / name)
        return root

    def run_gate(self, root):
        return subprocess.run([sys.executable, str(root / self.GATE)],
                              capture_output=True, text=True, timeout=180)

    def declared_parts(self, root, artifact):
        groups = json.loads((root / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
        return sum(1 for group in groups for handler in group['hooks']
                   if handler['command'].split('"')[-1].split()[0] == artifact)

    def test_current_pages_pass_the_gate(self):
        result = self.run_gate(ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(ORCHESTRATOR + ':', result.stdout)
        self.assertIn('arrive whole', result.stdout)

    def test_gate_passes_within_the_declared_parts_and_fails_past_them(self):
        root = self.install()
        page = root / ORCHESTRATOR
        source = page.read_text()
        declared = self.declared_parts(root, 'orchestrator')
        self.assertGreaterEqual(declared, 2)

        # Filling every declared part is still a pass: size is not the constraint, coverage is.
        filler = 'DEVSTANDARD_FILLER_LINE ' + 'x' * 40 + '\n'
        # A conservative per-part budget: the real one is the cap less this artifact's header.
        part_budget = INLINE_CAP_BYTES - 800

        def grow(parts):
            target = part_budget * parts - 1000
            page.write_text(source + filler * (max(0, target - len(source)) // len(filler)))

        grow(declared)
        within = self.run_gate(root)
        self.assertEqual(within.returncode, 0, within.stdout + within.stderr)
        self.assertIn(f'of {declared} declared parts', within.stdout)

        # One part more than hooks.json declares is the tail-losing case, and it fails here.
        grow(declared + 1)
        over = self.run_gate(root)
        self.assertNotEqual(over.returncode, 0, over.stdout)
        self.assertIn(ORCHESTRATOR, over.stderr)
        self.assertIn('instructed read', over.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
