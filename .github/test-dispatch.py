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
        self.assertEqual(parsed.get('agents.default_subagent_reasoning_effort'), 'medium')
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
def w(rows): t=c.with_name(c.name+'.tmp'); t.write_text(json.dumps(rows)); os.replace(t,c)
if a[:2]==['repo','view']: print('o/r')
elif a[:1]==['api']:
 if '/issues/comments/' in a[1]:
  rows=json.loads(c.read_text());row=next(r for r in rows if r['id']==int(a[1].rsplit('/',1)[1]))
  if '--input' in a:
   row['body']=json.loads(Path(a[a.index('--input')+1]).read_text())['body'];w(rows)
  print(json.dumps(row))
 elif '/issues/12/comments' in a[1]:
  assert '--paginate' in a
  rows=json.loads(c.read_text())
  print(json.dumps(rows[:1]));print(json.dumps(rows[1:]))
 elif '/comments' in a[1]: print(os.environ.get('REVIEW_COMMENTS','[]'))
 elif '/compare/' in a[1]: print(json.dumps({'behind_by':int(os.environ.get('PR_BEHIND','0'))}))
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
 rows=json.loads(c.read_text());rows.append({'id':len(rows)+1,'body':Path(a[a.index('--body-file')+1]).read_text()});w(rows);print('https://github.com/o/r/issues/12#issuecomment-'+str(len(rows)))
elif a[:2]==['pr','view']:
 data=json.loads(Path(os.environ['PR']).read_text());rows=data if isinstance(data,list) else [data]
 print(json.dumps(next(p for p in rows if p['number']==int(a[2]))))
elif a[:2]==['pr','list']:
 p=Path(os.environ['PR']);rows=json.loads(p.read_text()) if p.exists() else []
 rows=rows if isinstance(rows,list) else [rows]
 if '--head' in a: rows=[row for row in rows if row['headRefName']==a[a.index('--head')+1]]
 if '--state' in a and a[a.index('--state')+1]!='all': rows=[row for row in rows if row['state']==a[a.index('--state')+1].upper()]
 print(json.dumps(rows))
else: raise SystemExit('unexpected gh: '+repr(a))
''')
        self.tool('codex', '''import json,os,subprocess,sys,time
from pathlib import Path
a=sys.argv[1:]
if a[:2]==['mcp','list']:
 sys.stdout.write(os.environ.get('FAKE_MCP_LIST','[]'));raise SystemExit(int(os.environ.get('FAKE_MCP_EXIT','0')))
