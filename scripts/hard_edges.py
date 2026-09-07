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
                           normalize, version_only)


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


def absent(error):
    """Only an explicit 404 proves a remote thing is missing; every other failure stays closed."""
    return '(HTTP 404)' in str(error)


def required_checks(settings):
    """The protection contexts this target requires, named by policy, defaulting to `test`."""
    checks = settings.get('required_checks', ['test'])
    require(isinstance(checks, list) and checks
            and all(isinstance(name, str) and name for name in checks),
            'required_checks must be a non-empty list of check names')
    return list(checks)


def merged_result_check(settings, base, head):
    """A target may rename this check, never unbind it from the exact base and head."""
    template = settings.get('merged_result_check', MERGED_RESULT)
    require(isinstance(template, str) and '{base}' in template and '{head}' in template,
            'merged_result_check must be a string naming both {base} and {head}')
    return template.replace('{base}', base).replace('{head}', head)


def unprotected(repo, branch):
    """True only when the branch's protection is provably absent."""
    try:
        api(f'repos/{repo}/branches/{quote(branch, safe="")}/protection')
    except Refusal as error:
        return absent(error)
    return False


def founding_setup(repo, command, settings):
    """The one act a pre-policy repository cannot otherwise perform: its founding push.

    Admitted only while the default branch provably carries no policy file AND no
    protection — together, proof that this push can bypass no policy and replace no
    protection. An authorization record cannot precede the policy file that names its
    issue, so without this the founding push is unreachable and a seeded project can
    never become guarded. Landing that file is the last push this admits.
    """
    if settings.get('_policy') is not False:
        return False
    default = settings.get('_default_branch', 'main')
    words = simple_argv(command)
    if not words or Path(words[0]).name != 'git' or words[1:2] != ['push']:
        return False
    options = [word for word in words[2:] if word.startswith('-')]
    arguments = [word for word in words[2:] if not word.startswith('-')]
    if any(option not in ('-u', '--set-upstream') for option in options) or len(arguments) < 2:
        return False
    for refspec in arguments[1:]:
        if (not re.fullmatch(r'[A-Za-z0-9_./-]+(?::[A-Za-z0-9_./-]+)?', refspec)
                or destination_branch(refspec) != default):
            return False
    return unprotected(repo, default)


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


def commit_checks(repo, sha, required=('test',)):
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
    require(all(latest.get(name) == 'success' for name in required),
            f'CI not green for {sha}: required={list(required)!r}, observed={latest!r}')
    require(all(value in ('success', 'neutral', 'skipped') for value in latest.values()),
            f'CI red or unreported for {sha}: {latest!r}')
    return latest


def default_ci(repo):
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
    # Read the same plain form, and the same grounded decision lines, the review-packet publisher
    # reads; keep the original verdict intact.
    body = normalize(row['body'])
    require(re.search(r'^Reviewer: [^\n]+ — reviewed\s+' + re.escape(head) + r'\s*$', body, re.M),
            'latest verdict does not review the exact accepted head')
    goal = re.search(decision_line('Goal verdict', grounds=True), body, re.M)
    require(goal and (allow_goal_no or goal[1] == 'Yes'),
            'Goal Yes verdict required (or recorded orchestrator ruling)')
    floor = re.search(r'^### Floor\n(.*?)^### Notes\n', body, re.M | re.S)
    require(floor, 'missing Floor section')
    for label in FLOOR_LABELS:
        require(re.findall(decision_line(label, grounds=True), floor[1], re.M) == ['Pass'],
                'both Floor checks must Pass')
    require(re.search(r'^### Notes\n(?:[ \t]*\r?\n)*.+', body, re.M), 'incomplete verdict: missing Notes')  # ordinary Markdown leaves a blank line after a heading
    for heading in ('### Goal verdict', '### Floor', '### Notes', 'Ready to merge:'):
        require(len(re.findall('^' + re.escape(heading), body, re.M)) == 1,
                'duplicate or missing verdict section')
    ready = re.search(decision_line('Ready to merge', grounds=True), body, re.M)
    require(ready and ready[1] == goal[1], 'readiness contradicts Goal/Floor')
    require(body.rstrip().endswith('Post this verdict whole on the PR before acting on it.'), 'incomplete whole verdict')
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
            raise Refusal('accepted verdict: Notes do not authorize another round')
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
    policy_repo, settings = settings_for(project)
    require(policy_repo == repo, 'policy repository differs from merge repository')
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


