#!/usr/bin/env python3
"""Mechanical guard primitives. Python 3.9+, git 2.38+, authenticated gh."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from functools import lru_cache
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


# The one file the role hook reads, on the repository's default branch. Read from the
# ref rather than the working tree, so an unmerged local edit grants nothing.
POLICY_PATH = '.github/devstandard-guards.json'


def required_checks(settings):
    """The protection contexts this target requires, named by policy, defaulting to `test`."""
    checks = settings.get('required_checks', ['test'])
    require(isinstance(checks, list) and checks
            and all(isinstance(name, str) and name for name in checks),
            'required_checks must be a non-empty list of check names')
    return list(checks)


def declared_checks(settings):
    """The checks this target's policy actually names, or none where it names no set.

    `required_checks` defaults to `test` because protection must require some context by name.
    The dispatch gate has no such need, so an undeclared set leaves it to the all-observed-green
    predicate rather than a name this method picked (#314).
    """
    return required_checks(settings) if 'required_checks' in settings else []


def merged_result_check(settings, base, head):
    """A target may rename this check, never unbind it from the exact base and head."""
    template = settings.get('merged_result_check', MERGED_RESULT)
    require(isinstance(template, str) and '{base}' in template and '{head}' in template,
            'merged_result_check must be a string naming both {base} and {head}')
    return template.replace('{base}', base).replace('{head}', head)


def project_repo(project):
    """OWNER/REPO from this checkout's own origin remote; local, so no network."""
    url = run('git', '-C', str(project), 'remote', 'get-url', 'origin')
    match = re.search(r'[:/]([^/:]+/[^/]+?)(?:\.git)?/?$', url)
    require(match, f'cannot read OWNER/REPO from the origin remote: {url!r}')
    return match[1]


def protection_check(repo, branch, checks):
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
    return {'repo': repo, 'branch': branch, 'required_checks': checks, 'protection': 'pass',
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
        # The bump rides the change PR, so rebasing past a merged bump moves only these two lines.
        if old != new and path in MANIFESTS and old.split()[:2] == new.split()[:2]:
            bumps[path] = refusing(manifest_bump, project, old_head, new_head, path, clean_env)
        require(old == new or bumps.get(path), f'PR-changed path is not byte/mode-identical: {path!r}')
        require(not old.startswith('160000 '), 'submodules require full review')
    require(not bumps or (set(bumps) == set(MANIFESTS) and bumps[MANIFESTS[0]] == bumps[MANIFESTS[1]]),
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
                # The comparison exempts these two lines, so the replay feeding it does too. Taking
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


def default_ci(repo, settings):
    """Refuse a new lane on a red default branch, judged by this target's own policy."""
    default = api(f'repos/{repo}')['default_branch']
    head = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    try:
        checks = commit_checks(repo, head, declared_checks(settings))
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
    settings = settings_for(project)
    require(project_repo(project) == repo,
            'merge repository differs from this checkout\'s origin')
    pr = api(f'repos/{repo}/pulls/{number}')
    default = api(f'repos/{repo}')['default_branch']
    base = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    head = pr['head']['sha']
    require(pr['state'] == 'open', 'merge requires an open PR')
    require(pr['base']['repo']['full_name'] == repo and pr['base']['ref'] == default,
            'merge requires the default branch of this repository')
    require(pr['base']['sha'] == base, 'PR base is not current default-branch head')
    run('git', '-C', str(project), 'merge-base', '--is-ancestor', base, head)
    checks = required_checks(settings)
    protection_check(repo, default, checks)
    comments = api(f'repos/{repo}/issues/{number}/comments?per_page=100', '--paginate')
    publishers = settings.get('record_logins', [repo.split('/')[0]])
    comments = [row for row in comments if row.get('user', {}).get('login') in publishers]
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
        require(authorized(repo, head, f'merge {repo}#{number}', 'architecture', settings),
                'architecture-level merge requires recorded human sign-off')
    ci = commit_checks(repo, head, checks + [merged_result_check(settings, base, head)])
    latest = api(f'repos/{repo}/pulls/{number}')
    latest_base = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    require(latest == pr and latest_base == base, 'PR or base changed during merge verification')
    result = {'repo': repo, 'pr': number, 'base': base, 'head': head,
              'verdict': verdict['id'] if verdict else None, 'comparison': proof, 'checks': ci, 'merge': 'pass'}
    if execute:
        method = settings.get('merge_method', 'squash')
        message = run('git', '-C', str(project), 'log', '-1', '--format=%B', head)
        trailers = re.findall(r'^(?:Claude-Session|Codex-Session|Co-authored-by):[^\r\n]+',
                              message, re.I | re.M)
        # GitHub rechecks strict protection; the SHA precondition rejects a moved PR head.
        result['result'] = api(f'repos/{repo}/pulls/{number}/merge', '--method', 'PUT',
                              '-f', 'sha=' + head, '-f', 'merge_method=' + method,
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
# refuse for any role, and nothing here reads the network. Obfuscation, interpreter
# scripts, forged local refs and runtime data are outside this boundary by design;
# `guard merge`, branch protection and the sandboxes are the layers that remain
# (`reference/hard-edges.md`).
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
MERGE_WORDS = ('gh pr merge', 'git merge')
# A `gh` command carrying one of these writes through the API; the reviewer is read-only.
REVIEWER_GH_WRITE = ('-X', '--method', '-f', '-F', '--input')
# Release commands: the orchestrator's only under a standing delegation, never a lane's.
RELEASE_WORDS = ('tag', 'release')
# An `rm` whose first option carries `r` or `R`, or spells `--recursive`.
RECURSIVE_RM = re.compile(r'(?<!\w)rm\s+(?:-[A-Za-z]*[rR]|--recursive)(?!-)')
GUARD_MERGE = ('the only admitted merge entry is `<plugin>/scripts/guard merge`, which verifies '
               'the reviewed head, proves the rebase and reads GitHub itself')
DELEGATION_SOURCE = re.compile(
    r'https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/(?:issues|pull)/[0-9]+#issuecomment-[0-9]+')


def default_branches(settings):
    """`main`, `master`, and whatever else this target's policy declares its default."""
    declared = settings.get('default_branch')
    return ['main', 'master'] + ([declared] if isinstance(declared, str) and declared else [])


def standing_delegation(settings):
    """A human's standing release delegation, relayed by default-branch policy."""
    delegation = settings.get('standing_release')
    if not isinstance(delegation, dict):
        return False
    source = DELEGATION_SOURCE.fullmatch(str(delegation.get('source', '')))
    return bool(source and source['repo'] == delegation.get('repo'))


def policy_words(settings, role):
    """Extra words a target adds for one role. Additive only, so junk adds nothing."""
    patterns = settings.get('command_patterns')
    words = patterns.get(role) if isinstance(patterns, dict) else None
    if not isinstance(words, list):
        return ()
    return tuple(word for word in words if isinstance(word, str) and word.strip())


def temp_cleanup(text, at):
    """True when every absolute path after an `rm` is a real path under `/tmp/`."""
    targets = [word.strip('\'"()`') for word in text[at:].split()]
    absolute = [target for target in targets if target.startswith('/')]
    return bool(absolute) and all(
        target.startswith('/tmp/') and len(target) > len('/tmp/') and '..' not in target.split('/')
        for target in absolute)


def command_refusal(role, text, settings):
    """The whole shell decision: which of this role's words the raw text carries."""
    for word in REFUSED_WORDS[role] + policy_words(settings, role):
        if carries(text, word):
            reason = f'{role} role refuses a command carrying {word!r}'
            return reason + '; ' + GUARD_MERGE if word in MERGE_WORDS else reason
    if role == 'reviewer' and carries(text, 'gh'):
        for flag in REVIEWER_GH_WRITE:
            if carries(text, flag):
                return f'reviewer role is read-only and refuses a `gh` command carrying {flag!r}'
    if role == 'orchestrator' and not standing_delegation(settings):
        for word in RELEASE_WORDS:
            if carries(text, word):
                return (f'orchestrator role refuses a command carrying {word!r} without a standing '
                        f'release delegation in {POLICY_PATH}')
    if role == 'worker':
        recursive = RECURSIVE_RM.search(text)
        if recursive and not temp_cleanup(text, recursive.end()):
            return 'worker role refuses a recursive `rm` whose target is not under /tmp/'
    if carries(text, 'push'):
        named = next((name for name in default_branches(settings) if carries(text, name)), None)
        if named:
            # A repository being founded carries no policy file, so it can carry no
            # `authorization_issue` and no record — and the push that lands that file is
            # this one. The file appearing closes the door behind it (ADR 0046, #293).
            if role == 'orchestrator' and not settings.get('_policy'):
                return None
            return (f'{role} role refuses a command carrying \'push\' that also names the '
                    f'default branch {named!r}')
    return None


READ_TOOLS = {'Read', 'Glob', 'Grep'}
WORKER_TOOLS = READ_TOOLS | {'Bash', 'Edit', 'Write', 'Skill', 'apply_patch', 'exec_command',
                             'write_stdin', 'view_image', 'update_plan'}
REVIEWER_TOOLS = READ_TOOLS | {'Bash', 'exec_command', 'view_image'}


def tool_decision(role, tool, arguments, settings):
    """The hook's whole decision: this role's tool surface, then its word list."""
    if role == 'reviewer' and tool not in REVIEWER_TOOLS:
        return 'reviewer tool surface refuses this tool'
    if role == 'worker' and tool not in WORKER_TOOLS:
        return 'worker tool surface refuses this tool'
    if tool not in ('Bash', 'exec_command'):
        if role == 'orchestrator' and re.search(r'merge|release|delete|publish|send', tool, re.I):
            return f'orchestrator role refuses tool {tool!r}; ' + GUARD_MERGE
        return None
    return command_refusal(role, arguments.get('command', arguments.get('cmd', '')) or '', settings)


@lru_cache(maxsize=None)
def settings_for(project):
    """This target's policy, read once per hook process from the local `origin/main` ref.

    Never the network and never the working tree: no fetch happens inside a tool call,
    and an unmerged local edit grants nothing. A missing ref, a missing file, a directory
    outside any repository, or JSON that will not parse all mean the built-in defaults, so
    nothing here can refuse a tool call and nothing here can refuse because the network
    dropped (#303, #323).
    """
    try:
        raw = run('git', '-C', str(project), 'show', 'origin/main:' + POLICY_PATH)
    except Exception:
        return {}
    try:
        settings = json.loads(raw)
    except ValueError:
        settings = None
    # The file is on the default branch, so this repository is guarded even where its
    # contents are junk: only its extras are lost, never a built-in refusal.
    return dict(settings, _policy=True) if isinstance(settings, dict) else {'_policy': True}


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


def authorized(repo, head, command, kind, settings):
    """The human's head-bound sign-off record on the policy's authorization issue.

    Since #323 this is the only record left, and `guard merge` is its only reader: an
    architecture-level merge requires it. The role hook performs no lookup of any kind.
    """
    import hashlib
    from datetime import datetime, timezone
    issue = settings.get('authorization_issue')
    if not issue:
        return False
    rows = api(f'repos/{repo}/issues/{issue}/comments?per_page=100', '--paginate')
    prefix = '<!-- devstandard-authorization-v1 -->\n'
    digest = hashlib.sha256(command.encode()).hexdigest()
    for row in reversed(rows):
        if row.get('user', {}).get('login') not in settings.get('human_logins', []):
            continue
        if not row['body'].startswith(prefix):
            continue
        try:
            record = json.loads(row['body'][len(prefix):])
            if (record.get('repo'), record.get('head'), record.get('kind'), record.get('command_sha256')) != (repo, head, kind, digest):
                continue
            return record.get('revoked') is not True and datetime.fromisoformat(record['expires']) > datetime.now(timezone.utc)
        except (ValueError, KeyError, TypeError):
            return False  # A malformed later authorization must not revive an older grant.
    return False
