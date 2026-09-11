#!/usr/bin/env python3
"""Exercise real git and process detachment; fake GitHub and executor I/O."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class DispatchTest(unittest.TestCase):
    def assert_role_config(self, args, role):
        import shlex
        import tomllib
        overrides = [args[i+1] for i, arg in enumerate(args) if arg == '-c']
        parsed = {}
        for override in overrides:
            key, value = override.split('=', 1)
            if key != 'hooks.PreToolUse' and not key.startswith('agents.'):
                continue
            # Codex parses each -c value independently; several root assignments in
            # one argument must not masquerade as valid combined TOML here.
            assignment = tomllib.loads('value=' + value)
            self.assertEqual(set(assignment), {'value'})
            parsed[key] = assignment['value']
        self.assertEqual(parsed.get('agents.default_subagent_model'), 'gpt-6-astra')
        self.assertEqual(parsed.get('agents.default_subagent_reasoning_effort'), 'high')
        self.assertEqual(parsed['hooks.PreToolUse'], [{
            'matcher': '.*', 'hooks': [{'type': 'command', 'command': shlex.join([
                str(SOURCE / 'hooks/pre-tool-use'), '--role', role]), 'timeout': 30}]}])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dispatch-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()  # macOS /var aliases /private/var.
        self.project = self.root / 'project'
        self.project.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.issue = self.root / 'issue.json'
        self.comments = self.root / 'comments.json'
        self.comments.write_text('[]')
        self.issue.write_text(json.dumps(dict(number=12, title='A small task', url='https://github.com/o/r/issues/12',
            state='OPEN', body='## Goal\nProduce evidence.\n## Bounds\nOne task only.\n## Done-check\nOutput is captured.')))
        self.env = dict(os.environ, PATH=str(self.bin)+os.pathsep+os.environ['PATH'],
            ISSUE=str(self.issue), COMMENTS=str(self.comments), PR=str(self.root/'pr.json'), TMPDIR=str(self.root),
            GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'test@example.com')
        self.git('config', 'user.name', 'Test')
        (self.project / '.gitignore').write_text('/.claude/worktrees/\n')
        self.git('add', '.')
        self.git('commit', '-m', 'base')
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.tool('gh', '''import json,os,sys
from pathlib import Path
a=sys.argv[1:]; c=Path(os.environ['COMMENTS'])
if a[:2]==['repo','view']: print('o/r')
elif a[:1]==['api']:
 if '/issues/comments/' in a[1]:
  rows=json.loads(c.read_text());row=next(r for r in rows if r['id']==int(a[1].rsplit('/',1)[1]))
  if '--input' in a:
   row['body']=json.loads(Path(a[a.index('--input')+1]).read_text())['body'];c.write_text(json.dumps(rows))
  print(json.dumps(row))
 elif '/issues/12/comments' in a[1]:
  assert '--paginate' in a
  rows=json.loads(c.read_text())
  print(json.dumps(rows[:1]));print(json.dumps(rows[1:]))
 elif '/comments' in a[1]: print(os.environ.get('REVIEW_COMMENTS','[]'))
 elif '/git/trees/' in a[1] or '/git/blobs/' in a[1]:
  raise SystemExit('policy must be read from the local origin/main ref, not GitHub')
 else: print(json.dumps(json.loads(os.environ.get('DEFAULT_CI', '{"default_branch":"main","owner":{"login":"o"},"commit":{"sha":"abc"},"tree":[],"check_runs":[{"name":"test","status":"completed","conclusion":"success"}],"statuses":[]}'))))
elif a[:2]==['issue','view']:
 d=json.loads(Path(os.environ['ISSUE']).read_text());d['comments']=[dict(row,id='IC_fixture_'+str(i+1),url='https://github.com/o/r/issues/12#issuecomment-'+str(i+1)) for i,row in enumerate(json.loads(c.read_text()))];print(json.dumps(d))
elif a[:2]==['issue','comment']:
 body=Path(a[a.index('--body-file')+1]).read_text()
 record=json.loads(body.split('```json\\n')[1].split('\\n```')[0])
 if record['kind']=='run' and os.environ.get('PUBLICATION_PROBE'):
  import time
  time.sleep(.2)
  Path(os.environ['PUBLICATION_PROBE']).write_text(json.dumps(dict(record=record,started=Path(record['output']).exists())))
 if record['kind']=='run' and os.environ.get('REJECT_RUN_PUBLICATION'): raise SystemExit('fixture publication failed')
 rows=json.loads(c.read_text());rows.append({'id':len(rows)+1,'body':Path(a[a.index('--body-file')+1]).read_text()});c.write_text(json.dumps(rows));print('https://github.com/o/r/issues/12#issuecomment-'+str(len(rows)))
elif a[:2]==['pr','view']: print(Path(os.environ['PR']).read_text())
elif a[:2]==['pr','list']:
 p=Path(os.environ['PR']);print(json.dumps([json.loads(p.read_text())] if p.exists() else []))
else: raise SystemExit('unexpected gh: '+repr(a))
''')
        self.tool('codex', '''import json,os,subprocess,sys,time
from pathlib import Path
a=sys.argv[1:];out=Path(a[a.index('-o')+1]);
print('executor started',flush=True)
if os.environ.get('FAKE_COMMITS'):
 wt=Path(a[a.index('-C')+1])
 for n in range(2):
  (wt/'result.txt').write_text('worker result '+str(n))
  for cmd in [('add','result.txt'),('commit','-m','worker step '+str(n))]:
   subprocess.run(['git','-C',str(wt),*cmd],check=True)
out.write_text(json.dumps({'args':a,'sid':os.getsid(0),'pid':os.getpid(),'stdin':sys.stdin.read(),'role':os.environ.get('DEVSTANDARD_ROLE')}))
hold=os.environ.get('FAKE_HOLD');deadline=time.monotonic()+20
while hold and not Path(hold).exists() and time.monotonic()<deadline: time.sleep(.01)
raise SystemExit(int(os.environ.get('FAKE_EXIT','0')))
''')
        self.tool('claude', '''import json,os,sys,time
if os.environ.get('FAKE_CLAUDE_STARTUP_FAIL'):
 print('fixture Claude authentication unavailable',file=sys.stderr);raise SystemExit(9)
data=dict(args=sys.argv[1:],cwd=os.getcwd(),stdin=sys.stdin.read(),role=os.environ.get('DEVSTANDARD_ROLE'),sid=os.getsid(0),pid=os.getpid())
print('Claude executor started',file=sys.stderr,flush=True)
result=dict(type='result',subtype='success',is_error=False,result=json.dumps(data),session_id='fixture-session',permission_denials=json.loads(os.environ.get('FAKE_CLAUDE_DENIALS','[]')))
if sys.argv[sys.argv.index('--output-format')+1]=='stream-json':
 print(json.dumps(dict(type='system',subtype='init',session_id='fixture-session')),flush=True)
 print(json.dumps(result),flush=True)
 print(json.dumps(dict(result,result='Background agent finished.',permission_denials=[])),flush=True)
else: print(json.dumps(result),flush=True)
hold=os.environ.get('FAKE_HOLD');deadline=time.monotonic()+20
while hold and not __import__('pathlib').Path(hold).exists() and time.monotonic()<deadline: time.sleep(.01)
raise SystemExit(int(os.environ.get('FAKE_EXIT','0')))
''')
        self.script = SOURCE / 'scripts/dispatch'

    def tool(self, name, body):
        p = self.bin / name
        p.write_text('#!/usr/bin/env python3\n'+body)
        p.chmod(0o755)

    def without_detachment_tools(self):
        # macOS has no setsid utility. Exercise the same supported PATH on Linux.
        for name, executable in [('python3', sys.executable), ('git', shutil.which('git'))]:
            (self.bin / name).symlink_to(executable)
        self.env['PATH'] = str(self.bin)
        self.assertIsNone(shutil.which('setsid', path=self.env['PATH']))
        self.assertIsNone(shutil.which('nohup', path=self.env['PATH']))

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.project), *args], env=self.env, stderr=subprocess.DEVNULL, text=True).strip()

    def call(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(self.script), '12', *args, '--project', str(self.project)],
            env=self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stdout+r.stderr)
            return json.loads(r.stdout)
        self.assertNotEqual(r.returncode, 0)
        return r.stderr

    def start(self, *args):
        """A worker on the Codex process path, which most of these checks exercise.

        The implementation is named rather than inherited: the default is `claude` and is
        pinned by its own test below, so a flip there must not silently retarget the
        process-detachment, sandbox, git-grant and cleanup checks.
        """
        named = () if '--implementation' in args else ('--implementation', 'codex')
        return self.call('--purpose', 'worker', '--base', 'origin/main', *named, *args)

    def lane_records(self):
        return [json.loads(row['body'].split('```json\n')[1].split('\n```')[0])
                for row in json.loads(self.comments.read_text())]

    def hand_made_lane(self):
        branch='feat/hand-made'; wt=self.root/'hand-made'
        self.git('worktree','add','-b',branch,str(wt),'origin/main')
        return branch,wt

    def wait_completion(self, run):
        if self.env.get('FAKE_HOLD'):
            Path(self.env['FAKE_HOLD']).touch()
        marker = Path(run['completion'])
        deadline = time.monotonic()+8
        while not marker.exists() and time.monotonic()<deadline:
            time.sleep(.02)
        self.assertTrue(marker.exists(), Path(run['log']).read_text())

    def finish(self, run):
        self.wait_completion(run)
        return json.loads(Path(run['output']).read_text())

    def finish_claude(self, run):
        self.wait_completion(run)
        return [json.loads(line) for line in Path(run['output']).read_text().splitlines()]

    def review_packet(self, base=None, head=None, convention=None, identity='{REVIEWER_IDENTITY}'):
        import re
        base=base or self.git('rev-parse','origin/main');head=head or base
        template=re.search(r'\n```\n(.*?)\n```\n',
            (SOURCE/'reference/code-review-prompt.md').read_text(),re.S).group(1)
        predicate=re.search(r'<!-- BEGIN IN-REPO-WRITES PREDICATE -->.*?<!-- END IN-REPO-WRITES PREDICATE \(\d+ payload lines\) -->',
            (SOURCE/'reference/in-repo-writes.md').read_text(),re.S).group()
        slots=dict(ISSUE_GOAL_STATEMENT='Produce evidence.',ISSUE_BOUNDS='One task.',
            ISSUE_DONE_CHECK='Output captured.',ARCHITECTURE_LEVEL_FLAG='NO',
            COMPLETE_PR_DESCRIPTION='Complete report.',REVIEW_BASE_SHA=base,HEAD_SHA=head,
            CONVENTION_BASE_SHA=convention or base,ACCEPTED_SPEC_BLOB_SHA='NONE',
            CI_CONFIGURATION_PATHS='NONE',
            CI_FALLBACK_COMMENT_OR_NONE='NONE',IN_REPO_WRITES_PREDICATE=predicate,
            REVIEWER_IDENTITY=identity)
        packet=self.root/'review.txt'
        packet.write_text(json.dumps(dict(format='devstandard-review-packet-v1',template=template,slots=slots)))
        return packet

    def spawn_wait(self, implementation='codex'):
        self.env['FAKE_HOLD'] = str(self.root/'executor-release')
        self.waiting_after = len(self.lane_records())
        process = subprocess.Popen([sys.executable, str(self.script), '12', '--project', str(self.project),
            '--purpose', 'worker', '--base', 'origin/main', '--implementation', implementation, '--wait'],
            env=self.env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        return process

    def await_run(self, process=None):
        deadline = time.monotonic()+8
        while time.monotonic() < deadline:
            rows = self.lane_records()[getattr(self, 'waiting_after', 0):] if process else self.lane_records()
            runs = [r for r in rows if r['kind']=='run']
            if runs and Path(runs[-1]['output']).exists() and Path(runs[-1]['output']).stat().st_size:
                return runs[-1]
            if process and process.poll() is not None:
                self.fail('dispatcher returned before executor completion: '+repr(process.communicate()))
            time.sleep(.02)
        self.fail('executor did not start')

    def replace_run(self, record):
        rows = json.loads(self.comments.read_text())
        row = next(r for r in rows if record['brief'] in r['body'])
        row['body'] = '<!-- devstandard-dispatch-v1 -->\n```json\n'+json.dumps(record)+'\n```\n'
        self.comments.write_text(json.dumps(rows))

    def continuation_options(self):
        brief = self.root/'continue.txt'; brief.write_text('Complete the remaining work.')
        return ('--purpose', 'worker', '--implementation', 'codex', '--continue', '--brief', str(brief))

    def test_wait_holds_both_cli_invocations_until_atomic_completion_and_keeps_nonzero_output(self):
        for implementation in ('codex', 'claude-cli'):
            with self.subTest(implementation=implementation):
                self.env['FAKE_EXIT'] = '7'
                process = self.spawn_wait(implementation)
                record = self.await_run(process)
                self.assertIsNone(process.poll())
                self.assertFalse(Path(record['completion']).exists())
                Path(self.env['FAKE_HOLD']).touch()
                stdout, stderr = process.communicate(timeout=8)
                self.assertEqual(process.returncode, 0, stderr)
                returned = json.loads(stdout)
                self.assertEqual(returned['executor_exit'], 7)
                self.assertEqual(Path(record['completion']).read_text(), '7\n')
                self.assertTrue(Path(record['output']).read_text())
                self.assertFalse(Path(record['completion']).with_suffix('.tmp').exists())
                self.call('--cleanup', '--discard')
                Path(self.env['FAKE_HOLD']).unlink()

    def test_wait_rejects_native_and_maintenance_combinations_before_mutation(self):
        for options in [('--purpose','worker','--base','origin/main'),
                        ('--purpose','worker','--implementation','codex-native','--base','origin/main'),
                        ('--adopt',), ('--cleanup','--discard')]:
            before = set(self.root.iterdir())
            self.assertIn('--wait', self.call(*options, '--wait', ok=False))
            self.assertEqual(set(self.root.iterdir()), before)
            self.assertEqual(self.lane_records(), [])

    def test_wait_publication_failure_never_starts_either_cli(self):
        for implementation in ('codex', 'claude-cli'):
            # A separate issue fixture per adapter avoids inheriting the failed lane.
            with self.subTest(implementation=implementation):
                fixture = DispatchTest(); fixture.setUp()
                try:
                    probe = fixture.root/'publication.json'
                    fixture.env.update(PUBLICATION_PROBE=str(probe), REJECT_RUN_PUBLICATION='1')
                    error = fixture.call('--purpose','worker','--base','origin/main',
                        '--implementation',implementation,'--wait',ok=False)
                    self.assertIn('fixture publication failed', error)
                    record = json.loads(probe.read_text())['record']
                    self.assertFalse(Path(record['output']).exists())
                    self.assertFalse(Path(record['brief']).with_name('launch').exists())
                finally:
                    fixture.doCleanups()

    def test_active_lock_refuses_despite_absent_or_reused_diagnostic_pid(self):
        self.env['FAKE_HOLD'] = str(self.root/'executor-release')
        record = self.start(); self.await_run()
        options = self.continuation_options()
        try:
            for pid in (999999999, os.getpid()):
                record['pid'] = pid; self.replace_run(record)
                self.assertIn('running', self.call(*options, '--native-finished', ok=False))
                self.assertIn('running', self.call('--cleanup','--discard','--native-finished',ok=False))
        finally:
            self.wait_completion(record)

    def test_lost_supervisor_and_deleted_completion_never_admit_reuse(self):
        self.env['FAKE_HOLD'] = str(self.root/'executor-release')
        record = self.start(); self.await_run()
        os.killpg(record['pid'], signal.SIGKILL)
        time.sleep(.1)
        record['pid'] = 999999999; self.replace_run(record)
        options = self.continuation_options()
        for flags in (options, ('--cleanup','--discard')):
            self.assertIn('lost or unknown', self.call(*flags,'--native-finished',ok=False))
        self.assertFalse(Path(record['completion']).exists())

    def test_missing_legacy_scratch_is_unknown_even_with_native_finished(self):
        record = self.start(); self.finish(record)
        shutil.rmtree(Path(record['brief']).parent)
        record['pid'] = 999999999; record.pop('supervisor_lock',None); self.replace_run(record)
        self.assertIn('lost or unknown', self.call(*self.continuation_options(),'--native-finished',ok=False))
        self.assertIn('lost or unknown', self.call('--cleanup','--discard','--native-finished',ok=False))

    def test_wait_sigterm_cancels_only_owned_group_and_never_invents_success(self):
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])
        self.addCleanup(lambda: unrelated.poll() is None and unrelated.kill())
        process = self.spawn_wait()
        record = self.await_run(process)
        process.terminate()
        stdout, stderr = process.communicate(timeout=8)
        self.assertNotEqual(process.returncode, 0)
        self.assertIsNone(unrelated.poll())
        marker = Path(record['completion'])
        if marker.exists():
            self.assertLess(int(marker.read_text()), 0)
        self.assertNotIn('"executor_exit": 0', stdout)
        unrelated.terminate(); unrelated.wait()

    def reconcile_options(self, record):
        return ('--reconcile-lost',record['brief'],'--reason','Origin host inspection found no owned processes.',
                '--evidence','https://github.com/o/r/issues/12#issuecomment-99')

    def lost_record(self):
        record = self.start(); self.finish(record)
        Path(record['completion']).unlink()
        return record

    def test_reconcile_exact_lost_run_preserves_identity_and_admits_fresh_continuation(self):
        record = self.lost_record()
        before = json.loads(self.comments.read_text())
        result = self.call(*self.reconcile_options(record))
        self.assertEqual(result['status'],'reconciled-lost')
        self.assertNotIn('executor_exit',result)
        for key, value in record.items():
            if key != 'status': self.assertEqual(result[key],value)
        after = json.loads(self.comments.read_text())
        self.assertEqual(len(after),len(before))
        self.assertEqual(after[0],before[0])
        self.assertEqual(after[-1]['id'],before[-1]['id'])
        unchanged = self.comments.read_text()
        self.assertEqual(self.call(*self.reconcile_options(record)),result)
        self.assertEqual(self.comments.read_text(),unchanged)
        self.assertIn('conflict',self.call(*self.reconcile_options(record),'--reason','Different finding.',ok=False))
        self.assertEqual(self.comments.read_text(),unchanged)
        continued = self.call(*self.continuation_options(),'--wait'); self.finish(continued)
        self.assertEqual(continued['lane_id'],record['lane_id'])
        self.assertNotEqual(continued['brief'],record['brief'])

    def test_reconcile_refuses_active_completed_native_and_wrong_targets(self):
        self.env['FAKE_HOLD'] = str(self.root/'executor-release')
        record = self.start(); self.await_run()
        try:
            self.assertIn('running',self.call(*self.reconcile_options(record),ok=False))
        finally:
            self.wait_completion(record)
        self.assertIn('completion',self.call(*self.reconcile_options(record),ok=False))
        wrong = dict(record,brief=str(self.root/'wrong'/'brief.txt'))
        self.assertIn('exactly one',self.call(*self.reconcile_options(wrong),ok=False))
        native = self.call(*self.continuation_options(),'--implementation','codex-native')
        self.assertIn('CLI',self.call(*self.reconcile_options(native),ok=False))

    def test_reconcile_rejects_missing_evidence_and_combined_actions_without_mutation(self):
        record = self.lost_record()
        before = self.comments.read_text()
        for flags in [('--reason',''),('--evidence',''),('--evidence','local.log'),('--wait',),
                      ('--cleanup','--discard'),('--adopt',),('--purpose','worker'),('--continue',),
                      ('--native-finished',),('--implementation','codex')]:
            self.call(*self.reconcile_options(record),*flags,ok=False)
            self.assertEqual(self.comments.read_text(),before)

    def test_reconcile_missing_scratch_does_not_recreate_or_invent_completion(self):
        record = self.lost_record(); scratch = Path(record['brief']).parent
        shutil.rmtree(scratch)
        self.call(*self.reconcile_options(record))
        self.assertFalse(scratch.exists())
        continued = self.call(*self.continuation_options(),'--wait')
        self.assertEqual(continued['executor_exit'],0)

    def test_reconcile_rechecks_completion_and_issue_identity_before_patch(self):
        record = self.lost_record()
        source = (self.bin/'gh').read_text()
        injection = """elif a[:2]==['issue','view']:
 counter=Path(os.environ['VIEW_COUNTER']); count=int(counter.read_text())+1;counter.write_text(str(count))
 if count==2:
  if os.environ['RACE_KIND']=='completion': Path(os.environ['RACE_COMPLETION']).write_text('0\\n')
  else:
   rows=json.loads(c.read_text());rows[-1]['body']=rows[-1]['body'].replace('"model": "gpt-5.6-sol"','"model": "changed"');c.write_text(json.dumps(rows))
