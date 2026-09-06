"""Exercise delivery, including the byte boundary that prevents native persistence."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeliveryTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='devstandard-hook-')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        (self.root / 'hooks').mkdir()
        (self.root / 'reference').mkdir()
        shutil.copy2(ROOT / 'hooks/session-start', self.root / 'hooks/session-start')
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA')}
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
        for extra in ({}, {'CLAUDE_PLUGIN_DATA': ''}, {'PLUGIN_DATA': '/x'},
                      {'PLUGIN_DATA': '/x', 'CLAUDE_PLUGIN_DATA': '/x'}):
            self.env = {k: v for k, v in os.environ.items()
                        if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA')} | extra
            output, context = self.run_hook()
            self.assertIn('unknown harness', output['systemMessage'])
            self.assertNotIn('MUST_NOT_DELIVER', context)
            self.assertNotIn('core.md', context)

    def test_unrelated_inherited_plugin_data_preserves_claude_delivery(self):
        (self.root / 'core.md').write_text('INHERITED_ENV_TAIL')
        self.env['PLUGIN_DATA'] = '/unrelated'
        _, context = self.run_hook()
        self.assertIn('INHERITED_ENV_TAIL', context)


if __name__ == '__main__':
    unittest.main(verbosity=2)
