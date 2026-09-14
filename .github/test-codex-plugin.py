"""Package-boundary probes; real Codex execution lives in test-codex-runtime.py."""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INLINE_CAP_BYTES = int(re.search(
    r'^INLINE_CAP_BYTES=(\d+)$', (ROOT / 'hooks/session-start').read_text(), re.M)[1])
ARTIFACTS = {'orchestrator': 'reference/orchestrator.md', 'codex': 'reference/harness-codex.md'}


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
        # A page above one output arrives in ordered parts (ADR 0059), so each artifact is
        # reassembled from its declared handlers and compared with the file.
        with tempfile.TemporaryDirectory(prefix='devstandard-package-') as tmp:
            root = Path(tmp).resolve() / ('cache path 中文/' + 'x' * 70 + '/devstandard/0.47.0')
            root.mkdir(parents=True)
            for name in ('hooks', 'reference'):
                shutil.copytree(ROOT / name, root / name)
            groups = json.loads((root / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
            base = {k: v for k, v in os.environ.items()
                    if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}
            for harness in ('claude', 'codex'):
                env = dict(base, CLAUDE_PLUGIN_ROOT=str(root), CLAUDE_PLUGIN_DATA=str(root / 'data'))
                if harness == 'codex':
                    env.update(PLUGIN_ROOT=str(root), PLUGIN_DATA=str(root / 'data'))
                for source in ('startup', 'resume', 'clear', 'compact'):
                    pages = {}
                    notices = []
                    for group in groups:
                        if not re.search(group.get('matcher', ''), source):
                            continue
                        for handler in group['hooks']:
                            args = shlex.split(handler['command'].replace(
                                '${CLAUDE_PLUGIN_ROOT}', str(root)))
                            artifact, index = args[1], int(args[2])
                            result = subprocess.run(handler['command'], shell=True, env=env,
                                                    input=json.dumps({'source': source}), text=True,
                                                    capture_output=True, timeout=60, check=True,
                                                    cwd=tmp)
                            payload = json.loads(result.stdout)
                            context = payload.get('hookSpecificOutput', {}).get('additionalContext', '')
                            self.assertLessEqual(len(context.encode()), INLINE_CAP_BYTES)
                            if not context:
                                continue
                            if context.startswith('DevStandard operating context: '):
                                pages.setdefault(ARTIFACTS[artifact], []).append(
                                    (index, context.split('\n\n', 1)[1]))
                            else:
                                notices.append(context)
                    expected = [] if source == 'resume' else ['reference/orchestrator.md']
                    if harness == 'claude' and source == 'compact':
                        # #375: compaction cannot prove a root orchestrator session, so the role
                        # page is not delivered there — a short notice asks for it instead.
                        expected = []
                    if harness == 'codex':
                        expected.append('reference/harness-codex.md')
                    with self.subTest(harness=harness, source=source):
                        self.assertEqual(sorted(pages), sorted(expected))
                        for name in expected:
                            parts = [text for _, text in sorted(pages[name])]
                            self.assertEqual(''.join(parts), (root / name).read_text(), name)
                        if harness == 'claude' and source == 'compact':
                            self.assertEqual(len(notices), 1)
                            self.assertIn('IN FULL', notices[0])
                        else:
                            self.assertEqual(notices, [])

    def test_every_session_start_handler_raises_the_codex_context_limit_to_our_cap(self):
        """#389: left unset, Codex truncates a hook's additional context at 2500 tokens — and it
        drops the MIDDLE, so a role page keeps the opening that identifies it and an ending that
        looks like an ending and loses the rules in between. Measured on codex-cli 0.153.4.

        Our cap is bytes and theirs is tokens. A token is never shorter than one byte, so a limit
        numerically at least `INLINE_CAP_BYTES` cannot cut a page the byte cap already admits,
        however that page tokenizes. That conversion is why the key reuses the cap's own number
        instead of a second one, and this is where it is enforced: raising the cap without raising
        the key fails here, offline, before any Codex job runs.
        """
        groups = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
        handlers = [handler for group in groups for handler in group['hooks']]
        self.assertTrue(handlers)
        for handler in handlers:
            with self.subTest(command=handler['command']):
                limit = handler.get('additionalContextLimit')
                self.assertIsNotNone(limit, 'a SessionStart handler delivers context with no '
                                     'additionalContextLimit: Codex truncates it at 2500 tokens')
                self.assertGreaterEqual(limit, INLINE_CAP_BYTES)

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
