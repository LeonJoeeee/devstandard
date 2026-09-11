#!/usr/bin/env python3
"""Mechanical guard primitives. Python 3.9+, git 2.38+, authenticated gh."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote
from review_packet import (FLOOR_LABELS, MANIFESTS, decision_line, floor_results, manifest_bump,
                           normalize, recovery_ruling, verdict_shape, version_only)


class Refusal(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refusal(message)


def refusing(read, *args):
    """review_packet's pinned readers raise ValueError; at a guard boundary that is a Refusal."""
    try:
        return read(*args)
    except ValueError as error:
        raise Refusal(str(error)) from error


def ascending(pair):
    """True when a dotted numeric release sorts strictly above the one it replaces."""
    fields = [version.split('.') for version in pair]
    require(all(re.fullmatch('[0-9]+', field) for parts in fields for field in parts),
            'exempt version lines require dotted numeric releases: ' + repr(pair))
    return [int(field) for field in fields[0]] < [int(field) for field in fields[1]]


def run(*args, cwd=None, env=None, input=None):
    result = subprocess.run(args, cwd=cwd, env=env, input=input, text=True, capture_output=True)
    require(result.returncode == 0, result.stderr.strip() or result.stdout.strip() or f'{args[0]} failed')
    return result.stdout.rstrip('\n')


def api(endpoint, *args):
    raw = run('gh', 'api', endpoint, *args)
    if '--paginate' not in args:
        return json.loads(raw)
    decoder, pages = json.JSONDecoder(), []
    while raw.strip():
        page, end = decoder.raw_decode(raw.lstrip())
        pages.extend(page if isinstance(page, list) else [page])
        raw = raw.lstrip()[end:]
    return pages


# The name the shipped CI template reports for a PR's merge result, pinned to both SHAs.
MERGED_RESULT = 'merged-result / {base} / {head}'


def merged_result(base, head):
    """The integration check's name, pinned to this exact base and head."""
    return MERGED_RESULT.replace('{base}', base).replace('{head}', head)


def project_repo(project):
    """OWNER/REPO from this checkout's own origin remote; local, so no network."""
    url = run('git', '-C', str(project), 'remote', 'get-url', 'origin')
    match = re.search(r'[:/]([^/:]+/[^/]+?)(?:\.git)?/?$', url)
    require(match, f'cannot read OWNER/REPO from the origin remote: {url!r}')
    return match[1]


def protection_check(repo, branch, checks=()):
    """Protection's shape, plus any contexts the caller named on the command line (#326)."""
    checks = list(checks)
    state = api(f'repos/{repo}/branches/{quote(branch, safe="")}/protection')
    status = state.get('required_status_checks') or {}
    require(status.get('strict') is True, 'protection requires strict up-to-date checks')
    require(set(checks) <= set(status.get('contexts', [])), 'protection missing required checks')
    require((state.get('enforce_admins') or {}).get('enabled') is True, 'protection must enforce admins')
    for field in ('allow_force_pushes', 'allow_deletions'):
        require((state.get(field) or {}).get('enabled') is False, f'protection must disable {field}')
    # Classic protection carries no queue field; rulesets are where the API exposes one.
    rules = api(f'repos/{repo}/rules/branches/{quote(branch, safe="")}', '--paginate')
    require(isinstance(rules, list) and all(isinstance(rule, dict) for rule in rules),
            'branch rules unreadable, so a merge queue cannot be ruled out')
    require(not any(rule.get('type') == 'merge_queue' for rule in rules),
            'protection must not enable a merge queue: it merges a server-built commit '
            'that no reviewer saw and no guarded merge produced')
    return {'repo': repo, 'branch': branch, 'checks': checks, 'protection': 'pass',
            'merge_queue': 'off'}


