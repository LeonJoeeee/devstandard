#!/usr/bin/env python3
"""Probe the agent carrier gate against real, copied definition and anchor files."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]


class AgentEffortTest(unittest.TestCase):
    def test_worker_effort_must_match_the_claude_anchor(self):
        with tempfile.TemporaryDirectory(prefix='agent-effort-test-') as scratch:
            root = Path(scratch)
            for directory in ('agents', 'reference'):
                shutil.copytree(SOURCE / directory, root / directory)
            (root / '.github').mkdir()
            shutil.copy(SOURCE / '.github/check-agents.py', root / '.github/check-agents.py')
            worker = root / 'agents/worker.md'
            original = worker.read_text()
            for case, contents, succeeds in (
                ('matching', original, True),
                ('mismatched', original.replace('effort: high', 'effort: low', 1), False),
                ('missing', original.replace('effort: high\n', '', 1), False),
            ):
                with self.subTest(case=case):
                    worker.write_text(contents)
                    result = subprocess.run([sys.executable, str(root / '.github/check-agents.py')],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode == 0, succeeds, result.stdout + result.stderr)
                    if not succeeds:
                        self.assertIn('effort must match the Claude cell', result.stderr)


if __name__ == '__main__':
    unittest.main()