"""
        (self.bin/'gh').write_text(source.replace("elif a[:2]==['issue','view']:",injection))
        counter = self.root/'view-counter'
        self.env.update(VIEW_COUNTER=str(counter),RACE_COMPLETION=record['completion'])
        for kind in ('completion','record'):
            counter.write_text('0'); self.env['RACE_KIND']=kind
            error = self.call(*self.reconcile_options(record),ok=False)
            self.assertIn('completion' if kind=='completion' else 'changed',error)
            self.assertNotIn('reconciled-lost',self.comments.read_text())
            if kind=='completion': Path(record['completion']).unlink()

    def test_supervisor_owns_lock_but_orphaned_cli_does_not_inherit_it(self):
        self.env['FAKE_HOLD'] = str(self.root/'executor-release')
        record = self.start(); self.await_run()
        child = json.loads(Path(record['output']).read_text())['pid']
        try:
            with open(record['supervisor_lock'],'r+') as stream:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                os.kill(record['pid'],signal.SIGKILL)
                deadline=time.monotonic()+3
                while True:
                    try:
                        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                    except BlockingIOError:
                        if time.monotonic()>deadline: raise
                        time.sleep(.02)
                os.kill(child,0)  # The orphan still exists, so an unlocked lock is not completion.
            self.assertIn('lost or unknown',self.call(*self.continuation_options(),ok=False))
            self.assertFalse(Path(record['completion']).exists())
        finally:
            os.killpg(record['pid'],signal.SIGKILL)

    def test_malformed_lifecycle_artifacts_refuse_without_reuse(self):
        record = self.start(); self.finish(record)
        Path(record['completion']).write_text('done\n')
        self.assertIn('malformed completion',self.call(*self.continuation_options(),ok=False))
        Path(record['completion']).unlink()
        changed = dict(record,supervisor_lock=str(self.root/'unrelated.lock'))
        self.replace_run(changed)
        self.assertIn('malformed supervisor_lock',self.call(*self.continuation_options(),ok=False))
        self.assertFalse(Path(changed['supervisor_lock']).exists())
        self.replace_run(record)
        marker = Path(record['completion'])
        os.mkfifo(marker)
        result = subprocess.run([sys.executable,str(self.script),'12','--project',str(self.project),
            *self.continuation_options()],env=self.env,text=True,capture_output=True,timeout=3)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('malformed completion',result.stderr)

    def test_reconcile_holds_existing_lock_through_exact_comment_patch(self):
        record = self.lost_record()
        self.env['CHECK_PATCH_LOCK']=record['supervisor_lock']
        source = (self.bin/'gh').read_text()
        source=source.replace(" if '/issues/comments/' in a[1]:", """ if '/issues/comments/' in a[1]:
  if os.environ.get('CHECK_PATCH_LOCK'):
   import fcntl
   with open(os.environ['CHECK_PATCH_LOCK'],'r+') as lock:
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: pass
    else: raise SystemExit('reconciliation released lock before patch')
