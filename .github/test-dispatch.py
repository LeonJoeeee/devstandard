#!/usr/bin/env python3
"""Exercise the shipped command with real git and process detachment; fake GitHub/Codex I/O."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class DispatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dispatch-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
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
 if '/comments' in a[1]: print(os.environ.get('REVIEW_COMMENTS','[]'))
 else: print(json.dumps(json.loads(os.environ.get('DEFAULT_CI', '{"default_branch":"main","commit":{"sha":"abc"},"tree":[],"check_runs":[{"name":"test","status":"completed","conclusion":"success"}],"statuses":[]}'))))
elif a[:2]==['issue','view']:
 d=json.loads(Path(os.environ['ISSUE']).read_text());d['comments']=json.loads(c.read_text());print(json.dumps(d))
elif a[:2]==['issue','comment']:
 rows=json.loads(c.read_text());rows.append({'body':Path(a[a.index('--body-file')+1]).read_text()});c.write_text(json.dumps(rows));print('https://github.com/o/r/issues/12#issuecomment-'+str(len(rows)))
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
out.write_text(json.dumps({'args':a,'sid':os.getsid(0),'pid':os.getpid(),'stdin':sys.stdin.read()}))
hold=os.environ.get('FAKE_HOLD');deadline=time.monotonic()+20
while hold and not Path(hold).exists() and time.monotonic()<deadline: time.sleep(.01)
raise SystemExit(int(os.environ.get('FAKE_EXIT','0')))
''')
        self.script = SOURCE / 'scripts/dispatch'

    def tool(self, name, body):
        p = self.bin / name
        p.write_text('#!/usr/bin/env python3\n'+body)
        p.chmod(0o755)

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
        return self.call('--purpose', 'worker', '--base', 'origin/main', *args)

    def lane_records(self):
        return [json.loads(row['body'].split('```json\n')[1].split('\n```')[0])
                for row in json.loads(self.comments.read_text())]

    def hand_made_lane(self):
        branch='feat/hand-made'; wt=self.root/'hand-made'
        self.git('worktree','add','-b',branch,str(wt),'origin/main')
        return branch,wt

    def finish(self, run):
        if self.env.get('FAKE_HOLD'):
            Path(self.env['FAKE_HOLD']).touch()
        marker = Path(run['completion'])
        deadline = time.monotonic()+8
        while not marker.exists() and time.monotonic()<deadline:
            time.sleep(.02)
        self.assertTrue(marker.exists(), Path(run['log']).read_text())
        return json.loads(Path(run['output']).read_text())

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
            CI_FALLBACK_COMMENT_OR_NONE='NONE',IN_REPO_WRITES_PREDICATE=predicate,
            REVIEWER_IDENTITY=identity)
        packet=self.root/'review.txt'
        packet.write_text(json.dumps(dict(format='devstandard-review-packet-v1',template=template,slots=slots)))
        return packet

    def test_red_default_branch_refuses_before_lane_creation(self):
        self.env['DEFAULT_CI'] = json.dumps({'default_branch': 'main', 'commit': {'sha': 'abc'},
            'check_runs': [{'name': 'test', 'status': 'completed', 'conclusion': 'failure'}], 'statuses': []})
        self.assertIn('default-branch CI', self.call('--purpose', 'worker', '--base', 'origin/main', ok=False))
        self.assertFalse((self.project/'.claude').exists())
        self.assertEqual(json.loads(self.comments.read_text()), [])

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
        self.env['FAKE_HOLD']=str(self.root/'release')
        run=self.start()
        os.kill(run['pid'],0)
        self.assertNotEqual(os.getsid(run['pid']),os.getsid(0))
        data=self.finish(run); a=data['args']
        config = next((x for x in a if x.startswith('hooks.PreToolUse=')), '')
        self.assertIn('--role worker', config)
        self.assertIn('features.hooks=true', a)
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

    def test_setting_is_read_from_the_installed_role_source(self):
        install=self.root/'plugin'
        shutil.copytree(SOURCE/'scripts',install/'scripts')
        shutil.copytree(SOURCE/'reference',install/'reference')
        source=install/'reference/external-agent.md'
        import re
        source.write_text(re.sub(r'The standing setting on these projects is `[^`]+`',
            'The standing setting on these projects is `-m fixture-model -c model_reasoning_effort=medium`',source.read_text()))
        self.script=install/'scripts/dispatch'
        run=self.start();data=self.finish(run);a=data['args']
        self.assertEqual(a[a.index('-m')+1],'fixture-model')
        self.assertIn('model_reasoning_effort=medium',a)
        self.assertIn('Co-Authored-By: Codex fixture-model medium <noreply@openai.com>',a[-1])

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
        next_run=self.call('--purpose','worker','--continue','--brief',str(brief),'--pr','13')
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
        continued=self.call('--purpose','worker','--continue','--brief',str(brief))
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
        review=self.call('--purpose','reviewer','--packet',str(packet))
        a=self.finish(review)['args']
        self.assertEqual(a[a.index('-s')+1],'read-only')
        brief=self.root/'continue.txt';brief.write_text('Continue the adopted work.')
        continued=self.call('--purpose','worker','--continue','--brief',str(brief));self.finish(continued)
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
        continued=self.call('--purpose','worker','--continue','--brief',str(brief),'--pr','13');self.finish(continued)
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
        packet=self.review_packet()
        review=self.call('--purpose','reviewer','--packet',str(packet))
        data=self.finish(review);a=data['args']
        self.assertEqual(a[a.index('-s')+1],'read-only');self.assertNotIn('--add-dir',a);self.assertNotIn('sandbox_workspace_write.network_access=true',a)
        self.assertIn('Complete report.',a[-1]);self.assertEqual(review['worktree'],run['worktree'])

    def test_claude_returns_agent_instruction_without_claiming_launch(self):
        run=self.start('--implementation','claude')
        self.assertEqual(run['status'],'awaiting-agent-tool')
        spawn=json.loads(Path(run['instruction']).read_text())
        self.assertEqual(spawn['subagent_type'],'devstandard:worker')
        self.assertIn('Produce evidence.',spawn['prompt'])
        self.assertNotIn('pid',run)
        packet=self.review_packet(identity='Codex, stale-model at low, read-only')
        review=self.call('--purpose','reviewer','--implementation','claude','--packet',str(packet),'--native-finished')
        self.assertEqual(json.loads(Path(review['instruction']).read_text())['subagent_type'],'devstandard:reviewer')

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
                        identity='Claude subagent, opus, read-only'
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
        packet=self.review_packet(base,head,convention,identity='Claude subagent, opus, read-only')
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
            CI_FALLBACK_COMMENT_OR_NONE='NONE',IN_REPO_WRITES_PREDICATE=predicate,
            REVIEWER_IDENTITY='{REVIEWER_IDENTITY}')
        packet=self.root/'structured.json'
        packet.write_text(json.dumps(dict(format='devstandard-review-packet-v1',template=template,slots=slots)))
        review=self.call('--purpose','reviewer','--implementation','claude','--packet',str(packet))
        prompt=Path(review['brief']).read_text()
        self.assertIn(quoted,prompt)
        self.assertIn('Reviewer: Claude subagent, opus, read-only — reviewed',prompt)
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
        packet=self.review_packet(identity='Claude subagent, opus, read-only')
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
        good=self.review_packet(identity='Claude subagent, opus, read-only').read_text()
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
        first=self.start('--implementation','claude')
        packet=self.review_packet(identity='Claude subagent, opus, read-only')
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
