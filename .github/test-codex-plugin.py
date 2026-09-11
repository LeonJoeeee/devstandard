"""Package-boundary probes; real Codex execution lives in test-codex-runtime.py."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CodexPluginTest(unittest.TestCase):
    def test_marketplace_resolves_a_versioned_plugin_with_a_loadable_skill(self):
        market = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        entry, = market['plugins']
        self.assertEqual((ROOT / entry['source']['path']).resolve(), ROOT)
        self.assertEqual(entry['policy']['installation'], 'AVAILABLE')
        manifest = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(entry['name'], manifest['name'])
        versions = [manifest['version'],
                    json.loads((ROOT / '.claude-plugin/plugin.json').read_text())['version'],
                    json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())['plugins'][0]['version']]
        self.assertEqual(len(set(versions)), 1, versions)
        skills = list((ROOT / manifest['skills']).glob('*/SKILL.md'))
        self.assertEqual(len(skills), 1)
        text = skills[0].read_text()
        self.assertIn('\nname: devstandard\n', text)
        for target in re.findall(r'\]\(([^)]+)\)', text):
            self.assertTrue((skills[0].parent / target).resolve().is_file(), target)

    def test_registered_lifecycle_handlers_deliver_full_artifacts_from_a_cache_path(self):
        # Exercise command quoting and the shipped matcher/handler structure at an installed path.
        with tempfile.TemporaryDirectory(prefix='devstandard-package-') as tmp:
            root = Path(tmp).resolve() / ('cache path 中文/' + 'x' * 70 + '/devstandard/0.47.0')
            root.mkdir(parents=True)
            for name in ('hooks', 'reference'):
                shutil.copytree(ROOT / name, root / name)
            shutil.copy2(ROOT / 'core.md', root / 'core.md')
            groups = json.loads((root / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
            base = {k: v for k, v in os.environ.items()
                    if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}
            for harness in ('claude', 'codex'):
                env = dict(base, CLAUDE_PLUGIN_ROOT=str(root), CLAUDE_PLUGIN_DATA=str(root / 'data'))
                if harness == 'codex':
                    env.update(PLUGIN_ROOT=str(root), PLUGIN_DATA=str(root / 'data'))
                for source in ('startup', 'resume', 'clear', 'compact'):
                    contexts = []
                    for group in groups:
                        if not re.search(group.get('matcher', ''), source):
                            continue
                        for handler in group['hooks']:
                            result = subprocess.run(handler['command'], shell=True, env=env,
                                                    input=json.dumps({'source': source}), text=True,
                                                    capture_output=True, timeout=5, check=True, cwd=tmp)
                            payload = json.loads(result.stdout)
                            context = payload.get('hookSpecificOutput', {}).get('additionalContext', '')
                            self.assertLessEqual(len(context.encode()), 10000)
                            if context:
                                contexts.append(context)
                    expected = ([] if source == 'resume' else ['core.md', 'reference/orchestrator.md'])
                    if harness == 'codex':
                        expected.append('reference/harness-codex.md')
                    with self.subTest(harness=harness, source=source):
                        self.assertEqual(len(contexts), len(expected))
                        for name in expected:
                            self.assertTrue(any((root / name).read_text().rstrip('\n') in c for c in contexts), name)

    def run_guard(self, event, role=None, explicit=None):
        env = {k: v for k, v in os.environ.items() if k != 'DEVSTANDARD_ROLE'}
        if role:
            env['DEVSTANDARD_ROLE'] = role
        command = [str(ROOT / 'hooks/pre-tool-use')]
        if explicit:
            command += ['--role', explicit]
        result = subprocess.run(command, input=json.dumps(event), capture_output=True,
                                text=True, env=env, timeout=5, check=True)
        return json.loads(result.stdout).get('hookSpecificOutput', {}).get('permissionDecision')

    def test_inherited_role_and_explicit_role_keep_their_own_word_rules(self):
        event = {'tool_name': 'Bash', 'tool_input': {'command': 'git tag probe'}}
        self.assertIsNone(self.run_guard(event))
        self.assertEqual(self.run_guard(event, 'worker'), 'deny')
        event['tool_input']['command'] = 'git push origin topic'
        self.assertIsNone(self.run_guard(event, 'worker'))
        self.assertEqual(self.run_guard(event, 'reviewer'), 'deny')
        self.assertEqual(self.run_guard(event, 'worker', 'reviewer'), 'deny')
        self.assertIsNone(self.run_guard(event, 'reviewer', 'worker'))
        event['tool_input']['command'] = 'git status --short'
        for role in ('worker', 'reviewer', 'orchestrator'):
            self.assertIsNone(self.run_guard(event, role))

    def test_native_subagent_identity_uses_worker_rules_without_process_environment(self):
        event = {'tool_name': 'Bash', 'tool_input': {'command': 'git tag probe'}}
        self.assertIsNone(self.run_guard(event))
        event.update(agent_id='native-child-342', agent_type='default')
        self.assertEqual(self.run_guard(event), 'deny')
        event['tool_input']['command'] = 'git push origin topic'
        self.assertIsNone(self.run_guard(event))
        self.assertEqual(self.run_guard(event, 'reviewer'), 'deny')
        self.assertEqual(self.run_guard(event, explicit='reviewer'), 'deny')
        event['agent_type'] = 'devstandard:reviewer'
        self.assertEqual(self.run_guard(event), 'deny')
        self.assertEqual(self.run_guard(event, 'worker'), 'deny')
        self.assertIsNone(self.run_guard(event, 'reviewer', 'worker'))
        for missing in (None, ''):
            event.update(agent_id=missing, agent_type='default')
            event['tool_input']['command'] = 'git tag probe'
            self.assertIsNone(self.run_guard(event))

    def test_malformed_shell_events_are_denied_without_changing_non_shell_admission(self):
        for event in (None, [], {}, {'tool_name': 'Bash'},
                      {'tool_name': 'Bash', 'tool_input': {}},
                      {'tool_name': 'Bash', 'tool_input': []},
                      {'tool_name': 'Bash', 'tool_input': {'command': 12}}):
            with self.subTest(event=event):
                self.assertEqual(self.run_guard(event), 'deny')
        self.assertIsNone(self.run_guard({'tool_name': 'apply_patch', 'tool_input': 'opaque patch'}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