""")
        (self.bin/'gh').write_text(source)
        self.assertEqual(self.call(*self.reconcile_options(record))['status'],'reconciled-lost')

    def test_reconcile_refuses_ambiguous_or_wrong_lane_record(self):
        record = self.lost_record()
        original = self.comments.read_text()
        rows=json.loads(original);rows.append(dict(rows[-1],id=98))
        self.comments.write_text(json.dumps(rows))
        self.assertIn('exactly one',self.call(*self.reconcile_options(record),ok=False))
        self.comments.write_text(original)
        self.replace_run(dict(record,lane_id='another-lane'))
        self.assertIn('current recorded lane',self.call(*self.reconcile_options(record),ok=False))

    def test_wait_cancel_after_reaping_never_signals_reused_diagnostic_group(self):
        import runpy
        sys.path.insert(0,str(SOURCE/'scripts'))
        try:
            module=runpy.run_path(str(self.script))
        finally:
            sys.path.pop(0)
        unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)'],start_new_session=True)
        completed=subprocess.Popen([sys.executable,'-c','pass']);completed.wait()
        # Simulate the diagnostic number being reused after our owned child was reaped.
        completed.pid=unrelated.pid
        wait=module['wait_process']
        wait.__globals__['completion_exit']=lambda record: signal.raise_signal(signal.SIGTERM)
        try:
            with self.assertRaises(module['Refusal']): wait(completed,{})
            time.sleep(.1)
            self.assertIsNone(unrelated.poll())
        finally:
            if unrelated.poll() is None: unrelated.terminate()
            unrelated.wait()

    def test_red_default_branch_refuses_before_lane_creation(self):
        self.env['DEFAULT_CI'] = json.dumps({'default_branch': 'main', 'owner': {'login': 'o'},
            'commit': {'sha': 'abc'},
            'check_runs': [{'name': 'test', 'status': 'completed', 'conclusion': 'failure'}], 'statuses': []})
        self.assertIn('default-branch CI', self.call('--purpose', 'worker', '--base', 'origin/main', ok=False))
        self.assertFalse((self.project/'.claude').exists())
        self.assertEqual(json.loads(self.comments.read_text()), [])

    def observed_checks(self, *checks):
        """Publish the default branch's observed check runs for the lane-creation gate."""
        self.env['DEFAULT_CI'] = json.dumps({'default_branch': 'main', 'owner': {'login': 'o'},
            'commit': {'sha': 'abc'},
            'check_runs': [{'name': name, 'status': 'completed', 'conclusion': conclusion}
                           for name, conclusion in checks], 'statuses': []})

    def test_a_head_whose_every_check_is_green_admits_a_lane(self):
        """#326: no check name is configured anywhere, so no project renames its job for this."""
        self.observed_checks(('tests', 'success'), ('cycle-pr', 'success'),
                             ('notebook-english', 'success'))
        run = self.start(); self.finish(run)
        self.assertEqual(self.lane_records()[0]['branch'], 'task/12-a-small-task')

    def test_a_red_head_refuses_and_names_the_check_that_failed(self):
        self.observed_checks(('tests', 'success'), ('cycle-pr', 'failure'))
        error = self.call('--purpose', 'worker', '--base', 'origin/main', ok=False)
        self.assertIn('default-branch CI', error)
        self.assertIn("'cycle-pr': 'failure'", error)
        self.assertFalse((self.project/'.claude').exists())
        self.assertEqual(self.lane_records(), [])

    def test_eighth_round_worker_continuation_refuses_before_launch(self):
        run = self.start(); self.finish(run)
        head = self.git('rev-parse', run['branch'])
        (self.root/'pr.json').write_text(json.dumps(dict(number=13, url='https://github.com/o/r/pull/13',
            state='OPEN', headRefName=run['branch'], headRefOid=head)))
        rows = [{'id':i, 'user':{'login':'o'}, 'body':f'## Merge check 1 — round {i}\nReviewer: Probe — reviewed {head}\n'} for i in range(1,8)]
        self.env['REVIEW_COMMENTS'] = json.dumps(rows)
        brief = self.root/'continue.txt'; brief.write_text('Repair the goal gap.')
        before = self.comments.read_text()
        self.assertIn('7 review rounds', self.call('--purpose','worker','--continue','--pr','13','--brief',str(brief),ok=False))
        self.assertEqual(self.comments.read_text(), before)

    def test_accepted_recovery_continuation_keeps_the_delivered_lane(self):
        import runpy
        verdicts = runpy.run_path(str(SOURCE / '.github/test-review-packet.py'))
        first = self.start()
        self.finish(first)
        head = self.git('rev-parse', first['branch'])
        pr = dict(number=13, url='https://github.com/o/r/pull/13', state='OPEN', mergedAt=None,
                  headRefName=first['branch'], headRefOid=head)
        Path(self.env['PR']).write_text(json.dumps(pr))
        row = dict(id=1, user=dict(login='o'), body='## Merge check 1 — round 1\n' +
                   verdicts['canonical_verdict'](head))
        rule = dict(kind='ruling', round=1, head=head, decision='continue', reason='Rebase the accepted lane.')
        def rows():
            return json.dumps([row, dict(id=2, user=dict(login='o'),
                body='## Review ruling — after round 1\n\n<!-- devstandard-review-v1 -->\n```json\n' +
                     json.dumps(rule) + '\n```\n')])
        self.env['REVIEW_COMMENTS'] = rows()
        brief = self.root / 'continue.txt'
        brief.write_text('Rebase the accepted head onto current main and repeat the done-check.')
        before = self.comments.read_text()
        self.assertIn('Notes', self.call('--purpose', 'worker', '--continue', '--pr', '13',
                                        '--brief', str(brief), ok=False))
        self.assertEqual(self.comments.read_text(), before)
        (self.project / 'main.txt').write_text('Main advanced.\n')
        self.git('add', 'main.txt')
        self.git('commit', '-m', 'advance main')
        base = self.git('rev-parse', 'HEAD')
        rule['recovery'] = dict(kind='behind-base', head=head, base=base)
        self.env['REVIEW_COMMENTS'] = rows()
        continued = self.call('--purpose', 'worker', '--continue', '--pr', '13',
                              '--implementation', 'codex', '--brief', str(brief))
        self.finish(continued)
        for key in ('lane_id', 'branch', 'worktree'):
            self.assertEqual(continued[key], first[key])
        self.assertEqual(continued['pr'], pr['url'])

    def test_missing_fields_refused_before_any_lane_side_effect(self):
        for field in ['Goal', 'Bounds', 'Done-check']:
            with self.subTest(field=field):
                d=json.loads(self.issue.read_text()); original=d['body']
                d['body']=original.replace('## '+field, '## Other')
                self.issue.write_text(json.dumps(d))
                error=self.call('--purpose','worker','--base','origin/main',ok=False)
                self.assertIn(field.lower(),error.lower())
                self.assertFalse((self.project/'.claude').exists())
                self.assertEqual(json.loads(self.comments.read_text()),[])
                d['body']=original; self.issue.write_text(json.dumps(d))
        self.assertIn('base',self.call('--purpose','worker',ok=False))
        self.assertFalse((self.project/'.claude').exists())
        self.assertEqual(json.loads(self.comments.read_text()),[])

    def test_branch_and_worktree_defaults_are_deterministic_and_recorded(self):
        run=self.start();self.finish(run)
        lane=self.lane_records()[0]
        self.assertEqual(lane['kind'],'lane')
        self.assertEqual(lane['branch'],'task/12-a-small-task')
        self.assertEqual(lane['worktree'],str(self.project/'.claude/worktrees/12-a-small-task'))
        self.assertEqual(lane['base'],'origin/main')
        self.assertEqual(lane['base_sha'],self.git('rev-parse','origin/main'))
        self.assertEqual(run['lane_id'],lane['lane_id'])

    def test_detached_worker_has_filled_role_and_both_git_grants(self):
        self.env['DEVSTANDARD_ROLE']='orchestrator'
        self.env['FAKE_HOLD']=str(self.root/'release')
        run=self.start()
        os.kill(run['pid'],0)
        self.assertNotEqual(os.getsid(run['pid']),os.getsid(0))
        data=self.finish(run); a=data['args']
        self.assertEqual(data['role'], 'worker')
        self.assert_role_config(a, 'worker')
        config = next((x for x in a if x.startswith('hooks.PreToolUse=')), '')
        self.assertIn('--role worker', config)
        self.assertIn('features.hooks=true', a)
        self.assertIn('--dangerously-bypass-hook-trust', a)
        self.assertIn(str(SOURCE/'hooks/pre-tool-use'), config)
        self.assertEqual(data['stdin'],'')
        self.assertEqual(a[a.index('-s')+1],'workspace-write')
        self.assertIn('sandbox_workspace_write.network_access=true',a)
        grants=[a[i+1] for i,x in enumerate(a) if x=='--add-dir']
        self.assertEqual(set(grants),{str(self.project/'.git'),str(self.project/'.git/worktrees'/Path(run['worktree']).name)})
        self.assertIn('This brief is what makes you a worker',a[-1])
        self.assertNotIn('{ISSUE_LINK_OR_SPEC}',a[-1])
        self.assertIn('Produce evidence.',a[-1])
        self.assertIn('executor started',Path(run['log']).read_text())
        self.assertEqual(Path(run['completion']).read_text().strip(),'0')
        self.assertIn(run['branch'],self.comments.read_text())
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),2)

    def test_codex_detaches_without_external_session_utilities(self):
        self.without_detachment_tools()
        run = self.start()
        data = self.finish(run)
        self.assertEqual(data['sid'], run['pid'])
        self.assertNotEqual(data['sid'], os.getsid(0))
        self.assertEqual(Path(run['completion']).read_text().strip(), '0')

    def test_detached_executor_survives_session_hangup(self):
        self.env['FAKE_HOLD'] = str(self.root/'release')
        run = self.start()
        try:
            deadline = time.monotonic() + 8
            while not Path(run['output']).exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue(Path(run['output']).exists(), Path(run['log']).read_text())
            os.killpg(run['pid'], signal.SIGHUP)
        finally:
            self.finish(run)
        self.assertEqual(Path(run['completion']).read_text().strip(), '0')

    def test_executor_waits_for_run_publication(self):
        probe = self.root/'publication.json'
        self.env['PUBLICATION_PROBE'] = str(probe)
        run = self.start()
        self.finish(run)
        self.assertFalse(json.loads(probe.read_text())['started'])

    def test_failed_run_publication_does_not_start_executor(self):
        probe = self.root/'publication.json'
        self.env.update(PUBLICATION_PROBE=str(probe), REJECT_RUN_PUBLICATION='1')
        error = self.call('--purpose', 'worker', '--base', 'origin/main',
                          '--implementation', 'codex', ok=False)
        self.assertIn('fixture publication failed', error)
        observed = json.loads(probe.read_text())
        self.assertFalse(observed['started'])
        record = observed['record']
        self.assertFalse(Path(record['output']).exists())
        self.assertFalse(Path(record['brief']).with_name('launch').exists())
        self.assertEqual([row['kind'] for row in self.lane_records()], ['lane'])

    def test_setting_is_read_from_the_installed_role_source(self):
        install=self.root/'plugin'
        shutil.copytree(SOURCE/'scripts',install/'scripts')
        shutil.copytree(SOURCE/'reference',install/'reference')
        shutil.copytree(SOURCE/'hooks',install/'hooks')
        source=install/'reference/external-agent.md'
        import re
        source.write_text(source.read_text().replace(
            '| Implementation, tests, bug fixing, conflict resolution | `gpt-5.6-sol` at `high` | `opus` |',
            '| Implementation, tests, bug fixing, conflict resolution | `fixture-model` at `medium` | `opus` |'))
        self.script=install/'scripts/dispatch'
        native=self.start('--implementation','codex-native')
        instruction=json.loads(Path(native['instruction']).read_text())
        self.assertEqual((native['model'],native['effort']),('fixture-model','medium'))
        self.assertEqual((instruction['model'],instruction['reasoning_effort']),('fixture-model','medium'))
        continuation=self.root/'continue.txt';continuation.write_text('Continue with the configured executor.')
        run=self.call('--purpose','worker','--continue','--implementation','codex',
                      '--brief',str(continuation),'--native-finished')
        data=self.finish(run);a=data['args']
        self.assertEqual((run['model'],run['effort']),(native['model'],native['effort']))
        self.assertEqual(a[a.index('-m')+1],'fixture-model')
        self.assertIn('model_reasoning_effort=medium',a)
        self.assertIn('Co-Authored-By: Codex fixture-model medium <noreply@openai.com>',a[-1])

    def test_the_pinned_role_hook_rides_the_invocation_with_its_trust_bypass(self):
        """#326: the flag goes with the fixed hook this dispatcher checked, not with a setting."""
        run = self.start(); args = self.finish(run)['args']
        self.assertIn('--dangerously-bypass-hook-trust', args)
        self.assertTrue(any('--role worker' in arg and arg.startswith('hooks.PreToolUse=')
                            for arg in args))

    def test_missing_repository_role_hook_refuses_before_lane_creation(self):
        install = self.root/'plugin'
        shutil.copytree(SOURCE/'scripts',install/'scripts')
        shutil.copytree(SOURCE/'reference',install/'reference')
        self.script = install/'scripts/dispatch'
        self.assertIn('role hook', self.call('--purpose','worker','--base','origin/main',
                                             '--implementation','codex',ok=False))
        self.assertFalse((self.project/'.claude').exists())
        self.assertEqual(self.lane_records(), [])

    def test_invalid_inputs_leave_no_worktree_or_comments(self):
        for options in [('--base','HEAD'),('--base','missing/ref'),('--base',self.git('rev-parse','HEAD')),
                        ('--base','origin/main','--branch','bad branch'),
                        ('--base','origin/main','--packet',str(self.root/'absent'))]:
            # Worker packets are not accepted: they must not be silently ignored.
            self.call('--purpose','worker',*options,ok=False)
            self.assertFalse((self.project/'.claude').exists())
            self.assertEqual(json.loads(self.comments.read_text()),[])
        d=json.loads(self.issue.read_text());d['body']=d['body'].replace('Produce evidence.','{GOAL}')
        self.issue.write_text(json.dumps(d))
        self.assertIn('placeholder',self.call('--purpose','worker','--base','origin/main',ok=False))
        self.assertFalse((self.project/'.claude').exists())

    def test_nonzero_agent_exit_is_captured(self):
        self.env['FAKE_EXIT']='7'
        run=self.start();self.finish(run)
        self.assertEqual(Path(run['completion']).read_text().strip(),'7')

    def test_continuation_retains_lane_and_pr_and_rejects_live_writer(self):
        self.env['FAKE_HOLD']=str(self.root/'release')
        run=self.start()
        brief=self.root/'continue.txt';brief.write_text('Repair the missing evidence only.')
        (self.root/'pr.json').write_text(json.dumps(dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',headRefName=run['branch'],headRefOid=self.git('rev-parse',run['branch']))))
        self.assertIn('running', self.call('--purpose','worker','--continue','--brief',str(brief),'--pr','13',ok=False))
        self.finish(run)
        next_run=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief),'--pr','13')
        data=self.finish(next_run)
        self.assertEqual(next_run['branch'],run['branch']);self.assertEqual(next_run['worktree'],run['worktree'])
        self.assertIn('Repair the missing evidence only.',data['args'][-1])
        self.assertIn('https://github.com/o/r/pull/13',data['args'][-1])
        self.assertNotEqual(next_run['output'],run['output'])
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),2)
        self.assertIn('existing open --pr',self.call('--purpose','worker','--continue','--brief',str(brief),ok=False))
        pr=json.loads((self.root/'pr.json').read_text());pr.update(number=14,url='https://github.com/o/r/pull/14')
        (self.root/'pr.json').write_text(json.dumps(pr))
        self.assertIn('differs',self.call('--purpose','worker','--continue','--brief',str(brief),'--pr','14',ok=False))

    def test_pre_pr_continuation_reuses_recorded_lane(self):
        self.env['FAKE_HOLD']=str(self.root/'release')
        run=self.start()
        brief=self.root/'continue.txt';brief.write_text('Continue after the receipt escalation.')
        self.assertIn('running',self.call('--purpose','worker','--continue','--brief',str(brief),ok=False))
        self.finish(run)
        self.assertIn('--brief',self.call('--purpose','worker','--continue',ok=False))
        continued=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief))
        data=self.finish(continued)
        for key in ('lane_id','branch','worktree','base','base_sha'):
            self.assertEqual(continued[key],run[key])
        self.assertIsNone(continued['pr'])
        self.assertIn(brief.read_text(),data['args'][-1])
        self.assertNotIn('\nPR:',data['args'][-1])
        self.assertEqual(len([r for r in self.lane_records() if r['kind']=='lane']),1)
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),2)
        # A worker may have opened a PR without another dispatcher observation.
        (self.root/'pr.json').write_text(json.dumps(dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',headRefName=run['branch'],headRefOid=self.git('rev-parse',run['branch']))))
        self.assertIn('existing open --pr',self.call('--purpose','worker','--continue','--brief',str(brief),ok=False))

    def test_adopted_lane_supports_review_and_pre_pr_continuation(self):
        branch,wt=self.hand_made_lane()
        before=self.git('rev-parse',branch)
        lane=self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main')
        self.assertEqual(lane['kind'],'lane');self.assertEqual(lane['status'],'adopted')
        self.assertEqual(lane['branch'],branch);self.assertEqual(lane['worktree'],str(wt))
        self.assertEqual(self.lane_records(),[lane])
        self.assertEqual(self.git('rev-parse',branch),before)
        self.assertNotIn('pid',lane)
        packet=self.review_packet()
        review=self.call('--purpose','reviewer','--implementation','codex','--packet',str(packet))
        a=self.finish(review)['args']
        self.assertEqual(a[a.index('-s')+1],'read-only')
        brief=self.root/'continue.txt';brief.write_text('Continue the adopted work.')
        continued=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief));self.finish(continued)
        self.assertEqual(continued['lane_id'],lane['lane_id'])
        self.assertEqual(continued['worktree'],str(wt))
        self.assertIn('lane exists',self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main',ok=False))

    def test_adoption_records_pr_and_continuation_keeps_it(self):
        branch,wt=self.hand_made_lane()
        pr=dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',headRefName=branch,headRefOid=self.git('rev-parse',branch))
        (self.root/'pr.json').write_text(json.dumps(pr))
        lane=self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main','--pr','13')
        self.assertEqual(lane['pr'],pr['url'])
        brief=self.root/'continue.txt';brief.write_text('Repair the delivered lane.')
        self.assertIn('existing open --pr',self.call('--purpose','worker','--continue','--brief',str(brief),ok=False))
        continued=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief),'--pr','13');self.finish(continued)
        self.assertEqual(continued['pr'],pr['url']);self.assertEqual(continued['lane_id'],lane['lane_id'])
        pr['state']='CLOSED';(self.root/'pr.json').write_text(json.dumps(pr))
        self.assertIn('existing open --pr',self.call('--purpose','worker','--continue','--brief',str(brief),'--pr','13',ok=False))

    def test_adoption_refuses_missing_or_mismatched_lane_without_side_effects(self):
        branch,wt=self.hand_made_lane()
        for options in [('--branch',branch),('--worktree',str(wt)),
                        ('--branch','feat/absent','--worktree',str(wt)),
                        ('--branch',branch,'--worktree',str(self.root/'absent')),
                        ('--branch','main','--worktree',str(wt)),
                        ('--branch','main','--worktree',str(self.project)),
                        ('--branch',branch,'--worktree',str(wt),'--continue')]:
            with self.subTest(options=options):
                self.call('--adopt','--base','origin/main',*options,ok=False)
                self.assertEqual(self.lane_records(),[])
                self.assertTrue(wt.exists())
                self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),2)
        self.assertIn('base',self.call('--adopt','--branch',branch,'--worktree',str(wt),ok=False))
        self.assertEqual(self.lane_records(),[])
        (self.root/'pr.json').write_text(json.dumps(dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',headRefName='feat/other')))
        self.assertIn('PR branch differs',self.call('--adopt','--base','origin/main','--branch',branch,'--worktree',str(wt),'--pr','13',ok=False))
        self.assertEqual(self.lane_records(),[])

    def test_reviewer_reuses_lane_read_only_and_preserves_packet(self):
        run=self.start();self.finish(run)
        self.env['DEVSTANDARD_ROLE']='worker'
        packet=self.review_packet()
        review=self.call('--purpose','reviewer','--implementation','codex','--packet',str(packet))
        data=self.finish(review);a=data['args']
        self.assertEqual(data['role'], 'reviewer')
        self.assert_role_config(a, 'reviewer')
        self.assertIn('--dangerously-bypass-hook-trust',a)
        self.assertTrue(any('--role reviewer' in arg and arg.startswith('hooks.PreToolUse=') for arg in a))
        self.assertEqual(a[a.index('-s')+1],'read-only');self.assertNotIn('--add-dir',a);self.assertNotIn('sandbox_workspace_write.network_access=true',a)
        self.assertIn('Complete report.',a[-1]);self.assertEqual(review['worktree'],run['worktree'])

    def test_default_implementation_is_the_hosts_own_subagent(self):
        """#332: installed Codex no longer selects itself; the default is the host's subagent."""
        self.assertTrue(shutil.which('codex', path=str(self.bin)))
        run = self.call('--purpose', 'worker', '--base', 'origin/main')
        self.assertEqual(run['implementation'], 'claude')
        self.assertEqual(run['status'], 'awaiting-agent-tool')
        self.assertNotIn('pid', run)
        self.assertEqual([r['implementation'] for r in self.lane_records() if r['kind'] == 'run'],
                         ['claude'])

    def test_chosen_codex_fails_plainly_when_codex_is_absent(self):
        """#332: the named executor is the one that runs — a missing Codex refuses, never falls back."""
        (self.bin/'codex').unlink()
        self.env['PATH'] = os.pathsep.join(d for d in self.env['PATH'].split(os.pathsep)
                                           if not shutil.which('codex', path=d))
        error = self.call('--purpose', 'worker', '--base', 'origin/main',
                          '--implementation', 'codex', ok=False)
        self.assertIn('codex is not installed', error)
        self.assertFalse((self.project/'.claude').exists())
        self.assertEqual(self.lane_records(), [])

    def test_purpose_selects_distinct_codex_worker_and_reviewer_models(self):
        worker = self.start('--implementation', 'codex-native')
        self.assertEqual((worker['model'], worker['effort']), ('gpt-5.6-sol', 'high'))
        packet = self.review_packet()
        review = self.call('--purpose', 'reviewer', '--implementation', 'codex',
                           '--packet', str(packet), '--native-finished')
        args = self.finish(review)['args']
        self.assertEqual((review['model'], review['effort']), ('gpt-6-astra', 'high'))
        self.assertEqual(args[args.index('-m') + 1], 'gpt-6-astra')
        self.assertIn('model_reasoning_effort=high', args)

    def test_explicit_model_and_effort_override_independently_on_each_executor(self):
        for implementation in ('codex', 'codex-native', 'claude', 'claude-cli'):
            default = 'gpt-5.6-sol' if implementation.startswith('codex') else 'opus'
            for flags, expected in [(('--model', 'override-model'), ('override-model', 'high')),
                                    (('--effort', 'low'), (default, 'low')),
                                    (('--model', 'override-model', '--effort', 'low'),
                                     ('override-model', 'low'))]:
                with self.subTest(implementation=implementation, flags=flags):
                    fixture = DispatchTest(); fixture.setUp()
                    try:
                        run = fixture.start('--implementation', implementation, *flags)
                        self.assertEqual((run['model'], run['effort']), expected)
                        self.assertIn(' '.join(expected), Path(run['brief']).read_text())
                        if implementation in ('claude', 'codex-native'):
                            instruction = json.loads(Path(run['instruction']).read_text())
                            key = 'reasoning_effort' if implementation == 'codex-native' else 'effort'
                            self.assertEqual((instruction['model'], instruction[key]), expected)
                        elif implementation == 'codex':
                            args = fixture.finish(run)['args']
                            self.assertEqual(args[args.index('-m') + 1], expected[0])
                            self.assertIn('model_reasoning_effort=' + expected[1], args)
                        else:
                            args = json.loads(fixture.finish_claude(run)[1]['result'])['args']
                            self.assertEqual((args[args.index('--model') + 1],
                                              args[args.index('--effort') + 1]), expected)
                        self.assertEqual((fixture.lane_records()[-1]['model'],
                                          fixture.lane_records()[-1]['effort']), expected)
                    finally:
                        fixture.doCleanups()

    def test_claude_returns_agent_instruction_without_claiming_launch(self):
        run=self.start('--implementation','claude')
        self.assertEqual(run['status'],'awaiting-agent-tool')
        spawn=json.loads(Path(run['instruction']).read_text())
        self.assertEqual(spawn['subagent_type'],'devstandard:worker')
        self.assertEqual((spawn['model'], spawn['effort']), ('opus', 'high'))
        self.assertIn('Executor: Claude opus high', spawn['prompt'])
        self.assertIn('Produce evidence.',spawn['prompt'])
        self.assertNotIn('pid',run)
        self.assertNotIn('--dangerously-bypass-hook-trust',json.dumps(spawn))
        packet=self.review_packet(identity='Codex, stale-model at low, read-only')
        review=self.call('--purpose','reviewer','--implementation','claude','--packet',str(packet),'--native-finished')
        instruction = json.loads(Path(review['instruction']).read_text())
        self.assertEqual(instruction['subagent_type'],'devstandard:reviewer')
        self.assertEqual((instruction['model'], instruction['effort']), ('opus', 'high'))
        self.assertIn('Claude subagent, opus at high, read-only', Path(review['brief']).read_text())

    def assert_native_canonical_brief(self, run):
        instruction = json.loads(Path(run['instruction']).read_text())
        saved = Path(run['brief']).read_bytes()
        digest = hashlib.sha256(saved).hexdigest()
        self.assertTrue(Path(run['brief']).is_absolute())
        self.assertEqual(instruction.get('brief'), run['brief'])
        self.assertEqual(instruction.get('brief_sha256'), digest)
        self.assertEqual(run.get('brief_sha256'), digest)
        inline = saved.decode('utf-8')
        self.assertTrue(instruction['message'].endswith(inline))
        preamble = instruction['message'][:-len(inline)]
        self.assertIn(run['brief'], preamble)
        self.assertIn(digest, preamble)
        self.assertIn('IN FULL', preamble)
        self.assertIn('authoritative', preamble)
        self.assertIn('blocked', preamble)
        self.assertTrue(inline.startswith('# Worker\n'))
        self.assertNotIn(digest, inline)

    def test_native_codex_prepares_full_worker_without_codex_cli(self):
        self.without_detachment_tools()
        (self.bin/'codex').unlink()
        run = self.start('--implementation', 'codex-native')
        self.assertEqual(run['status'], 'awaiting-agent-tool')
        self.assertEqual(run['implementation'], 'codex-native')
        self.assertEqual((run['model'], run['effort']), ('gpt-5.6-sol', 'high'))
        self.assertFalse({'pid', 'output', 'completion'} & run.keys())
        self.assertEqual(self.lane_records()[-1], run)
        instruction = json.loads(Path(run['instruction']).read_text())
        self.assertEqual(instruction['format'], 'devstandard-codex-native-v1')
        self.assertEqual((instruction['model'], instruction['reasoning_effort']), ('gpt-5.6-sol', 'high'))
        self.assertTrue(instruction['fresh_conversation'])
        self.assertEqual(instruction['worktree'], run['worktree'])
        self.assert_native_canonical_brief(run)
        self.assertIn('This brief is what makes you a worker', instruction['message'])
        self.assertIn('Produce evidence.', instruction['message'])
        self.assertIn('Worktree: ' + run['worktree'], instruction['message'])
        self.assertIn('Co-Authored-By: Codex native subagent', instruction['message'])
        self.assertIn('<noreply@openai.com>', instruction['message'])
        self.assertNotIn('subagent_type', instruction)
        self.assertNotIn('run_in_background', instruction)
        self.assertFalse(Path(run['brief']).with_name('command.json').exists())

    def test_native_codex_reviewer_refuses_inherited_permissions_before_writes(self):
        before = set(self.root.iterdir())
        error = self.call('--purpose', 'reviewer', '--implementation', 'codex-native', ok=False)
        self.assertIn('inherit', error)
        self.assertIn('read-only', error)
        self.assertIn('--implementation codex', error)
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertEqual(self.lane_records(), [])
        self.assertEqual(self.git('worktree', 'list', '--porcelain').count('worktree '), 1)

    def test_native_codex_continuation_is_fresh_in_the_same_lane(self):
        first = self.start('--implementation', 'codex-native')
        original = Path(first['brief']).read_bytes()
        self.assert_native_canonical_brief(first)
        brief = self.root/'continue.txt'
        brief.write_text('Finish the evidence for the existing lane.')
        options = ('--purpose', 'worker', '--implementation', 'codex-native',
                   '--continue', '--brief', str(brief))
        self.assertIn('running', self.call(*options, ok=False))
        self.assertIn('--resume', self.call(*options, '--native-finished', '--resume', 'native-handle', ok=False))
        continued = self.call(*options, '--native-finished')
        for key in ('lane_id', 'branch', 'worktree', 'base', 'base_sha'):
            self.assertEqual(continued[key], first[key])
        self.assertNotEqual(continued['instruction'], first['instruction'])
        self.assertNotEqual(continued['brief'], first['brief'])
        self.assertNotEqual(continued['brief_sha256'], first['brief_sha256'])
        self.assertEqual(Path(first['brief']).read_bytes(), original)
        self.assert_native_canonical_brief(continued)
        instruction = json.loads(Path(continued['instruction']).read_text())
        self.assertTrue(instruction['fresh_conversation'])
        self.assertIn(brief.read_text(), instruction['message'])
        self.assertEqual(self.git('worktree', 'list', '--porcelain').count('worktree '), 2)

    def test_native_codex_failed_publication_returns_no_spawn_instruction(self):
        self.env['REJECT_RUN_PUBLICATION'] = '1'
        result = subprocess.run([sys.executable, str(self.script), '12', '--purpose', 'worker',
            '--implementation', 'codex-native', '--base', 'origin/main', '--project', str(self.project)],
            env=self.env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('fixture publication failed', result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual([row['kind'] for row in self.lane_records()], ['lane'])

    def test_claude_cli_launches_worker_with_full_stdin_and_preserves_denials(self):
        self.without_detachment_tools()
        self.env['DEVSTANDARD_ROLE'] = 'orchestrator'
        denials = [dict(tool_name='Bash', tool_use_id='denied-call', tool_input={'command': 'git push'})]
        self.env['FAKE_CLAUDE_DENIALS'] = json.dumps(denials)
        run = self.start('--implementation', 'claude-cli')
        events = self.finish_claude(run)
        self.assertEqual([event['type'] for event in events], ['system', 'result', 'result'])
        result = events[1]
        data = json.loads(result['result'])
        self.assertEqual(data['args'], ['--print', '--plugin-dir', str(SOURCE), '--agent', 'devstandard:worker',
            '--permission-mode', 'acceptEdits', '--permission-prompts', 'none', '--output-format', 'stream-json', '--verbose',
            '--no-session-persistence', '--model', 'opus', '--effort', 'high'])
        self.assertEqual((run['model'], run['effort']), ('opus', 'high'))
        self.assertEqual((run['permission_mode'], run['output_format']), ('acceptEdits', 'stream-json'))
        self.assertEqual(Path(run['output']).name, 'output.jsonl')
        self.assertEqual(run['sandbox'], 'host')
        self.assertEqual(data['role'], 'worker')
        self.assertEqual(data['cwd'], run['worktree'])
        self.assertEqual(data['sid'], run['pid'])
        self.assertEqual(data['stdin'], Path(run['brief']).read_text())
        self.assertIn('This brief is what makes you a worker', data['stdin'])
        self.assertIn('Co-Authored-By: Claude opus high <noreply@anthropic.com>', data['stdin'])
        self.assertEqual(result['permission_denials'], denials)
        self.assertEqual(events[-1]['permission_denials'], [])
        self.assertEqual(events[-1]['result'], 'Background agent finished.')
        self.assertIn('Claude executor started', Path(run['log']).read_text())
        self.assertEqual(Path(run['completion']).read_text().strip(), '0')
        self.assertNotIn('instruction', run)

    def test_claude_cli_uses_installed_routing_model_and_worker_effort(self):
        install = self.root/'plugin with spaces'
        for directory in ('scripts', 'reference', 'hooks', 'agents', '.claude-plugin'):
            shutil.copytree(SOURCE/directory, install/directory)
        worker = install/'agents/worker.md'
        worker.write_text(worker.read_text().replace('model: opus', 'model: fable').replace('effort: high', 'effort: medium'))
        page = install/'reference/external-agent.md'
        page.write_text(page.read_text().replace(
            '| Implementation, tests, bug fixing, conflict resolution | `gpt-5.6-sol` at `high` | `opus` |',
            '| Implementation, tests, bug fixing, conflict resolution | `gpt-5.6-sol` at `high` | `sonnet` |'))
        self.script = install/'scripts/dispatch'
        run = self.start('--implementation', 'claude-cli')
        args = json.loads(self.finish_claude(run)[1]['result'])['args']
        self.assertEqual(args[args.index('--plugin-dir')+1], str(install))
        self.assertEqual((run['model'], run['effort']), ('sonnet', 'medium'))
        self.assertEqual(args[args.index('--model')+1], 'sonnet')
        self.assertEqual(args[args.index('--effort')+1], 'medium')

    def test_missing_claude_cli_refuses_before_lane_creation(self):
        self.without_detachment_tools()
        (self.bin/'claude').unlink()
        error = self.call('--purpose', 'worker', '--implementation', 'claude-cli', '--base', 'origin/main', ok=False)
        self.assertIn('claude is not installed', error)
        self.assertFalse((self.project/'.claude').exists())
        self.assertEqual(self.lane_records(), [])

    def test_claude_cli_startup_failure_is_recorded_without_a_result(self):
        self.env['FAKE_CLAUDE_STARTUP_FAIL'] = '1'
        run = self.start('--implementation', 'claude-cli')
        self.wait_completion(run)
        self.assertEqual(Path(run['completion']).read_text().strip(), '9')
        self.assertIn('authentication unavailable', Path(run['log']).read_text())
        self.assertEqual(Path(run['output']).read_text(), '')

    def test_claude_cli_waits_for_run_publication(self):
        probe = self.root/'publication.json'
        self.env['PUBLICATION_PROBE'] = str(probe)
        run = self.start('--implementation', 'claude-cli')
        self.finish_claude(run)
        self.assertFalse(json.loads(probe.read_text())['started'])

    def test_claude_cli_failed_publication_does_not_start_executor(self):
        probe = self.root/'publication.json'
        self.env.update(PUBLICATION_PROBE=str(probe), REJECT_RUN_PUBLICATION='1')
        error = self.call('--purpose', 'worker', '--base', 'origin/main', '--implementation', 'claude-cli', ok=False)
        self.assertIn('fixture publication failed', error)
        observed = json.loads(probe.read_text())
        self.assertFalse(observed['started'])
        self.assertFalse(Path(observed['record']['output']).exists())
        self.assertFalse(Path(observed['record']['brief']).with_name('launch').exists())
        self.assertEqual([row['kind'] for row in self.lane_records()], ['lane'])

    def test_claude_cli_continuation_is_fresh_and_native_finished_does_not_clear_pid(self):
        self.env['FAKE_HOLD'] = str(self.root/'release')
        first = self.start('--implementation', 'claude-cli')
        brief = self.root/'continue.txt'; brief.write_text('Finish the existing work.')
        options = ('--purpose', 'worker', '--implementation', 'claude-cli', '--continue', '--brief', str(brief))
        self.assertIn('running', self.call(*options, '--native-finished', ok=False))
        self.finish_claude(first)
        self.assertIn('--resume', self.call(*options, '--resume', 'old-session', ok=False))
        second = self.call(*options)
        data = json.loads(self.finish_claude(second)[1]['result'])
        for key in ('lane_id', 'branch', 'worktree', 'base_sha'):
            self.assertEqual(first[key], second[key])
        for key in ('brief', 'output', 'completion'):
            self.assertNotEqual(first[key], second[key])
        self.assertIn(brief.read_text(), data['stdin'])
        self.assertNotIn('--resume', data['args'])
        self.assertNotIn('--continue', data['args'])

    def test_claude_cli_reviewer_refuses_before_writes(self):
        before = set(self.root.iterdir())
        error = self.call('--purpose', 'reviewer', '--implementation', 'claude-cli', ok=False)
        self.assertIn('read-only', error)
        self.assertIn('--implementation codex', error)
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertEqual(self.lane_records(), [])

    def test_reviewer_identity_is_filled_or_overridden_from_executor(self):
        run=self.start();self.finish(run)
        for implementation in ('codex','claude'):
            for supplied in ('{REVIEWER_IDENTITY}','Wrong reviewer, stale-model'):
                with self.subTest(implementation=implementation,supplied=supplied):
                    packet=self.review_packet(identity=supplied)
                    history='## PR fulfillment claim and evidence\nReviewer: Historical reviewer — reviewed old-head\n'
                    data=json.loads(packet.read_text());data['slots']['COMPLETE_PR_DESCRIPTION']=history
                    packet.write_text(json.dumps(data))
                    review=self.call('--purpose','reviewer','--implementation',implementation,
                                     '--packet',str(packet),'--native-finished')
                    if implementation=='codex':
                        a=self.finish(review)['args'];prompt=a[-1]
                        identity=f"Codex, {a[a.index('-m')+1]} at {a[a.index('-c')+1].split('=')[1]}, read-only"
                        self.assertNotIn('## Pinned Git evidence',prompt)
                    else:
                        prompt=Path(review['brief']).read_text()
                        identity='Claude subagent, opus at high, read-only'
                    self.assertIn(f'Reviewer: {identity} — reviewed',prompt)
                    self.assertIn(f'Reviewer identity: {identity}.',prompt)
                    self.assertNotIn(supplied,prompt)
                    self.assertIn(history,prompt)

    def test_claude_inlines_pinned_diffs_and_convention_blobs(self):
        doc=self.project/'guide.md';doc.write_text('Convention content.\n\n')
        old=self.project/'old name.md';old.write_text('Renamed content.\n')
        (self.project/' notes').write_text('')
        self.git('add','.');self.git('commit','-m','convention docs')
        convention=self.git('rev-parse','HEAD')
        doc.write_text('Review base content.\n')
        self.git('add','.');self.git('commit','-m','review base')
        base=self.git('rev-parse','HEAD')
        self.git('update-ref','refs/remotes/origin/main',base)
        run=self.start();self.finish(run);wt=Path(run['worktree'])
        (wt/'guide.md').write_text('Pinned head content.\n')
        (wt/'old name.md').rename(wt/'new name.md')
        (wt/'added.md').write_text('New documentation.\n')
        (wt/' notes').write_text('Prose without a documentation extension.\n')
        self.git('-C',str(wt),'add','.')
        self.git('-C',str(wt),'commit','-m','reviewed changes')
        head=self.git('rev-parse',run['branch'])
        packet=self.review_packet(base,head,convention,identity='Claude subagent, opus at high, read-only')
        # Neither the checkout nor a later branch tip may substitute for the pinned head.
        (wt/'guide.md').write_text('Later content must not appear.\n')
        self.git('-C',str(wt),'add','.')
        self.git('-C',str(wt),'commit','-m','later change')
        review=self.call('--purpose','reviewer','--implementation','claude','--packet',str(packet))
        prompt=Path(review['brief']).read_text()
        self.assertIn('## Pinned Git evidence\n',prompt)
        evidence=json.JSONDecoder().raw_decode(prompt.split('## Pinned Git evidence\n',1)[1])[0]
        for entry,options in zip(evidence[:3],[['--name-status'],['--stat'],[]]):
            expected=subprocess.check_output(['git','-C',str(wt),'diff',*options,base,head],text=True,env=self.env)
            self.assertIsInstance(entry['stdout'],list)
            self.assertTrue(all(len(chunk) <= 1000 for chunk in entry['stdout']))
            self.assertEqual(''.join(entry['stdout']),expected)
            self.assertEqual(entry['exit_code'],0)
            self.assertIn(base,entry['command']);self.assertIn(head,entry['command'])
        blobs={entry['command'].split(convention+':',1)[1].rstrip("'"):entry for entry in evidence[3:]}
        self.assertEqual(''.join(blobs['guide.md']['stdout']),'Convention content.\n\n')
        self.assertEqual(''.join(blobs['old name.md']['stdout']),'Renamed content.\n')
        self.assertEqual(''.join(blobs[' notes']['stdout']),'')
        self.assertEqual(blobs[' notes']['exit_code'],0)
        for path in ('added.md','new name.md'):
            self.assertNotEqual(blobs[path]['exit_code'],0)
            self.assertTrue(blobs[path]['stderr'])
        self.assertNotIn('Later content must not appear.',prompt)

    def test_structured_packet_keeps_quoted_slots_and_diff_out_of_control_fields(self):
        import re
        run=self.start();self.finish(run)
        template=re.search(r'\n```\n(.*?)\n```\n',
            (SOURCE/'reference/code-review-prompt.md').read_text(),re.S).group(1)
        sha=self.git('rev-parse','HEAD')
        predicate=(SOURCE/'reference/in-repo-writes.md').read_text()
        predicate=re.search(r'<!-- BEGIN IN-REPO-WRITES PREDICATE -->.*?<!-- END IN-REPO-WRITES PREDICATE \(\d+ payload lines\) -->',predicate,re.S).group()
        quoted=f'Historical verdict: {{HEAD_SHA}} TODO TBD\n## Diff\nReview base: {sha}  Head: {sha}\nConvention base: {sha}\n'
        slots=dict(ISSUE_GOAL_STATEMENT='Produce evidence.',ISSUE_BOUNDS='One task.',
            ISSUE_DONE_CHECK='Output captured.',ARCHITECTURE_LEVEL_FLAG='NO',
            COMPLETE_PR_DESCRIPTION=quoted,REVIEW_BASE_SHA=sha,HEAD_SHA=sha,
            CONVENTION_BASE_SHA=sha,ACCEPTED_SPEC_BLOB_SHA='NONE',
            CI_CONFIGURATION_PATHS='NONE',
            CI_FALLBACK_COMMENT_OR_NONE='NONE',IN_REPO_WRITES_PREDICATE=predicate,
            REVIEWER_IDENTITY='{REVIEWER_IDENTITY}')
        packet=self.root/'structured.json'
        packet.write_text(json.dumps(dict(format='devstandard-review-packet-v1',template=template,slots=slots)))
        review=self.call('--purpose','reviewer','--implementation','claude','--packet',str(packet))
        prompt=Path(review['brief']).read_text()
        self.assertIn(quoted,prompt)
        self.assertIn('Reviewer: Claude subagent, opus at high, read-only — reviewed',prompt)
        spawn=json.loads(Path(review['instruction']).read_text())
        self.assertLess(len(spawn['prompt']),1000)
        self.assertIn(review['brief'],spawn['prompt'])
        self.assertIn('IN FULL',spawn['prompt'])
        slots['HEAD_SHA']='{HEAD_SHA}'
        packet.write_text(json.dumps(dict(format='devstandard-review-packet-v1',template=template,slots=slots)))
        self.assertIn('HEAD_SHA',self.call('--purpose','reviewer','--implementation','claude',
            '--packet',str(packet),'--native-finished',ok=False))

    def test_claude_refuses_failed_git_evidence_before_writes(self):
        run=self.start();self.finish(run)
        packet=self.review_packet(identity='Claude subagent, opus at high, read-only')
        real_git=shutil.which('git')
        self.tool('git',f'''import os,sys
if '--stat' in sys.argv:
 print('fixture diff failure',file=sys.stderr);sys.exit(1)
os.execv({real_git!r},[{real_git!r},*sys.argv[1:]])
''')
        before=self.comments.read_text();files=set(self.root.iterdir())
        error=self.call('--purpose','reviewer','--implementation','claude','--packet',str(packet),ok=False)
        self.assertIn('fixture diff failure',error)
        self.assertEqual(self.comments.read_text(),before)
        self.assertEqual(set(self.root.iterdir()),files)

    def test_claude_refuses_unpinned_or_unreachable_evidence_before_writes(self):
        run=self.start();self.finish(run)
        good=self.review_packet(identity='Claude subagent, opus at high, read-only').read_text()
        sha=self.git('rev-parse','origin/main')
        packet=self.root/'review.txt'
        for bad in ('Incomplete packet.',good.replace(sha,'origin/main'),good.replace(sha,'f'*40)):
            with self.subTest(packet=bad):
                packet.write_text(bad)
                before=self.comments.read_text();files=set(self.root.iterdir())
                self.call('--purpose','reviewer','--implementation','claude','--packet',str(packet),'--native-finished',ok=False)
                self.assertEqual(self.comments.read_text(),before)
                self.assertEqual(set(self.root.iterdir()),files)

    def test_native_finished_attests_all_prior_native_runs_but_not_codex(self):
        first=self.start('--implementation','codex-native')
        packet=self.review_packet(identity='Claude subagent, opus at high, read-only')
        options=('--purpose','reviewer','--implementation','claude','--packet',str(packet))
        self.assertIn('running',self.call(*options,ok=False))
        second=self.call(*options,'--native-finished')
        self.assertNotEqual(first['instruction'],second['instruction'])
        self.assertIn('running',self.call(*options,ok=False))
        self.env['FAKE_HOLD']=str(self.root/'release')
        running=self.call('--purpose','reviewer','--implementation','codex','--packet',str(packet),'--native-finished')
        self.assertIn('running',self.call(*options,'--native-finished',ok=False))
        self.finish(running)
        cleanup=self.call('--cleanup','--discard','--native-finished')
        self.assertEqual(cleanup['status'],'cleaned')

    def test_cleanup_requires_merge_and_preserves_dirty_work(self):
        run=self.start();self.finish(run)
        pr=dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',mergedAt=None,headRefName=run['branch'],headRefOid=self.git('rev-parse',run['branch']))
        (self.root/'pr.json').write_text(json.dumps(pr))
        self.assertIn('merged',self.call('--cleanup','--pr','13',ok=False))
        pr.update(state='MERGED',mergedAt='2026-01-01T00:00:00Z');(self.root/'pr.json').write_text(json.dumps(pr))
        stray=Path(run['worktree'])/'stray';stray.write_text('keep')
        self.assertIn('dirty',self.call('--cleanup','--pr','13',ok=False));self.assertTrue(stray.exists())
        stray.unlink()
        self.call('--cleanup','--pr','13')
        self.assertFalse(Path(run['worktree']).exists())
        self.assertNotIn(run['branch'],self.git('branch','--list'))

    def test_cleanup_after_worker_commits_and_real_git_squash_merge(self):
        self.env['FAKE_COMMITS']='1'
        run=self.start();self.finish(run)
        self.assertEqual(self.git('rev-list','--count','origin/main..'+run['branch']),'2')
        head=self.git('rev-parse',run['branch'])
        self.git('merge','--squash',run['branch']);self.git('commit','-m','squash worker PR')
        self.git('update-ref','refs/remotes/origin/main','HEAD')
        self.assertNotEqual(head,self.git('rev-parse','origin/main'))
        self.assertEqual(self.git('diff','origin/main',run['branch']),'')
        pr=dict(number=13,url='https://github.com/o/r/pull/13',state='MERGED',mergedAt='2026-01-01T00:00:00Z',headRefName=run['branch'],headRefOid=head)
        (self.root/'pr.json').write_text(json.dumps(pr))
        error=self.call('--cleanup','--pr','13',ok=False)
        self.assertIn('worker step 0',error);self.assertIn('worker step 1',error)
        self.assertIn('--force-delete',error)
        self.assertTrue(Path(run['worktree']).exists());self.assertEqual(self.git('rev-parse',run['branch']),head)
        # Even explicit -D authority cannot discard commits beyond the merged PR head.
        self.git('-C',run['worktree'],'commit','--allow-empty','-m','unpublished work')
        self.assertIn('unpublished work',self.call('--cleanup','--pr','13','--force-delete',ok=False))
        self.git('-C',run['worktree'],'reset','--hard',head)
        cleanup=self.call('--cleanup','--pr','13','--force-delete')
        self.assertEqual(cleanup['status'],'cleaned')
        self.assertFalse(Path(run['worktree']).exists())
        self.assertEqual(self.git('branch','--list',run['branch']),'')
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),1)
        self.assertEqual(self.lane_records()[-1],cleanup)


if __name__ == '__main__':
    unittest.main()