out=Path(a[a.index('-o')+1]);
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

    def pr(self, number, branch, state='OPEN'):
        return dict(number=number, url=f'https://github.com/o/r/pull/{number}', state=state,
                    mergedAt=None, baseRefName='main', headRefName=branch, headRefOid=self.git('rev-parse', branch))

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

    def test_lost_reconciliation_records_claim_and_preserves_legacy_attestation(self):
        record = self.lost_record()
        result = self.call(*self.reconcile_options(record))
        self.assertTrue(result['reconciliation']['ownership_attestation'].startswith('Caller attests'))
        legacy = 'Authoritative inspection of the originating host/environment found no executor or supervisor owned by this exact run.'
        rows = json.loads(self.comments.read_text())
        rows[-1]['body'] = rows[-1]['body'].replace(
            result['reconciliation']['ownership_attestation'], legacy)
        self.comments.write_text(json.dumps(rows))
        unchanged = self.comments.read_text()
        retried = self.call(*self.reconcile_options(record))
        self.assertEqual(retried['reconciliation']['ownership_attestation'], legacy)
        self.assertEqual(self.comments.read_text(), unchanged)
        self.assertIn('conflict', self.call(*self.reconcile_options(record),
                                            '--reason', 'Different claim.', ok=False))
        continued = self.call(*self.continuation_options(), '--wait')
        self.assertEqual(continued['lane_id'], record['lane_id'])

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
   rows=json.loads(c.read_text());rows[-1]['body']=rows[-1]['body'].replace('"model": "gpt-6-astra"','"model": "changed"');w(rows)
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

    def test_eighth_round_worker_continuation_refuses_before_launch(self):
        run = self.start(); self.finish(run)
        head = self.git('rev-parse', run['branch'])
        (self.root/'pr.json').write_text(json.dumps(dict(number=13, url='https://github.com/o/r/pull/13',
            state='OPEN', baseRefName='main', headRefName=run['branch'], headRefOid=head)))
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
                  baseRefName='main', headRefName=first['branch'], headRefOid=head)
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

    def test_version_only_rebase_continuation_reuses_the_acceptance_without_a_ruling(self):
        """#421: main moved under an accepted head; the rebase costs no ruling and no round."""
        import runpy
        verdicts = runpy.run_path(str(SOURCE / '.github/test-review-packet.py'))
        first = self.start()
        self.finish(first)
        head = self.git('rev-parse', first['branch'])
        Path(self.env['PR']).write_text(json.dumps(self.pr(13, first['branch'])))
        accepted = [dict(id=1, user=dict(login='o'), body='## Merge check 1 — round 1\n'
                         + verdicts['canonical_verdict'](head))]
        self.env['REVIEW_COMMENTS'] = json.dumps(accepted)
        brief = self.root / 'continue.txt'
        brief.write_text('Rebase onto current main and carry the lockstep bump.')
        options = ('--purpose', 'worker', '--continue', '--pr', '13',
                   '--implementation', 'codex', '--brief', str(brief))
        # (b) The PR's base is still the default branch's head: today's refusal stands.
        before = self.comments.read_text()
        self.assertIn('Notes', self.call(*options, ok=False))
        self.assertEqual(self.comments.read_text(), before)
        # (c) A recorded ruling governs unchanged, base advance or not.
        self.env['PR_BEHIND'] = '1'
        rule = dict(kind='ruling', round=1, head=head, decision='continue', reason='assessed gap')
        self.env['REVIEW_COMMENTS'] = json.dumps(accepted + [dict(id=2, user=dict(login='o'),
            body='## Review ruling — after round 1\n\n<!-- devstandard-review-v1 -->\n```json\n'
                 + json.dumps(rule) + '\n```\n')])
        self.assertIn('Notes', self.call(*options, ok=False))
        self.assertEqual(self.comments.read_text(), before)
        # (a) No ruling, base advanced: admitted on the acceptance and recorded as the rebase.
        self.env['REVIEW_COMMENTS'] = json.dumps(accepted)
        continued = self.call(*options)
        self.finish(continued)
        self.assertEqual(continued['continuation'], 'rebase')
        for key in ('lane_id', 'branch', 'worktree'):
            self.assertEqual(continued[key], first[key])
        self.assertEqual(continued['pr'], 'https://github.com/o/r/pull/13')
        # No round and no ruling: the lane published the run record and nothing else.
        self.assertEqual([r['kind'] for r in self.lane_records()], ['lane', 'run', 'run'])

    def test_missing_fields_refused_before_any_lane_side_effect(self):
        """#427: only the reviewer reads these sections, so only the reviewer path still parses
        them — and it refuses before a packet is even opened."""
        for field in ['Goal', 'Bounds', 'Done-check']:
            with self.subTest(field=field):
                d=json.loads(self.issue.read_text()); original=d['body']
                d['body']=original.replace('## '+field, '## Other')
                self.issue.write_text(json.dumps(d))
                error=self.call('--purpose','reviewer','--packet',str(self.review_packet()),ok=False)
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
        self.assertIn('Produce evidence.',a[-1])
        self.assertIn('executor started',Path(run['log']).read_text())
        self.assertEqual(Path(run['completion']).read_text().strip(),'0')
        self.assertIn(run['branch'],self.comments.read_text())
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),2)

    def test_worker_packet_contains_the_verbatim_issue_and_human_comment_but_not_dispatch_records(self):
        """Dropping the preamble, a human comment, or retaining machine history breaks the handover."""
        issue = json.loads(self.issue.read_text())
        issue['body'] = ('Memo context that is outside the three contract headings.\n\n'
                         '## Goal\nProduce evidence.\n## Bounds\nOne task only.\n'
                         '## Done-check\nOutput is captured.')
        self.issue.write_text(json.dumps(issue))
        human_body = 'Human correction, kept byte for byte.\n\n```text\nDo the later thing.\n```'
        machine_body = ('<!-- devstandard-dispatch-v1 -->\n'
                        'Dispatcher lane observation.\n```json\n{"kind":"fixture"}\n```\n')
        self.comments.write_text(json.dumps([
            dict(id=41, user={'login':'human-owner'}, created_at='2026-09-13T12:34:56Z',
                 body=human_body),
            dict(id=42, user={'login':'human-owner'}, created_at='2026-09-13T12:35:00Z',
                 body=machine_body),
        ]))

        run = self.start('--implementation', 'codex-native')
        packet = Path(run['brief']).read_text()

        self.assertIn(issue['body'], packet)
        self.assertIn('Issue body (verbatim):', packet)
        self.assertIn('Issue comment by human-owner on 2026-09-13T12:34:56Z (verbatim):', packet)
        self.assertIn(human_body, packet)
        self.assertNotIn('<!-- devstandard-dispatch-v1 -->', packet)
        self.assertNotIn(machine_body, packet)

    def test_only_a_codex_brief_carries_the_codex_worker_harness_mechanics(self):
        """Each family is delivered its own harness page and never the other's (ADR 0061).

        Codex has no carrier that survives a lost packet — a native child gets SubagentStart and a
        CLI child runs with `DEVSTANDARD_ROLE` set, so neither receives `reference/harness-codex.md`
        at session start — so the brief carries its worker-facing section. Both Claude paths load
        `reference/harness-claude.md` from the agent definition body instead, which is why the
        brief adds nothing there. A worker handed the other harness's mechanics would recover its
        binding through a lookup its own host cannot perform.
        """
        contract = (SOURCE / 'reference/worker.md').read_text()
        codex_page = (SOURCE / 'reference/harness-codex.md').read_text()
        mechanics = codex_page.split('<!-- BEGIN CODEX WORKER MECHANICS -->\n', 1)[1] \
                              .split('<!-- END CODEX WORKER MECHANICS -->\n', 1)[0].strip('\n')
        claude_page = (SOURCE / 'reference/harness-claude.md').read_text()
        self.assertTrue(mechanics and mechanics not in claude_page and mechanics not in contract)
        self.assertTrue(claude_page not in contract)

        process = self.start('--implementation', 'codex')
        process_brief = Path(process['brief']).read_text()
        self.finish(process)
        # The same lane, continued once per executor: what differs between the three briefs is
        # the implementation and nothing else.
        carry_on = self.root / 'continue.txt'
        carry_on.write_text('Continue the same lane on another executor.')
        resume = ('--purpose', 'worker', '--continue', '--brief', str(carry_on))
        native = self.call(*resume, '--implementation', 'codex-native')
        native_message = json.loads(Path(native['instruction']).read_text())['message']
        claude = self.call(*resume, '--implementation', 'claude', '--native-finished')
        claude_prompt = json.loads(Path(claude['instruction']).read_text())['prompt']

        for name, text in (('codex', process_brief), ('codex-native', native_message)):
            with self.subTest(implementation=name):
                self.assertIn(contract, text)
                self.assertEqual(text.count(mechanics), 1)
                self.assertNotIn(claude_page, text)
                # Only the marked section travels: the rest of that page is host-facing and a
                # worker must not read an orchestrator's dispatch instructions as its own.
                self.assertNotIn(codex_page, text)
        self.assertNotIn(mechanics, claude_prompt)
        self.assertNotIn(claude_page, claude_prompt)
        self.assertNotIn(contract, claude_prompt)

    def test_continuation_refetches_comments_for_its_worker_packet(self):
        """Reusing the first launch's issue snapshot would hide a conclusion added mid-lane."""
        first = self.start()
        first_packet = Path(first['brief']).read_text()
        self.finish(first)
        later_body = 'Human conclusion added after the first launch, verbatim.'
        rows = json.loads(self.comments.read_text())
        rows.append(dict(id=99, user={'login':'human-owner'}, created_at='2026-09-13T12:40:00Z',
                         body=later_body))
        self.comments.write_text(json.dumps(rows))

        continued = self.call(*self.continuation_options())
        continued_packet = Path(continued['brief']).read_text()
        self.finish(continued)

        self.assertNotIn(later_body, first_packet)
        self.assertIn('Issue comment by human-owner on 2026-09-13T12:40:00Z (verbatim):',
                      continued_packet)
        self.assertIn(later_body, continued_packet)

    def test_reviewer_packet_carries_the_same_issue_record_without_changing_pinned_evidence(self):
        """Restricting the fresh issue to workers would leave the reviewer judging a stale task."""
        issue = json.loads(self.issue.read_text())
        issue['body'] = ('Memo and accepted design, kept byte for byte.\n\n'
                         '## Goal\nProduce evidence.\n## Bounds\nOne task only.\n'
                         '## Done-check\nOutput is captured.')
        self.issue.write_text(json.dumps(issue))
        human_body = 'Human task change for both dispatched purposes, verbatim.'
        self.comments.write_text(json.dumps([
            dict(id=51, user={'login':'human-owner'}, created_at='2026-09-14T08:15:00Z',
                 body=human_body),
        ]))

        worker = self.start()
        worker_prompt = Path(worker['brief']).read_text()
        self.finish(worker)
        packet = self.review_packet()
        packet_before = packet.read_bytes()
        review = self.call('--purpose', 'reviewer', '--implementation', 'claude',
                           '--packet', str(packet), '--native-finished')
        reviewer_prompt = Path(review['brief']).read_text()

        def issue_record(prompt):
            start = prompt.index('Issue body (verbatim):')
            return prompt[start:prompt.index('\nExecutor:', start)]

        self.assertEqual(issue_record(reviewer_prompt), issue_record(worker_prompt))
        self.assertIn(issue['body'], reviewer_prompt)
        self.assertIn(human_body, reviewer_prompt)
        self.assertEqual(packet.read_bytes(), packet_before)

        marker = '## Pinned Git evidence\n'
        evidence = json.JSONDecoder().raw_decode(reviewer_prompt.split(marker, 1)[1])[0]
        sha = self.git('rev-parse', 'origin/main')
        command = f"git -C {worker['worktree']} diff --no-ext-diff --no-textconv --no-color"
        self.assertEqual(evidence, [
            dict(command=f'{command} --name-status {sha} {sha}', exit_code=0,
                 stdout=[], stderr=[]),
            dict(command=f'{command} --stat {sha} {sha}', exit_code=0,
                 stdout=[], stderr=[]),
            dict(command=f'{command} {sha} {sha}', exit_code=0, stdout=[], stderr=[]),
        ])

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
        source=install/'reference/orchestrator.md'
        import re
        source.write_text(source.read_text().replace(
            '| worker | `gpt-6-astra` at `medium` | `opus` at `high` |',
            '| worker | `fixture-model` at `low` | `opus` at `high` |'))
        self.script=install/'scripts/dispatch'
        native=self.start('--implementation','codex-native')
        instruction=json.loads(Path(native['instruction']).read_text())
        self.assertEqual((native['model'],native['effort']),('fixture-model','low'))
        self.assertEqual((instruction['model'],instruction['reasoning_effort']),('fixture-model','low'))
        continuation=self.root/'continue.txt';continuation.write_text('Continue with the configured executor.')
        run=self.call('--purpose','worker','--continue','--implementation','codex',
                      '--brief',str(continuation),'--native-finished')
        data=self.finish(run);a=data['args']
        self.assertEqual((run['model'],run['effort']),(native['model'],native['effort']))
        self.assertEqual(a[a.index('-m')+1],'fixture-model')
        self.assertIn('model_reasoning_effort=low',a)
        self.assertIn('Co-Authored-By: Codex fixture-model low <noreply@openai.com>',a[-1])

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

    def test_an_unparsed_issue_body_and_comment_still_reach_the_worker_verbatim(self):
        """#427: nothing has read the dispatcher's issue-contract parse since #402, and its own
        refusals stopped this issue's first dispatch for naming the token they look for."""
        body = ('## Goal\nUse a {PLACEHOLDER} token and leave the rest TBD.\n'
                '## Goal\nA second one, because a human wrote two.\n'
                '## Done-check\n')
        self.issue.write_text(json.dumps(dict(json.loads(self.issue.read_text()), body=body)))
        self.comments.write_text(json.dumps([dict(id=61, body='A comment with neither login nor date.')]))
        run = self.start()
        packet = Path(run['brief']).read_text()
        self.finish(run)
        self.assertIn(body, packet)
        self.assertIn('Issue comment by unknown author on unknown date (verbatim):', packet)
        self.assertIn('A comment with neither login nor date.', packet)
        self.assertEqual(run['kind'], 'run')
        self.assertIn(run['branch'], self.git('branch', '--list', run['branch']))

    def test_nonzero_agent_exit_is_captured(self):
        self.env['FAKE_EXIT']='7'
        run=self.start();self.finish(run)
        self.assertEqual(Path(run['completion']).read_text().strip(),'7')

    def test_continuation_retains_lane_and_pr_and_rejects_live_writer(self):
        self.env['FAKE_HOLD']=str(self.root/'release')
        run=self.start()
        brief=self.root/'continue.txt';brief.write_text('Repair the missing evidence only.')
        (self.root/'pr.json').write_text(json.dumps(dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',baseRefName='main', headRefName=run['branch'],headRefOid=self.git('rev-parse',run['branch']))))
        self.assertIn('running', self.call('--purpose','worker','--continue','--brief',str(brief),'--pr','13',ok=False))
        self.finish(run)
        next_run=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief),'--pr','13')
        data=self.finish(next_run)
        self.assertEqual(next_run['branch'],run['branch']);self.assertEqual(next_run['worktree'],run['worktree'])
        self.assertIn('Repair the missing evidence only.',data['args'][-1])
        self.assertIn('https://github.com/o/r/pull/13',data['args'][-1])
        self.assertNotEqual(next_run['output'],run['output'])
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),2)
        resolved=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief))
        self.finish(resolved)
        self.assertEqual(resolved['pr'],'https://github.com/o/r/pull/13')

    def test_delivered_lane_continues_into_an_open_replacement_pr_on_its_branch(self):
        branch,wt=self.hand_made_lane()
        old=self.pr(13,branch)
        (self.root/'pr.json').write_text(json.dumps(old))
        lane=self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main','--pr','13')
        replacement=self.pr(14,branch)
        (self.root/'pr.json').write_text(json.dumps([dict(old,state='CLOSED'),replacement]))
        brief=self.root/'continue.txt';brief.write_text('Continue the rewritten delivery.')

        continued=self.call('--purpose','worker','--continue','--implementation','codex',
                            '--brief',str(brief),'--pr','14')
        self.finish(continued)
        self.assertEqual(continued['lane_id'],lane['lane_id'])
        self.assertEqual(continued['pr'],replacement['url'])

    def test_delivered_lane_refuses_a_replacement_pr_from_another_branch(self):
        branch,wt=self.hand_made_lane()
        old=self.pr(13,branch)
        (self.root/'pr.json').write_text(json.dumps(old))
        self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main','--pr','13')
        other=self.pr(14,'main')
        (self.root/'pr.json').write_text(json.dumps([dict(old,state='CLOSED'),other]))
        brief=self.root/'continue.txt';brief.write_text('Continue the rewritten delivery.')

        self.assertIn('PR branch differs from lane',self.call('--purpose','worker','--continue',
            '--brief',str(brief),'--pr','14',ok=False))

    def test_delivered_lane_without_pr_resolves_the_open_pr_on_its_branch(self):
        branch,wt=self.hand_made_lane()
        old=self.pr(13,branch)
        (self.root/'pr.json').write_text(json.dumps(old))
        lane=self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main','--pr','13')
        replacement=self.pr(14,branch)
        (self.root/'pr.json').write_text(json.dumps([dict(old,state='CLOSED'),replacement]))
        brief=self.root/'continue.txt';brief.write_text('Continue the rewritten delivery.')

        continued=self.call('--purpose','worker','--continue','--implementation','codex',
                            '--brief',str(brief))
        self.finish(continued)
        self.assertEqual(continued['lane_id'],lane['lane_id'])
        self.assertEqual(continued['pr'],replacement['url'])

    def test_delivered_lane_whose_pr_is_closed_or_ambiguous_continues_on_the_lane_branch(self):
        """#427: this family stranded #362's lane twice (#371/#372). A closed or ambiguous PR is
        reported in the run record; the continuation still reaches its lane branch."""
        branch,wt=self.hand_made_lane()
        old=self.pr(13,branch)
        (self.root/'pr.json').write_text(json.dumps(old))
        lane=self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main','--pr','13')
        brief=self.root/'continue.txt';brief.write_text('Continue the rewritten delivery.')

        # A delivered lane whose only PR has been closed.
        (self.root/'pr.json').write_text(json.dumps([dict(old,state='CLOSED')]))
        continued=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief))
        self.finish(continued)
        self.assertEqual(continued['lane_id'],lane['lane_id'])
        self.assertIsNone(continued['pr'])
        self.assertIn('#13 CLOSED',continued['pr_note'])
        self.assertNotIn('\nPR:',Path(continued['brief']).read_text())

        # The named PR is closed: the caller's explicit choice is reported, not refused.
        named=self.call('--purpose','worker','--continue','--implementation','codex',
                        '--brief',str(brief),'--pr','13')
        self.finish(named)
        self.assertEqual(named['pr'],old['url'])
        self.assertIn('#13 is CLOSED',named['pr_note'])

        # Two open PRs on the lane branch: pick none, say so, continue.
        (self.root/'pr.json').write_text(json.dumps([self.pr(14,branch),self.pr(15,branch)]))
        ambiguous=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief))
        self.finish(ambiguous)
        self.assertIsNone(ambiguous['pr'])
        self.assertIn('#14',ambiguous['pr_note']);self.assertIn('#15',ambiguous['pr_note'])
        self.assertEqual([r for r in self.lane_records() if r['kind']=='run'][-1]['pr_note'],
                         ambiguous['pr_note'])

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
        (self.root/'pr.json').write_text(json.dumps(dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',baseRefName='main', headRefName=run['branch'],headRefOid=self.git('rev-parse',run['branch']))))
        delivered=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief))
        self.finish(delivered)
        self.assertEqual(delivered['pr'],'https://github.com/o/r/pull/13')

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
        pr=dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',baseRefName='main', headRefName=branch,headRefOid=self.git('rev-parse',branch))
        (self.root/'pr.json').write_text(json.dumps(pr))
        lane=self.call('--adopt','--branch',branch,'--worktree',str(wt),'--base','origin/main','--pr','13')
        self.assertEqual(lane['pr'],pr['url'])
        brief=self.root/'continue.txt';brief.write_text('Repair the delivered lane.')
        resolved=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief));self.finish(resolved)
        self.assertEqual(resolved['pr'],pr['url'])
        continued=self.call('--purpose','worker','--continue','--implementation','codex','--brief',str(brief),'--pr','13');self.finish(continued)
        self.assertEqual(continued['pr'],pr['url']);self.assertEqual(continued['lane_id'],lane['lane_id'])

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
        (self.root/'pr.json').write_text(json.dumps(dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',baseRefName='main', headRefName='feat/other')))
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

    def test_codex_child_admits_host_mcp_tools_and_keeps_each_purposes_sandbox(self):
        """#358: `codex exec` is non-interactive, so its approval policy is `never`, which
        auto-rejects every MCP tool call. On codex-cli 0.153.4 only the per-server key admits
        one, and it composes with both sandbox modes, so neither mode moves to buy MCP back."""
        self.env['FAKE_MCP_LIST']=json.dumps([{'name':'papervault','enabled':True},
                                              {'name':'chrome-devtools','enabled':True},
                                              {'name':'retired','enabled':False},
                                              {'name':'odd.name','enabled':True}])
        admitted=['mcp_servers.chrome-devtools.default_tools_approval_mode="approve"',
                  'mcp_servers.papervault.default_tools_approval_mode="approve"']
        run=self.start();a=self.finish(run)['args']
        self.assertEqual([x for x in a if x.startswith('mcp_servers.')],admitted)
        self.assertEqual(run['mcp_servers'],['chrome-devtools','papervault'])
        self.assertEqual(a[a.index('-s')+1],'workspace-write')
        # A disabled server contributes no tools; a name a dotted -c cannot address is named
        # on the issue instead of leaving a tool that is visible and silently refused.
        self.assertNotIn('retired',' '.join(a));self.assertIn('odd.name',run['notice'])
        self.env['DEVSTANDARD_ROLE']='worker'
        review=self.call('--purpose','reviewer','--implementation','codex','--packet',str(self.review_packet()))
        b=self.finish(review)['args']
        self.assertEqual([x for x in b if x.startswith('mcp_servers.')],admitted)
        self.assertEqual(b[b.index('-s')+1],'read-only')
        for argv in (a,b):
            self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',argv)
            self.assertNotIn('--approve-for-me',argv)
            self.assertFalse([x for x in argv if x.startswith('approval_policy')])

    def test_unenumerable_mcp_servers_are_recorded_not_silently_dead(self):
        """A child whose MCP calls will be refused must not look like one whose servers are down."""
        self.env['FAKE_MCP_EXIT']='3'
        run=self.start();a=self.finish(run)['args']
        self.assertEqual([x for x in a if x.startswith('mcp_servers.')],[])
        self.assertEqual(run['mcp_servers'],[])
        self.assertIn('could not be enumerated',run['notice'])
        self.assertIn('harness limit',run['notice'])
        self.assertIn('could not be enumerated',self.comments.read_text())

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

    def test_both_purposes_take_their_anchored_codex_setting(self):
        """#406: worker and reviewer are anchored on one Codex setting, not routed by kind of work."""
        worker = self.start('--implementation', 'codex-native')
        self.assertEqual((worker['model'], worker['effort']), ('gpt-6-astra', 'medium'))
        packet = self.review_packet()
        review = self.call('--purpose', 'reviewer', '--implementation', 'codex',
                           '--packet', str(packet), '--native-finished')
        args = self.finish(review)['args']
        self.assertEqual((review['model'], review['effort']), ('gpt-6-astra', 'medium'))
        self.assertEqual(args[args.index('-m') + 1], 'gpt-6-astra')
        self.assertIn('model_reasoning_effort=medium', args)

    def test_explicit_model_and_effort_override_independently_on_each_executor(self):
        for implementation in ('codex', 'codex-native', 'claude', 'claude-cli'):
            codex = implementation.startswith('codex')
            default = ('gpt-6-astra', 'medium') if codex else ('opus', 'high')
            for flags, expected in [(('--model', 'override-model'), ('override-model', default[1])),
                                    (('--effort', 'low'), (default[0], 'low')),
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
        self.assertEqual((run['model'], run['effort']), ('gpt-6-astra', 'medium'))
        self.assertFalse({'pid', 'output', 'completion'} & run.keys())
        self.assertEqual(self.lane_records()[-1], run)
        instruction = json.loads(Path(run['instruction']).read_text())
        self.assertEqual(instruction['format'], 'devstandard-codex-native-v1')
        self.assertEqual((instruction['model'], instruction['reasoning_effort']), ('gpt-6-astra', 'medium'))
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

    def test_native_codex_continuation_resumes_its_handle_or_starts_fresh_in_the_same_lane(self):
        first = self.start('--implementation', 'codex-native')
        original = Path(first['brief']).read_bytes()
        self.assert_native_canonical_brief(first)
        brief = self.root/'continue.txt'
        brief.write_text('Finish the evidence for the existing lane.')
        options = ('--purpose', 'worker', '--implementation', 'codex-native',
                   '--continue', '--brief', str(brief))
        self.assertIn('running', self.call(*options, ok=False))
        # A refused required act is the orchestrator's to perform; it then resumes the same
        # finished native child, which answers with its context intact (#352).
        handle = '/root/devstandard_worker'
        # A resume stays a continuation of a native worker: it never opens a lane, and a CLI
        # executor keeps no context to resume.
        self.assertIn('--resume', self.call('--purpose', 'worker', '--implementation', 'codex-native',
                                            '--base', 'origin/main', '--resume', handle, ok=False))
        self.assertIn('--resume', self.call('--purpose', 'worker', '--implementation', 'codex',
                                            '--continue', '--brief', str(brief),
                                            '--native-finished', '--resume', handle, ok=False))
        resumed = self.call(*options, '--native-finished', '--resume', handle)
        receipt = json.loads(Path(resumed['instruction']).read_text())
        self.assertEqual(receipt['resume'], handle)
        self.assertFalse(receipt['fresh_conversation'])
        obligations = '\n'.join(receipt['native_tool_obligations'])
        self.assertIn('send_input', obligations)
        self.assertIn('followup_task', obligations)
        self.assertNotIn('fork_context=false', obligations)
        self.assertIn('follow-up', resumed['notice'])
        self.assertIn(brief.read_text(), receipt['message'])
        self.assert_native_canonical_brief(resumed)
        for key in ('lane_id', 'branch', 'worktree', 'base', 'base_sha'):
            self.assertEqual(resumed[key], first[key])
        self.assertEqual(self.lane_records()[-1], resumed)
        # Without a handle the same lane still continues through a fresh native child.
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
        self.assertNotIn('resume', instruction)
        self.assertIn('fork_context=false', '\n'.join(instruction['native_tool_obligations']))
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
        # Until #411 this asserted the role page's opening line here, when `--agent
        # devstandard:worker` above was already delivering the whole page as this process's
        # system prompt: the worker received it twice. The role now rides the definition on both
        # Claude paths, so what stdin must carry is the task packet and nothing else.
        self.assertNotIn((SOURCE/'reference/worker.md').read_text(), data['stdin'])
        self.assertNotIn('This brief is what makes you a worker', data['stdin'])
        self.assertTrue(data['stdin'].lstrip('\n').startswith('# Task packet'), data['stdin'][:80])
        self.assertIn('Co-Authored-By: Claude opus high <noreply@anthropic.com>', data['stdin'])
        self.assertEqual(result['permission_denials'], denials)
        self.assertEqual(events[-1]['permission_denials'], [])
        self.assertEqual(events[-1]['result'], 'Background agent finished.')
        self.assertIn('Claude executor started', Path(run['log']).read_text())
        self.assertEqual(Path(run['completion']).read_text().strip(), '0')
        self.assertNotIn('instruction', run)

    def install_claude_anchor(self, page_cell, frontmatter_effort):
        """An installed plugin whose Claude worker anchor is the given page cell and frontmatter."""
        install = self.root/'plugin with spaces'
        for directory in ('scripts', 'reference', 'hooks', 'agents', '.claude-plugin'):
            shutil.copytree(SOURCE/directory, install/directory)
        worker = install/'agents/worker.md'
        worker.write_text(worker.read_text().replace('effort: high', 'effort: ' + frontmatter_effort, 1))
        page = install/'reference/orchestrator.md'
        page.write_text(page.read_text().replace(
            '| worker | `gpt-6-astra` at `medium` | `opus` at `high` |',
            '| worker | `gpt-6-astra` at `medium` | ' + page_cell + ' |'))
        self.script = install/'scripts/dispatch'
        return install

    def test_claude_cli_uses_the_installed_anchored_row(self):
        install = self.install_claude_anchor('`sonnet` at `medium`', 'medium')
        run = self.start('--implementation', 'claude-cli')
        args = json.loads(self.finish_claude(run)[1]['result'])['args']
        self.assertEqual(args[args.index('--plugin-dir')+1], str(install))
        self.assertEqual((run['model'], run['effort']), ('sonnet', 'medium'))
        self.assertEqual(args[args.index('--model')+1], 'sonnet')
        self.assertEqual(args[args.index('--effort')+1], 'medium')

    def test_claude_anchor_disagreeing_with_its_definition_refuses_before_lane_creation(self):
        """#406: the Agent tool takes no effort, so a page promising one the definition does not
        pin would misreport what runs. Refuse instead."""
        self.install_claude_anchor('`opus` at `xhigh`', 'high')
        error = self.call('--purpose', 'worker', '--base', 'origin/main',
                          '--implementation', 'claude', ok=False)
        self.assertIn('pins effort high', error)
        self.assertIn('xhigh', error)
        self.assertEqual(self.lane_records(), [])

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
        pr=dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',mergedAt=None,baseRefName='main', headRefName=run['branch'],headRefOid=self.git('rev-parse',run['branch']))
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
        """#427: a squash merge always leaves the lane head off main, so the old -D authorization
        was always required and stopped nothing. The checks that can actually lose work run first."""
        self.env['FAKE_COMMITS']='1'
        run=self.start();self.finish(run)
        self.assertEqual(self.git('rev-list','--count','origin/main..'+run['branch']),'2')
        head=self.git('rev-parse',run['branch'])
        self.git('merge','--squash',run['branch']);self.git('commit','-m','squash worker PR')
        self.git('update-ref','refs/remotes/origin/main','HEAD')
        self.assertNotEqual(head,self.git('rev-parse','origin/main'))
        self.assertEqual(self.git('diff','origin/main',run['branch']),'')
        # The lane head is not an ancestor of the integrated base: plain `git branch -d` refuses.
        self.assertNotEqual(subprocess.run(['git','-C',str(self.project),'merge-base','--is-ancestor',
                                            head,'origin/main'],capture_output=True).returncode,0)
        pr=dict(number=13,url='https://github.com/o/r/pull/13',state='MERGED',mergedAt='2026-01-01T00:00:00Z',baseRefName='main', headRefName=run['branch'],headRefOid=head)
        (self.root/'pr.json').write_text(json.dumps(pr))
        # The kept protections still fire, and each of them preserves the lane.
        stray=Path(run['worktree'])/'stray';stray.write_text('keep')
        self.assertIn('dirty',self.call('--cleanup','--pr','13',ok=False))
        stray.unlink()
        self.git('-C',run['worktree'],'commit','--allow-empty','-m','unpublished work')
        self.assertIn('unpublished work',self.call('--cleanup','--pr','13',ok=False))
        self.assertTrue(Path(run['worktree']).exists())
        self.git('-C',run['worktree'],'reset','--hard',head)
        # With them passed, cleanup needs no flag and still prints the inventory it printed before.
        result=subprocess.run([sys.executable,str(self.script),'12','--cleanup','--pr','13',
                               '--project',str(self.project)],env=self.env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('worker step 0',result.stderr);self.assertIn('worker step 1',result.stderr)
        cleanup=json.loads(result.stdout)
        self.assertEqual(cleanup['status'],'cleaned')
        self.assertFalse(Path(run['worktree']).exists())
        self.assertEqual(self.git('branch','--list',run['branch']),'')
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '),1)
        self.assertEqual(self.lane_records()[-1],cleanup)


if __name__ == '__main__':
    unittest.main()