def shell_syntax(command):
    """Mask quoted literals, retaining dollar/backtick refusals in double quotes."""
    def mask(match):
        raw = match[0]
        if raw.startswith("'"):
            return ' ' * len(raw)
        if raw.startswith('"'):
            return re.sub(r'[^$`]', ' ', raw)
        # Consume escaped quotes without opening a quoted segment; retain the
        # existing conservative refusals for escaped expansion outside quotes.
        return raw
    return re.sub(r"""'[^']*'|"(?:[^"\\]|\\.)*"|\\.""", mask, command)


def unsupported_shell(command):
    """Reject control characters everywhere and unmodelled nonliteral syntax."""
    return bool(re.search(r'[\x00-\x08\x0a-\x1f\x7f-\x9f]|[^\S \t]', command)
                or re.search(r'[`$(){}*?\[\]~]', shell_syntax(command)))


# Closed lexical grammar: every byte must belong to horizontal space, a literal
# word (possibly quoted/escaped), or an explicitly handled operator. Keep raw
# spellings so quoted operators and quoted/spaced descriptor numbers stay argv.
SHELL_WORD = re.compile(r'''(?:[^ \t;&|()<>'"\\]+|'[^']*'|"(?:[^"\\]|\\.)*"|\\.)+''')
SHELL_OPERATORS = re.compile(r'[;&|<>]+')
SHELL_SEPARATORS = {';', '&&', '||', '|', '&'}
SHELL_REDIRECTIONS = {'<', '>', '>>', '&>', '&>>', '>|', '>&', '<&', '<<<', '<>'}
SHELL_WRAPPERS = {
    'eval', 'sh', 'bash', 'dash', 'zsh', 'ksh', 'fish', 'env', 'xargs', 'command',
    'exec', 'nohup', 'setsid', 'time', 'nice', 'sudo', 'timeout', 'builtin',
    'source', '.', 'alias', 'unalias',
}
SHELL_RESERVED = {'!', 'if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'until',
                  'do', 'done', 'case', 'esac', 'select', 'in', 'function', 'coproc'}


