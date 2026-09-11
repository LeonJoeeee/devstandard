"""Exercise delivery, including the byte boundary that prevents native persistence.

The same boundary is the budget gate's: `BudgetGateTest` holds it to a red CI run.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


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

    def run_hook(self, artifact='core', source='startup'):
        result = subprocess.run([str(self.root / 'hooks/session-start'), artifact],
                                input=json.dumps({'source': source}), capture_output=True,
                                text=True, cwd='/tmp', env=self.env, timeout=5, check=True)
        output = json.loads(result.stdout)
        self.assertEqual(output['hookSpecificOutput']['hookEventName'], 'SessionStart')
        context = output['hookSpecificOutput']['additionalContext']
        self.assertLessEqual(len(context.encode()), 10000)
        return output, context

    def test_complete_small_artifacts_arrive_inline_independently(self):
        # Dropping one role, or escaping its content incorrectly, loses these tails.
        samples = {'core': ('core.md', 'Normative core. "quoted" \\ tab\t\n核心尾部\n'),
                   'orchestrator': ('reference/orchestrator.md', 'Orchestrator contract.\nROLE_END\n')}
        for artifact, (path, content) in samples.items():
            (self.root / path).write_text(content)
            for source in ('startup', 'clear', 'compact', ''):
                with self.subTest(artifact=artifact, source=source):
                    output, context = self.run_hook(artifact, source)
                    self.assertIn(content.rstrip('\n'), context)
                    if source:
                        self.assertIn(f'(source: {source})', output['systemMessage'])

    def test_exact_byte_boundary_is_inline_and_one_more_byte_is_a_forced_read(self):
        path = self.root / 'core.md'
        path.write_text('X')
        _, short = self.run_hook()
        overhead = len(short.encode()) - 1
        content = 'x' * (10000 - overhead - 8) + 'TAIL205!'
        path.write_text(content)
        _, at_limit = self.run_hook()
        self.assertEqual(len(at_limit.encode()), 10000)
        self.assertIn(content, at_limit)
        path.write_text(content + 'x')
        _, overflow = self.run_hook()
        self.assertNotIn('TAIL205!', overflow)
        self.assertIn(str(path), overflow)
        self.assertIn('IN FULL', overflow)
        self.assertIn('before acting', overflow)

    def test_multibyte_content_is_measured_in_bytes(self):
        (self.root / 'core.md').write_text('界' * 4000 + 'UNICODE_TAIL')
        _, context = self.run_hook()
        self.assertNotIn('UNICODE_TAIL', context)
        self.assertIn('IN FULL', context)

    def test_missing_role_reports_failure_instead_of_empty_delivery(self):
        output, context = self.run_hook('orchestrator')
        self.assertIn('not delivered', output['systemMessage'])
        self.assertIn('Stop', context)

    def test_unsupported_environments_deliver_no_method(self):
        (self.root / 'core.md').write_text('MUST_NOT_DELIVER')
        for extra in ({}, {'CLAUDE_PLUGIN_DATA': ''}):
            self.env = {k: v for k, v in os.environ.items()
                        if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')} | extra
            output, context = self.run_hook()
            self.assertIn('unknown harness', output['systemMessage'])
            self.assertNotIn('MUST_NOT_DELIVER', context)
            self.assertNotIn('core.md', context)

    def test_unrelated_inherited_plugin_data_preserves_claude_delivery(self):
        (self.root / 'core.md').write_text('INHERITED_ENV_TAIL')
        self.env['PLUGIN_DATA'] = '/unrelated'
        _, context = self.run_hook()
        self.assertIn('INHERITED_ENV_TAIL', context)


    def test_codex_environment_delivers_each_shared_artifact(self):
        for extra in ({'PLUGIN_DATA': '/codex'},
                      {'PLUGIN_DATA': '/codex', 'CLAUDE_PLUGIN_DATA': '/codex'}):
            self.env.pop('CLAUDE_PLUGIN_DATA', None)
            self.env.update(extra)
            for artifact, path in (('core', 'core.md'),
                                   ('orchestrator', 'reference/orchestrator.md'),
                                   ('codex', 'reference/harness-codex.md')):
                (self.root / path).write_text('CODEX_ROLE_TAIL')
                for source in ('startup', 'resume', 'clear', 'compact'):
                    with self.subTest(environment=extra, artifact=artifact, source=source):
                        _, context = self.run_hook(artifact, source)
                        self.assertIn('CODEX_ROLE_TAIL', context)

    def test_dispatched_roles_do_not_receive_orchestrator_context(self):
        self.env.update(PLUGIN_DATA='/codex', CLAUDE_PLUGIN_DATA='/codex')
        for role in ('worker', 'reviewer'):
            self.env['DEVSTANDARD_ROLE'] = role
            for artifact in ('core', 'orchestrator', 'codex'):
                result = subprocess.run([str(self.root / 'hooks/session-start'), artifact],
                                        input='{}', capture_output=True, text=True,
                                        env=self.env, timeout=5, check=True)
                self.assertEqual(json.loads(result.stdout), {})

    def test_idle_stdin_cannot_hang_delivery(self):
        (self.root / 'core.md').write_text('IDLE_PIPE_TAIL')
        with subprocess.Popen([str(self.root / 'hooks/session-start')],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=self.env) as process:
            process.wait(timeout=4)
            output = json.loads(process.stdout.read())
            self.assertEqual(process.returncode, 0)
            self.assertIn('IDLE_PIPE_TAIL', output['hookSpecificOutput']['additionalContext'])

    def test_codex_adapter_is_not_delivered_to_claude(self):
        result = subprocess.run([str(self.root / 'hooks/session-start'), 'codex'],
                                input='{}', capture_output=True, text=True,
                                env=self.env, timeout=5, check=True)
        self.assertEqual(json.loads(result.stdout), {})


class BudgetGateTest(unittest.TestCase):
    """The gate refuses an artifact that would fall back to the instructed read."""

    GATE = '.github/check-core-budget.py'
    SOURCES = ('core.md', 'hooks/session-start', 'hooks/hooks.json',
               'reference/orchestrator.md', 'reference/worker.md', 'reference/harness-codex.md')

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
                              capture_output=True, text=True, timeout=60)

    def emitted_context(self, root, artifact):
        env = {k: v for k, v in os.environ.items()
               if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}
        env['CLAUDE_PLUGIN_DATA'] = 'test'
        result = subprocess.run([str(root / 'hooks/session-start'), artifact],
                                input='{"source":"startup"}', capture_output=True, text=True,
                                cwd='/tmp', env=env, timeout=5, check=True)
        return json.loads(result.stdout)['hookSpecificOutput']['additionalContext']

    def test_current_pages_pass_the_gate(self):
        result = self.run_gate(ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('reference/orchestrator.md: inline', result.stdout)

    def test_gate_passes_at_the_cap_and_fails_one_byte_over(self):
        root = self.install()
        page = root / 'reference/orchestrator.md'
        # The hook's `$(cat …)` drops the trailing newline, so pad the stripped page: that is
        # the text the emitted context actually carries, and one more byte crosses the cap.
        source = page.read_text().rstrip('\n')
        headroom = 10000 - len(self.emitted_context(root, 'orchestrator').encode())
        self.assertGreaterEqual(headroom, 0, 'fixture already overflows before padding')

        page.write_text(source + 'x' * headroom)
        self.assertEqual(len(self.emitted_context(root, 'orchestrator').encode()), 10000)
        at_cap = self.run_gate(root)
        self.assertEqual(at_cap.returncode, 0, at_cap.stderr)

        page.write_text(source + 'x' * (headroom + 1))
        self.assertIn('IN FULL', self.emitted_context(root, 'orchestrator'))
        over_cap = self.run_gate(root)
        self.assertNotEqual(over_cap.returncode, 0, over_cap.stdout)
        self.assertIn('reference/orchestrator.md', over_cap.stderr)
        self.assertIn('inline', over_cap.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