def compare_rebase(project, old_base, old_head, new_base, new_head):
    """Replay in a disposable clone; never move the caller's refs/index/worktree."""
    project = Path(project).resolve()
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    clean_env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                     GIT_TERMINAL_PROMPT='0', GIT_EDITOR='true', GIT_AUTHOR_NAME='Rebase proof',
                     GIT_AUTHOR_EMAIL='proof@example.invalid', GIT_COMMITTER_NAME='Rebase proof',
                     GIT_COMMITTER_EMAIL='proof@example.invalid')

    def git(at, *args):
        return run('git', '-C', str(at), '-c', 'core.hooksPath=/dev/null', *args, env=clean_env)

    pins = [old_base, old_head, new_base, new_head]
    require(all(re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', pin) for pin in pins), 'comparison requires full immutable SHAs')
    for pin in pins:
        require(git(project, 'rev-parse', '--verify', pin + '^{commit}') == pin, 'pin is not a commit')
    git(project, 'merge-base', '--is-ancestor', old_base, old_head)
    git(project, 'merge-base', '--is-ancestor', old_base, new_base)
    git(project, 'merge-base', '--is-ancestor', new_base, new_head)
    require(not git(project, 'rev-list', '--merges', f'{old_base}..{old_head}'), 'merge commits require full review')
    require(not git(project, 'rev-list', '--merges', f'{new_base}..{new_head}'), 'merge commits require full review')

    def changed(base, head):
        # -z retains whitespace/newlines in names; no rename inference hides a deleted path.
        raw = git(project, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-only', '-z', base, head)
        return set(raw.rstrip('\0').split('\0')) if raw else set()

    def exempt_conflict(clone):
        """Conflicted paths when the replay stopped only on the exempt manifest version lines."""
        raw = git(clone, 'ls-files', '--unmerged', '-z')
        stopped = {row.split('\t', 1)[-1] for row in raw.rstrip('\0').split('\0')} if raw else set()
        if not stopped or not stopped <= set(MANIFESTS):
            return set()
        try:  # git's :1/:2/:3 are the conflict's base, the new base's side and the reviewed lane's.
            sides = [manifest_bump(clone, ':1', side, path, clean_env)
                     for path in sorted(stopped) for side in (':2', ':3')]
        except ValueError:
            return set()
        return stopped if all(sides) else set()

    paths = changed(old_base, old_head) | changed(new_base, new_head)
    require(paths, 'empty PR requires full review')
    bumps = {}
    for path in sorted(paths):
        # Entry identity includes mode, object type and blob bytes, including deletion and symlinks.
        old = git(project, 'ls-tree', '-z', old_head, '--', ':(literal)' + path)
        new = git(project, 'ls-tree', '-z', new_head, '--', ':(literal)' + path)
        # The bump rides the change PR, so rebasing past a merged bump moves only these version lines.
        if old != new and path in MANIFESTS and old.split()[:2] == new.split()[:2]:
            bumps[path] = refusing(manifest_bump, project, old_head, new_head, path, clean_env)
        require(old == new or bumps.get(path), f'PR-changed path is not byte/mode-identical: {path!r}')
        require(not old.startswith('160000 '), 'submodules require full review')
    require(not bumps or (set(bumps) == set(MANIFESTS)
                          and all(bump == bumps[MANIFESTS[0]] for bump in bumps.values())),
            'exempt manifest version lines must move in lockstep: ' + repr(bumps))
    with tempfile.TemporaryDirectory(prefix='devstandard-rebase-proof-') as scratch:
        clone = Path(scratch) / 'replay'
        run('git', 'clone', '--shared', '--no-checkout', '--quiet', str(project), str(clone), env=clean_env)
        git(clone, 'checkout', '--detach', old_head)
        step = ['rebase', '--no-autostash', '--no-gpg-sign', '--reapply-cherry-picks',
                '--empty=keep', '--onto', new_base, old_base]
        while True:
            try:
                git(clone, '-c', 'rerere.enabled=false', *step)
                break
            except Refusal as error:
                # The comparison exempts these version lines, so the replay feeding it does too. Taking
                # the new base's side leaves the ordering checks below a version they must beat.
                stopped = exempt_conflict(clone)
                if not stopped:
                    raise Refusal(f'conflict-free rebase proof refused: {error}') from error
                for path in sorted(stopped):
                    git(clone, 'checkout', '--ours', '--', ':(literal)' + path)
                    git(clone, 'add', '--', ':(literal)' + path)
                step = ['rebase', '--continue']
        replay = git(clone, 'rev-parse', 'HEAD')
        if git(clone, 'rev-parse', replay + '^{tree}') != git(project, 'rev-parse', new_head + '^{tree}'):
            require(refusing(version_only, clone, replay, new_head, clean_env),
                    'new head differs from conflict-free replay tree')
            # The exemption admits a bump the head declares, never a silent revert of the base's.
            replayed = refusing(manifest_bump, clone, replay, new_head, MANIFESTS[0], clean_env)
            require(bumps and replayed and bumps[MANIFESTS[0]][1] == replayed[1],
                    'exempt version lines must carry the reviewed head bump: ' + repr(bumps))
            require(ascending(bumps[MANIFESTS[0]]) and ascending(replayed),
                    'exempt version lines must sort above the versions they replace: '
                    + repr([bumps[MANIFESTS[0]], replayed]))
    return {'old_base': old_base, 'accepted_head': old_head, 'base': new_base, 'head': new_head,
            'paths': sorted(paths), 'version_bump': bumps.get(MANIFESTS[0]), 'comparison': 'pass'}


def commit_checks(repo, sha, required=()):
    """Every observed check must be green; `required` additionally names checks that must exist.

    Each refusal names the observed checks and the required set actually applied, and only a
    check that is not green is reported as not green (#314).
    """
    pages = api(f'repos/{repo}/commits/{sha}/check-runs?per_page=100', '--paginate')
    if isinstance(pages, dict):  # Also accepts a single page from API boundary doubles.
        pages = [pages]
    runs = [row for page in pages for row in page.get('check_runs', [])]
    pages = api(f'repos/{repo}/commits/{sha}/status?per_page=100', '--paginate')
    if isinstance(pages, dict):
        pages = [pages]
    statuses = [row for page in pages for row in page.get('statuses', [])]
    # The API returns newest first; an older successful run must not hide a current red run.
    latest = {}
    for row in sorted(runs, key=lambda row: row.get('id', 0), reverse=True):
        latest.setdefault(row['name'], row.get('conclusion') if row.get('status') == 'completed' else 'pending')
    for row in sorted(statuses, key=lambda row: row.get('id', 0), reverse=True):
        latest.setdefault(row['context'], row.get('state'))
    # An empty required set never admits an unchecked head: silence is not green.
    require(latest, f'no CI checks reported for {sha}: required={list(required)!r}')
    require(all(value in ('success', 'neutral', 'skipped') for value in latest.values()),
            f'CI not green for {sha}: required={list(required)!r}, observed={latest!r}')
    # Absent or reported anything but success: green observed checks cannot stand in for these.
    unmet = [name for name in required if latest.get(name) != 'success']
    require(not unmet, f'required CI checks unmet for {sha}: unmet={unmet!r}, '
                       f'required={list(required)!r}, observed={latest!r}')
    return latest


def default_ci(repo):
    """Refuse a new lane on a red default branch: every observed check green, at least one (#314)."""
    default = api(f'repos/{repo}')['default_branch']
    head = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    try:
        checks = commit_checks(repo, head)
    except Refusal as error:
        raise Refusal(f'default-branch CI refused dispatch: {error}') from error
    return {'branch': default, 'head': head, 'checks': checks}


def acceptance(comments, head, allow_goal_no=False):
    """Read the canonical whole verdict, never a readiness substring in arbitrary prose."""
    verdicts = [row for row in comments if re.match(r'^## Merge check 1 — round [1-9][0-9]*\s*\n', row['body'])]
    require(verdicts, 'no whole Merge check 1 verdict')
    row = verdicts[-1]
    # Remove only the public heading and optional record envelope; validate the same whole return
    # as publication, never a readiness substring in the record or arbitrary surrounding prose.
    body = row['body'].split('\n', 1)[1].lstrip('\n')
    envelope = re.match(r'<!-- devstandard-review-v1 -->\n```json\n.*?\n```\n', body, re.S)
    if envelope:
        body = body[envelope.end():].lstrip('\n')
    defect = verdict_shape(body, head)
    require(defect is None, defect)
    body = normalize(body)
    goal = re.search(decision_line('Goal verdict', grounds=True), body, re.M)
    require(goal and (allow_goal_no or goal[1] == 'Yes'),
            'Goal Yes verdict required (or recorded orchestrator ruling)')
    for label in FLOOR_LABELS:
        require(floor_results(body, label) == ['Pass'],
                'both Floor checks must Pass')
    return row


def review_history(comments):
    """Consume #203's public record format; the review-packet command owns publication."""
    attempts, rulings, active = [], [], []
    for row in comments:
        body = row['body']
        match = re.match(r'^## (?:Review attempt|Merge check 1|Review ruling) — [^\n]+\n\n'
                         r'<!-- devstandard-review-v1 -->\n```json\n(.*?)\n```\n', body, re.S)
        if match:
            record = json.loads(match[1])
            record['row'] = row
            if record['kind'] == 'ruling':
                rulings.append(record)
            elif record.get('status') == 'returned':
                record['row'] = dict(row, body=f"## Merge check 1 — round {record['round']}\n" + body[match.end():].lstrip('\n'))
                attempts.append(record)
            elif record.get('status') in ('reserved', 'dispatched'):
                active.append(record)
        elif body.startswith('## Merge check 1'):
            match = re.match(r'^## Merge check 1 — round ([1-9][0-9]*)\n', body)
            require(match, 'ambiguous legacy review round; reconcile history')
            head = re.search(r'^Reviewer: [^\n]+ — reviewed\s+([0-9a-f]{40,64})', body, re.M)
            attempts.append({'round': int(match[1]), 'head': head[1] if head else None, 'row': row})
    attempts.sort(key=lambda row: row['round'])
    require([row['round'] for row in attempts] == list(range(1, len(attempts)+1)),
            'missing or duplicate review rounds; reconcile history')
    require(len(attempts) <= 7, '7 review rounds exceeded; orchestrator ruling required')
    require(not active, 'review attempt active; wait for whole verdict')
    last = attempts[-1] if attempts else None
    rulings = [r for r in rulings if last and r['round'] == last['round'] and r['head'] == last['head']]
    return attempts, last, rulings[-1] if rulings else None


def round_check(comments, head):
    attempts, last, ruling = review_history(comments)
    require(len(attempts) < 7, '7 review rounds consumed; orchestrator ruling required (no eighth review)')
    if last:
        # Read the decision the verdict parsers read; raw text let emphasis hide a Fail (#260).
        require('Fail' not in floor_results(last['row']['body'], '2. Authorization and scope'),
                'Floor check 2 failed; stop lane and escalate to human')
        try:
            acceptance([last['row']], head)
        except Refusal:
            pass
        else:
            require(recovery_ruling(ruling, head), 'accepted verdict: Notes do not authorize another round')
        require(ruling and ruling['decision'] == 'continue', 'explicit orchestrator continuation ruling required')
    return {'rounds': len(attempts), 'next_round': len(attempts)+1, 'head': head}


# Every record this method publishes on a PR carries one of these; the tooling posts them under
# the repository owner's account, so a sign-off is an owner comment that is none of them.
PUBLISHED_RECORD = re.compile(r'<!-- devstandard-[a-z-]+-v[0-9]+ -->'
                              r'|^## (?:Merge check 1|Review attempt|Review ruling)\b', re.M)


def owner_signoff(comments, owner):
    """The human's architecture-level sign-off: one comment of their own on the PR (#326).

    There is no record format to write, no issue to find it on and no allowlist to configure.
    This is a publishing-identity check, not proof that a shared account's operator is human —
    the same limitation the retired JSON record carried, now with nothing to maintain.
    """
    return next((row for row in comments
                 if row.get('user', {}).get('login') == owner
                 and (row.get('body') or '').strip()
                 and not PUBLISHED_RECORD.search(row['body'])), None)


def merge_acceptance(comments, head):
    attempts, last, ruling = review_history(comments)
    require(last, 'no whole Merge check 1 verdict')
    require(len(attempts) < 7 or ruling, 'round 7 requires orchestrator ruling before merge')
    if ruling:
        require(ruling['decision'] == 'merge-as-is', 'latest orchestrator ruling does not authorize merge')
    result = acceptance([last['row']], head, allow_goal_no=bool(ruling))
    return dict(result, record=last)


def merge_check(project, repo, number, old_base=None, old_head=None, execute=False):
    """Require review and integration evidence, then optionally merge the verified head."""
    require(project_repo(project) == repo,
            'merge repository differs from this checkout\'s origin')
    pr = api(f'repos/{repo}/pulls/{number}')
    repository = api(f'repos/{repo}')
    default = repository['default_branch']
    # The account that owns the repository: who publishes the operative review records, and
    # whose comment on the PR is an architecture-level sign-off. Read here, declared nowhere.
    owner = repository['owner']['login']
    base = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    head = pr['head']['sha']
    require(pr['state'] == 'open', 'merge requires an open PR')
    require(pr['base']['repo']['full_name'] == repo and pr['base']['ref'] == default,
            'merge requires the default branch of this repository')
    require(pr['base']['sha'] == base, 'PR base is not current default-branch head')
    run('git', '-C', str(project), 'merge-base', '--is-ancestor', base, head)
    protection_check(repo, default)
    comments = api(f'repos/{repo}/issues/{number}/comments?per_page=100', '--paginate')
    comments = [row for row in comments if row.get('user', {}).get('login') == owner]
    bare_bump = refusing(version_only, project, base, head)
    verdict = None if bare_bump else merge_acceptance(comments, old_head or head)
    proof = None
    if old_head and not bare_bump:
        require(old_base, 'prior acceptance requires its review base')
        require(verdict['record'].get('base') == old_base,
                'prior acceptance must record the exact old review base (#203 record)')
        proof = compare_rebase(project, old_base, old_head, base, head)
    flag = re.search(r'^architecture-level:\s*(true|false)\s*$', pr.get('body') or '', re.I | re.M)
    recorded_flag = verdict['record'].get('architecture') if verdict else None
    require(bare_bump or flag or recorded_flag in ('YES', 'NO'), 'explicit architecture-level flag required')
    architecture = (flag and flag[1].lower() == 'true') or recorded_flag == 'YES'
    if architecture:
        require(owner_signoff(comments, owner),
                f'architecture-level merge requires a sign-off comment on this PR by {owner!r}, '
                'the account that owns the repository')
    ci = commit_checks(repo, head, [merged_result(base, head)])
    latest = api(f'repos/{repo}/pulls/{number}')
    latest_base = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    require(latest == pr and latest_base == base, 'PR or base changed during merge verification')
    result = {'repo': repo, 'pr': number, 'base': base, 'head': head,
              'verdict': verdict['id'] if verdict else None, 'comparison': proof, 'checks': ci, 'merge': 'pass'}
    if execute:
        message = run('git', '-C', str(project), 'log', '-1', '--format=%B', head)
        trailers = re.findall(r'^(?:Claude-Session|Codex-Session|Co-authored-by):[^\r\n]+',
                              message, re.I | re.M)
        # GitHub rechecks strict protection; the SHA precondition rejects a moved PR head.
        result['result'] = api(f'repos/{repo}/pulls/{number}/merge', '--method', 'PUT',
                              '-f', 'sha=' + head, '-f', 'merge_method=squash',
                              '-f', f'commit_title={pr["title"]} (#{number})',
                              '-f', 'commit_message=' + '\n'.join(trailers))
        require(result['result'].get('merged'), 'GitHub refused the verified merge')
    return result


# ---------------------------------------------------------------------------
# The role hook's one rule (#323, ADR 0051).
#
# The hook reads the command's raw text — quotes, here-doc bodies and substitution
# bodies included — and refuses when that text carries one of its role's words.
# There is no parsing and no grammar, so unparseable syntax is never a reason to
# refuse for any role. Nothing here reads a file, a ref or the network, and there is
# nothing to configure: the words below are the whole policy (#326, ADR 0052).
# It judges commands and nothing else: a tool name is never a reason to refuse, so
# every non-shell tool call is admitted for every role (#334).
# Obfuscation, interpreter scripts, forged local refs and runtime data are outside
# this boundary by design; `guard merge`, branch protection and the sandboxes are the
# layers that remain (`reference/hard-edges.md`).
# ---------------------------------------------------------------------------


def carries(text, phrase):
    """True where the phrase's words stand next to each other in the raw text.

    A word matches where it begins at a non-identifier position and is not continued
    by a hyphen. That one boundary rule is why `--force` never reads
    `--force-with-lease`, why `-X` reads `-XPOST`, and why `git merge-base` is not
    `git merge`. A phrase of several words matches only where those words stand
    together, so an option wedged between them escapes — inside the accepted residual.
    """
    return re.search(r'(?<!\w)' + r'\s+'.join(re.escape(word) for word in phrase.split())
                     + r'(?!-)', text) is not None


REFUSED_WORDS = {
    'worker': ('merge', 'tag', 'release', '--force', 'branch -D', 'branch --delete',
               'push --delete', 'worktree remove'),
    'reviewer': ('push', 'merge', 'tag', 'release', 'delete', 'rm'),
    'orchestrator': ('gh pr merge', 'git merge'),
}
# A `gh` command carrying one of these writes through the API; the reviewer is read-only.
REVIEWER_GH_WRITE = ('-X', '--method', '-f', '-F', '--input')
# An `rm` whose first option carries `r` or `R`, or spells `--recursive`.
RECURSIVE_RM = re.compile(r'(?<!\w)rm\s+(?:-[A-Za-z]*[rR]|--recursive)(?!-)')
# The two names a default branch has. Written here rather than read from anywhere: a target that
# calls its branch something else is outside this rule, and the layer that catches the push it
# admits is GitHub's branch protection (#326).
DEFAULT_BRANCHES = ('main', 'master')

# ---------------------------------------------------------------------------
# Every refusal is a reminder, not a wall. A role that reaches for a guarded word has usually
# forgotten which lane it is in rather than defected, and the harness feeds this text back to
# the model as the tool result — so it is written to be acted on: what was refused, what the
# role does instead, the one page to read, and, because the scan is textual and a benign
# command can spell a word, how to re-spell when the operation was not the intent (#323).
# ---------------------------------------------------------------------------
INSTEAD = {
    'worker': ('a worker pushes its own task branch and hands the PR back to the orchestrator, '
               'which owns acceptance, merge and teardown'),
    'reviewer': 'a reviewer returns a verdict and writes nothing',
    'orchestrator': ('the orchestrator merges only through `<plugin>/scripts/guard merge`, which '
                     'verifies the reviewed head, proves the rebase and reads GitHub itself'),
}
ROLE_PAGE = {
    'worker': "`reference/worker.md`'s Never section",
    'reviewer': "`reference/code-review-prompt.md`'s Output format section",
    'orchestrator': "`reference/orchestrator.md`'s Acceptance and integration section",
}
RESPELL = ('If that operation was not the intent — the word sits in a commit message, an issue '
           'body or a search pattern — re-spell the command so the word is absent: put the text in '
           'a file and pass the file (`--body-file`, `-F`, a script), or search with a pattern that '
           'does not spell it. That detour is legitimate.')


def refusal(role, word, subject='a command', qualifier=''):
    """The one refusal template, filled with the word the caller actually wrote."""
    return (f'{role} role refuses {subject} carrying {word!r}{qualifier}. '
            f'Instead, {INSTEAD[role]}. Read {ROLE_PAGE[role]}. {RESPELL}')


def temp_cleanup(text, at):
    """True when every absolute path after an `rm` is a real path under `/tmp/`."""
    targets = [word.strip('\'"()`') for word in text[at:].split()]
    absolute = [target for target in targets if target.startswith('/')]
    return bool(absolute) and all(
        target.startswith('/tmp/') and len(target) > len('/tmp/') and '..' not in target.split('/')
        for target in absolute)


def command_refusal(role, text):
    """The whole shell decision: which of this role's words the raw text carries."""
    for word in REFUSED_WORDS[role]:
        if carries(text, word):
            return refusal(role, word)
    if role == 'reviewer' and carries(text, 'gh'):
        for flag in REVIEWER_GH_WRITE:
            if carries(text, flag):
                return refusal(role, flag, subject='a `gh` command')
    if role == 'worker':
        recursive = RECURSIVE_RM.search(text)
        if recursive and not temp_cleanup(text, recursive.end()):
            return refusal(role, ' '.join(recursive.group().split()),
                           qualifier=' whose target is not under /tmp/')
        # The orchestrator's is not here: founding pushes its first commits to the default
        # branch, and once founding has set protection GitHub refuses the push server-side.
        if carries(text, 'push'):
            named = next((name for name in DEFAULT_BRANCHES if carries(text, name)), None)
            if named:
                return refusal(role, 'push',
                               qualifier=f' that also names the default branch {named!r}')
    return None


def tool_decision(role, tool, arguments):
    """The hook's whole decision: this role's word list, against a command's raw text.

    A tool name is admitted for every role. Only a shell tool supplies command text for the
    role's word list to decide.
    """
    if tool not in ('Bash', 'exec_command'):
        return None
    return command_refusal(role, arguments.get('command', arguments.get('cmd', '')) or '')


def codex_hook_config(root, role):
    import shlex
    require(role in ('worker', 'reviewer'), 'executor role required')
    command = shlex.join([str(Path(root) / 'hooks/pre-tool-use'), '--role', role])
    return '\n'.join([
        'hooks.PreToolUse=[{matcher=".*",hooks=[{type="command",command='
        + json.dumps(command) + ',timeout=30}]}]',
        'agents.default_subagent_model="gpt-6-astra"',
        'agents.default_subagent_reasoning_effort="high"',
    ])