def shell_segments(command):
    """Recover literal argv, removing redirections without losing command words.

    No expansion, wrapper execution, here-doc body, or compound grammar is
    inferred. Unhandled input raises ValueError before any segment is classified.
    Comments retain the existing conservative over-scan (never discard a suffix).
    """
    import shlex
    tokens = []
    at = 0
    while at < len(command):
        if command[at] in ' \t':
            at += 1
            continue
        operator = SHELL_OPERATORS.match(command, at)
        if operator:
            raw = operator[0]
            if raw not in SHELL_SEPARATORS | SHELL_REDIRECTIONS:
                raise ValueError('unsupported shell operator')
            tokens.append(('operator', raw, raw, at, operator.end()))
            at = operator.end()
            continue
        word = SHELL_WORD.match(command, at)
        if not word:
            raise ValueError('unread shell syntax')
        raw = word[0]
        lexer = shlex.shlex(raw, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ''
        decoded = list(lexer)
        if (len(decoded) != 1 or decoded[0] is None or lexer.state is not None
                or lexer.instream.read() or lexer.pushback):
            raise ValueError('incomplete shell word')
        tokens.append(('word', decoded[0], raw, at, word.end()))
        at = word.end()

    segments, words = [], []
    last_word_index = None
    i = 0
    while i < len(tokens):
        token_type, value, raw, start, end = tokens[i]
        if token_type == 'word':
            words.append(value)
            last_word_index = i
        elif value in SHELL_REDIRECTIONS:
            # Only an unquoted adjacent IO_NUMBER belongs to the operator.
            # `gh 2>file ...` removes 2; `gh 2 >file ...` and `gh "2">file ...` do not.
            if i and value[0] in '<>':
                previous = tokens[i - 1]
                if (last_word_index == i - 1 and previous[4] == start
                        and re.fullmatch(r'[0-9]+', previous[2])):
                    if words and words[-1] == previous[1]:
                        words.pop()
            i += 1
            if i >= len(tokens) or tokens[i][0] != 'word':
                raise ValueError('redirection requires a literal target')
            # Target is consumed as data, including fd duplication/move/close.
        else:
            if words:
                segments.append(words)
            words = []
        i += 1
    if words:
        segments.append(words)
    for words in segments:
        executable = words[0] if words[0] == '.' else Path(words[0]).name
        if (executable in SHELL_WRAPPERS | SHELL_RESERVED
                or re.match(r'^[A-Za-z_][A-Za-z_0-9]*=', words[0])):
            raise ValueError('wrapper or compound shell command is unsupported')
    return segments


# Each tuple is a conjunction of token predicates, in any order in one segment.
# Recognition is shared by every role; only the consequence depends on role.
# Configured patterns may extend these built-in operations, never disable them.
OPERATIONS = {
    'merge': [('gh', 'pr', 'merge'), ('guard', 'merge')],
    'release': [('git', 'tag'),
                ('git', 'push', r'(?:--tags|--follow-tags|.*refs/tags/.*|.*\bv[0-9]+\.[0-9]+\.[0-9]+\b.*)'),
                ('gh', 'release', '(?:create|upload|edit|delete)'),
                ('(?:npm|pnpm|yarn)', 'publish'), ('twine', 'upload')],
    'irreversible': [('rm', r'(?:-[rRf]|--recursive|--force)'),
                     ('git', 'push', r'(?:--force(?:=.*)?|-f|--force-with-lease(?:=.*)?|--force-if-includes|--mirror|--delete|-d|[+:].+|:|--all|--branches|--prune|(?:.*:)?(?:refs/heads/)?main)'),
                     ('git', 'branch', '-D'),
                     ('git', 'branch', '(?:-d|--delete)', '(?:-f|--force)'),
                     ('git', 'tag', '(?:-d|--delete)'),
                     ('git', 'update-ref', '-d'),
                     ('gh', 'release', 'delete'),
                     ('gh', 'repo', 'delete'),
                     ('gh', 'api', r'(?:(?:-X|--method=)?(?:DELETE|PUT|PATCH|POST)|-[fF].*|--(?:raw-field|field|input)(?:=.*)?)'),
                     ('guard', 'protection', '--apply'),
                     ('terraform', 'destroy'), ('terraform', 'apply', '-destroy'),
                     ('kubectl', 'delete'), ('aws', 'delete(?:-.*)?')],
}
OPERATIONS = {kind: [tuple(re.compile(token) for token in operation) for operation in operations]
              for kind, operations in OPERATIONS.items()}


def indicator_tokens(words):
    """Keep literals and expand short clusters before matching operation indicators.

    This is conservative token recognition, not option-value parsing: a value
    that looks like an option may also match. Long options remain whole; short
    suffixes retain attached values (e.g. -iXDELETE supplies -XDELETE).
    """
    tokens = set(words) | {Path(word).name for word in words if not any(c.isspace() for c in word)}
    for word in words:
        if re.fullmatch(r'-[A-Za-z0-9][^\s]*', word):
            for at, char in enumerate(word[1:], 1):
                if not char.isalnum():
                    break
                tokens.add('-' + char)
                tokens.add('-' + word[at:])
    return tokens


def destination_branch(refspec):
    """Normalize the destination of bare, source:destination, and deletion refs."""
    destination = refspec.rsplit(':', 1)[-1]
    for prefix in ('refs/heads/', 'heads/'):
        if destination.startswith(prefix):
            return destination[len(prefix):]
    return destination


def wildcard_branch_destination(refspec):
    """A wildcard branch destination reaches every match, the default branch included.

    Quoting is how a caller stops the local shell expanding a refspec, so the
    pattern arrives at git intact: this is the `--all`/`--branches` effect spelled
    as a refspec. Only a positional branch ref counts — an option keeps whatever
    its own indicator decides, and another namespace (refs/tags/, refs/notes/)
    keeps the kind its own predicate gives it.
    """
    if refspec.startswith('-'):
        return False
    destination = refspec.rsplit(':', 1)[-1]
    if destination.startswith('refs/') and not destination.startswith('refs/heads/'):
        return False
    return '*' in destination_branch(refspec)


def classify(command, settings):
    """Recover complete segments and recognize operation tokens independently of role."""
    if unsupported_shell(command):
        return 'unparsed'
    try:
        segments = shell_segments(command)
    except ValueError:
        return 'unparsed'
    kinds = set()
    for words in segments:
        # Retain literal tokens as well as executable basenames. Do not split
        # quoted prose, consume option values, or combine separate segments.
        tokens = indicator_tokens(words)
        for kind, operations in OPERATIONS.items():
            if any(all(any(predicate.fullmatch(token) for token in tokens) for predicate in operation)
                   for operation in operations):
                kinds.add(kind)
        # Repository metadata, never a worker-supplied policy field, provides
        # the actual default branch. Retain the built-in main indicator too, and
        # a wildcard destination, which names the default branch without spelling it.
        defaults = {'main', settings.get('_default_branch', 'main')}
        if {'git', 'push'} <= tokens and any(
                word.rsplit(':', 1)[-1] in defaults or destination_branch(word) in defaults
                or wildcard_branch_destination(word)
                for word in words):
            kinds.add('irreversible')
        # Target-specific patterns extend the shared recognition surface. They
        # cannot replace built-ins or reinterpret unsupported shell composition.
        flat = ' '.join('<argument>' if any(c.isspace() for c in word)
                        else Path(word).name if Path(word).name in ('git', 'gh', 'guard') else word
                        for word in words)
        for kind in OPERATIONS:
            if any(re.search(pattern, flat) for pattern in settings.get('command_patterns', {}).get(kind, [])):
                kinds.add(kind)
    # A release delegation never permits an irreversible command appended to a release.
    return next((kind for kind in ('merge', 'irreversible', 'release') if kind in kinds), None)


def simple_argv(command):
    """Role exceptions admit one literal command, without redirects or composition."""
    if unsupported_shell(command) or re.search(r'[;&|<>]', shell_syntax(command)):
        return []
    segments = shell_segments(command)
    return segments[0] if len(segments) == 1 else []


def worker_routine_command(command, settings):
    words = simple_argv(command)
    if not words:
        return False
    if Path(words[0]).name == 'rm':
        targets, options = [], True
        for word in words[1:]:
            if options and word == '--':
                options = False
            elif options and word.startswith('-'):
                if not re.fullmatch(r'(?:-[rRfivI]+|--recursive|--force|--verbose)', word):
                    return False
            else:
                targets.append(Path(word))
        # Resolve existing symlinks as well as lexical parents. Never exempt a
        # temp root itself, relative/ambiguous targets, or a mixed outside list.
        roots = {Path('/tmp').resolve(), Path(tempfile.gettempdir()).resolve()}
        roots.discard(Path('/'))
        return bool(targets) and all(
            target.is_absolute() and '..' not in target.parts
            and target.resolve() not in roots
            and any(root in target.resolve().parents for root in roots)
            for target in targets)
    if Path(words[0]).name != 'git' or words[1:2] != ['push']:
        return False
    safe_flags = re.compile(r'(?:--force-with-lease(?:=.*)?|--force-if-includes)')
    flags = [word for word in words[2:] if safe_flags.fullmatch(word)]
    arguments = [word for word in words[2:] if not safe_flags.fullmatch(word)]
    if not flags or len(arguments) < 2 or any(word.startswith('-') for word in arguments):
        return False
    for refspec in arguments[1:]:
        if not re.fullmatch(r'[A-Za-z0-9_./-]+(?::[A-Za-z0-9_./-]+)?', refspec):
            return False
        destination = refspec.rsplit(':', 1)[-1]
        branch = destination_branch(refspec)
        if (destination.startswith('refs/') and not destination.startswith('refs/heads/')
                or branch in ('HEAD', 'main', settings.get('_default_branch', 'main'))):
            return False
    # Only lease indicators are excused. Another recognized operation or a
    # repository extension on the remaining command retains its refusal.
    import shlex
    return classify(shlex.join(words[:2] + arguments), settings) is None


def reviewer_github_read(command):
    words = simple_argv(command)
    if not words or Path(words[0]).name != 'gh':
        return False
    api_read = words[1:2] == ['api']
    if api_read:
        arguments = words[2:]
        switches = {'--paginate', '--slurp', '--include', '-i', '--silent'}
        values = {'--method', '-X', '--jq', '-q', '--template', '-t', '--hostname'}
    elif tuple(words[1:3]) in {('pr', 'view'), ('issue', 'view'), ('run', 'view'), ('pr', 'checks')}:
        arguments = words[3:]
        switches = {'--comments', '-c', '--log', '--log-failed', '--verbose', '-v',
                    '--exit-status', '--required'}
        values = {'--json', '--jq', '-q', '--template', '-t', '--repo', '-R',
                  '--job', '-j', '--attempt', '-a'}
    else:
        return False
    positional = []
    at = 0
    while at < len(arguments):
        word = arguments[at]
        option, equals, value = word.partition('=')
        if word in switches:
            at += 1
            continue
        if not equals and word.startswith('-') and not word.startswith('--') and len(word) > 2:
            option, value = word[:2], word[2:]
        if option in values:
            if not equals and not value:
                at += 1
                if at == len(arguments):
                    return False
                value = arguments[at]
            if api_read and option in ('--method', '-X') and value != 'GET':
                return False
        elif word.startswith('-'):
            return False
        else:
            positional.append(word)
        at += 1
    # GraphQL defaults to POST; only ordinary REST endpoint reads are admitted.
    return (len(positional) == 1 and positional[0].strip('/') != 'graphql'
            and ':' not in positional[0]) if api_read else len(positional) <= 1


# find is the one read command carrying an action language of its own: these primaries
# execute, delete, or write a file, so a find bearing any of them is not a reviewer read.
FIND_ACTIONS = {'-delete', '-exec', '-execdir', '-ok', '-okdir',
                '-fprint', '-fprint0', '-fprintf', '-fls'}


def tool_decision(role, tool, arguments, settings):
    kind = (classify(arguments.get('command', arguments.get('cmd', '')), settings)
            if tool in ('Bash', 'exec_command') else None)
    if kind == 'unparsed':
        return 'shell syntax is unsupported; use separate simple commands'
    if kind == 'irreversible' and role == 'worker' and worker_routine_command(
            arguments.get('command', arguments.get('cmd', '')), settings):
        return None
    if kind and role in ('worker', 'reviewer'):
        return f'{role} role refuses recognized {kind} operation'
    read_tools = {'Read', 'Glob', 'Grep'}
    worker_tools = read_tools | {'Bash', 'Edit', 'Write', 'Skill', 'apply_patch', 'exec_command',
                                'write_stdin', 'view_image', 'update_plan'}
    if role == 'reviewer':
        # Codex keeps a shell only for pinned git/read commands; its OS sandbox stays read-only.
        if tool not in read_tools | {'Bash', 'exec_command', 'view_image'}:
            return 'reviewer tool surface refuses this tool'
        if tool in {'Bash', 'exec_command'}:
            command = arguments.get('command', arguments.get('cmd', ''))
            words = simple_argv(command)
            read_command = bool(words) and (
                words[0] in {'cat', 'rg', 'head', 'tail', 'ls', 'pwd'}
                or words[0] == 'find' and not FIND_ACTIONS.intersection(words[1:])
                or words[0] == 'git' and words[1:2] in [
                    ['diff'], ['show'], ['cat-file'], ['rev-parse'], ['ls-tree'], ['status']])
            if not (read_command or reviewer_github_read(command)):
                return 'reviewer tool surface refuses non-read command'
        return None
    if role == 'worker' and tool not in worker_tools:
        return 'worker tool surface refuses this tool'
    if tool not in ('Bash', 'exec_command'):
        if role == 'orchestrator' and re.search(r'(?:merge|release|delete|publish|send)', tool, re.I):
            return 'recognized external operation requires recorded authorization and the guarded CLI'
        return None
    if kind:
        if kind == 'merge':
            return 'merge requires scripts/guard merge with reviewed-head verification'
        return f'{kind} operation requires recorded authorization'
    return None


@lru_cache(maxsize=None)
def settings_for(project):
    """Only default-branch policy is authoritative; an unmerged worker edit grants nothing."""
    try:
        repo = run('gh', 'repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner', cwd=project)
    except Refusal as discovery_error:
        # Setup starts outside Git, then in a checkout without an origin. Prove that
        # local state before treating failed discovery as no repository authority.
        try:
            remotes = run('git', 'remote', cwd=project, env=dict(os.environ, LC_ALL='C')).splitlines()
        except Refusal as git_error:
            if str(git_error).startswith('fatal: not a git repository'):
                return None, {}
            raise discovery_error from git_error
        if 'origin' not in remotes:
            return None, {}
        raise
    default = api(f'repos/{repo}')['default_branch']
    try:
        commit = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    except Refusal as error:
        # A default branch with no commits carries no policy file; every other read failure refuses.
        require(absent(error), f'cannot establish policy absence: {error}')
        return repo, {'_default_branch': default, '_policy': False}
    entries = api(f'repos/{repo}/git/trees/{commit}?recursive=1')
    path = '.github/devstandard-guards.json'
    entry = next((entry for entry in entries['tree'] if entry['path'] == path), None)
    if not entry:
        require(not entries.get('truncated'), 'cannot establish policy absence from truncated tree')
        return repo, {'_default_branch': default, '_policy': False}
    import base64
    blob = api(f'repos/{repo}/git/blobs/{entry["sha"]}')
    settings = json.loads(base64.b64decode(blob['content']))
    require(isinstance(settings, dict), 'guard settings must be an object')
    patterns = settings.get('command_patterns', {})
    require(isinstance(patterns, dict) and set(patterns) <= set(OPERATIONS),
            'command_patterns must map recognized kinds to regex lists')
    for expressions in patterns.values():
        require(isinstance(expressions, list) and all(isinstance(p, str) for p in expressions),
                'command_patterns values must be regex lists')
        for expression in expressions:
            re.compile(expression)  # Invalid policy refuses even on non-shell tools.
    required_checks(settings)  # A malformed check list or merged-result name refuses at load,
    merged_result_check(settings, 'BASE', 'HEAD')  # for every role, not only at merge time.
    settings['_default_branch'] = default
    settings['_policy'] = True
    return repo, settings


def codex_hook_config(root, role):
    import shlex
    require(role in ('worker', 'reviewer'), 'executor role required')
    command = shlex.join([str(Path(root) / 'hooks/pre-tool-use'), '--role', role])
    return ('hooks.PreToolUse=[{matcher=".*",hooks=[{type="command",command='
            + json.dumps(command) + ',timeout=30}]}]')


def authorized(repo, head, command, kind, settings):
    import hashlib
    from datetime import datetime, timezone
    delegation = settings.get('standing_release') or {}
    if kind == 'release' and delegation.get('repo') == repo and re.fullmatch(
            r'https://github.com/' + re.escape(repo) + r'/(?:issues|pull)/[0-9]+#issuecomment-[0-9]+', delegation.get('source', '')):
        return True
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
