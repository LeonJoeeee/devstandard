#!/usr/bin/env python3
"""Mechanical guard primitives. Python 3.9+, git 2.38+, authenticated gh."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote


class Refusal(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refusal(message)


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


def protection_check(repo, branch, checks):
    state = api(f'repos/{repo}/branches/{quote(branch, safe="")}/protection')
    status = state.get('required_status_checks') or {}
    require(status.get('strict') is True, 'protection requires strict up-to-date checks')
    require(set(checks) <= set(status.get('contexts', [])), 'protection missing required checks')
    require((state.get('enforce_admins') or {}).get('enabled') is True, 'protection must enforce admins')
    for field in ('allow_force_pushes', 'allow_deletions'):
        require((state.get(field) or {}).get('enabled') is False, f'protection must disable {field}')
    return {'repo': repo, 'branch': branch, 'required_checks': checks, 'protection': 'pass'}


def compare_rebase(project, old_base, old_head, new_base, new_head):
    """Replay in a disposable clone; never move the caller's refs/index/worktree."""
    project = Path(project).resolve()
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    clean_env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                     GIT_TERMINAL_PROMPT='0', GIT_AUTHOR_NAME='Rebase proof',
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

    paths = changed(old_base, old_head) | changed(new_base, new_head)
    require(paths, 'empty PR requires full review')
    for path in sorted(paths):
        # Entry identity includes mode, object type and blob bytes, including deletion and symlinks.
        old = git(project, 'ls-tree', '-z', old_head, '--', ':(literal)' + path)
        new = git(project, 'ls-tree', '-z', new_head, '--', ':(literal)' + path)
        require(old == new, f'PR-changed path is not byte/mode-identical: {path!r}')
        require(not old.startswith('160000 '), 'submodules require full review')
    with tempfile.TemporaryDirectory(prefix='devstandard-rebase-proof-') as scratch:
        clone = Path(scratch) / 'replay'
        run('git', 'clone', '--shared', '--no-checkout', '--quiet', str(project), str(clone), env=clean_env)
        git(clone, 'checkout', '--detach', old_head)
        try:
            git(clone, '-c', 'rerere.enabled=false', 'rebase', '--no-autostash', '--no-gpg-sign',
                '--reapply-cherry-picks', '--empty=keep', '--onto', new_base, old_base)
        except Refusal as error:
            raise Refusal(f'conflict-free rebase proof refused: {error}') from error
        require(git(clone, 'rev-parse', 'HEAD^{tree}') == git(project, 'rev-parse', new_head + '^{tree}'),
                'new head differs from conflict-free replay tree')
    return {'old_base': old_base, 'accepted_head': old_head, 'base': new_base,
            'head': new_head, 'paths': sorted(paths), 'comparison': 'pass'}


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
    body = row['body']
    # Match the merged review-packet publisher's Goal presentation tolerance.
    # Normalize only that presentation; return the original whole verdict unchanged.
    body = re.sub(r'^ {0,3}###[ \t]+[*_]{0,2}Goal verdict[*_]{0,2}[ \t]*(?:#+[ \t]*)?\r?\n',
                  '### Goal verdict\n', body, flags=re.M)
    body = re.sub(r'(^### Goal verdict\n)(?:[ \t]*\r?\n)*[ \t]*[*_]{0,2}(Yes|No)[*_]{0,2}(?=[\W_]|$)',
                  r'\1\2', body, flags=re.M)
    require(re.search(r'^Reviewer: [^\n]+ — reviewed\s+' + re.escape(head) + r'\s*$', body, re.M),
            'latest verdict does not review the exact accepted head')
    require(re.search(r'^### Goal verdict\n(?:Yes' + ('|No' if allow_goal_no else '') + r') — .+', body, re.M),
            'Goal Yes verdict required (or recorded orchestrator ruling)')
    floor = re.search(r'^### Floor\n(.*?)^### Notes\n', body, re.M | re.S)
    require(floor, 'missing Floor section')
    for label in ('1. Evidence-backed completion claim:', '2. Authorization and scope:'):
        values = re.findall('^' + re.escape(label) + r' (Pass|Fail) — .+', floor[1], re.M)
        require(values == ['Pass'], 'both Floor checks must Pass')
    require(re.search(r'^### Notes\n.+', body, re.M), 'incomplete verdict: missing Notes')
    for heading in ('### Goal verdict', '### Floor', '### Notes', 'Ready to merge:'):
        require(len(re.findall('^' + re.escape(heading), body, re.M)) == 1,
                'duplicate or missing verdict section')
    goal = re.search(r'^### Goal verdict\n(Yes|No)', body, re.M)[1]
    require(re.search(r'^Ready to merge: ' + ('Yes' if goal == 'Yes' else 'No') + r' — .+', body, re.M),
            'readiness contradicts Goal/Floor')
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
        require('2. Authorization and scope: Fail' not in last['row']['body'],
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


def merge_check(project, repo, number, old_base=None, old_head=None):
    """Read current remote pins and require both review and integration evidence."""
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
    checks = settings.get('required_checks', ['test'])
    protection_check(repo, default, checks)
    comments = api(f'repos/{repo}/issues/{number}/comments?per_page=100', '--paginate')
    publishers = settings.get('record_logins', [repo.split('/')[0]])
    comments = [row for row in comments if row.get('user', {}).get('login') in publishers]
    verdict = merge_acceptance(comments, old_head or head)
    proof = None
    if old_head:
        require(old_base, 'prior acceptance requires its review base')
        require(verdict['record'].get('base') == old_base,
                'prior acceptance must record the exact old review base (#203 record)')
        proof = compare_rebase(project, old_base, old_head, base, head)
    flag = re.search(r'^architecture-level:\s*(true|false)\s*$', pr.get('body') or '', re.I | re.M)
    recorded_flag = verdict['record'].get('architecture')
    require(flag or recorded_flag in ('YES', 'NO'), 'explicit architecture-level flag required')
    architecture = (flag and flag[1].lower() == 'true') or recorded_flag == 'YES'
    if architecture:
        require(authorized(repo, head, f'merge {repo}#{number}', 'architecture', settings),
                'architecture-level merge requires recorded human sign-off')
    ci = commit_checks(repo, head, checks + [f'merged-result / {base} / {head}'])
    latest = api(f'repos/{repo}/pulls/{number}')
    latest_base = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    require(latest == pr and latest_base == base, 'PR or base changed during merge verification')
    return {'repo': repo, 'pr': number, 'base': base, 'head': head,
            'verdict': verdict['id'], 'comparison': proof, 'checks': ci, 'merge': 'pass'}


def unsupported_shell(command):
    """Conservative raw gate, including quoted data: no expansion or compound grammar."""
    return bool(re.search(r'[\x00-\x08\x0a-\x1f\x7f-\x9f]|[^\S \t]|[`$(){}*?\[\]~]', command))


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
    'irreversible': [('rm', r'(?:-[^-]*[rf].*|--recursive|--force)'),
                     ('git', 'push', r'(?:--force(?:=.*)?|-[^-]*f.*|--delete|(?:.*:)?(?:refs/heads/)?main)'),
                     ('gh', 'repo', 'delete'),
                     ('gh', 'api', r'(?:(?:-X|--method=)?(?:DELETE|PUT|PATCH|POST)|-[fF].*|--(?:raw-field|field|input)(?:=.*)?)'),
                     ('guard', 'protection', '--apply'),
                     ('terraform', 'destroy'), ('kubectl', 'delete'), ('aws', 'delete(?:-.*)?')],
}
OPERATIONS = {kind: [tuple(re.compile(token) for token in operation) for operation in operations]
              for kind, operations in OPERATIONS.items()}


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
        tokens = set(words) | {Path(word).name for word in words if not any(c.isspace() for c in word)}
        for kind, operations in OPERATIONS.items():
            if any(all(any(predicate.fullmatch(token) for token in tokens) for predicate in operation)
                   for operation in operations):
                kinds.add(kind)
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


def tool_decision(role, tool, arguments, settings):
    kind = (classify(arguments.get('command', arguments.get('cmd', '')), settings)
            if tool in ('Bash', 'exec_command') else None)
    if kind == 'unparsed':
        return 'shell syntax is unsupported; use separate simple commands'
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
            if not re.fullmatch(r'(?:git (?:diff|show|cat-file|rev-parse|ls-tree|status)\b[^;&|()<>`$]*|(?:cat|rg|head|tail|ls|pwd)\b[^;&|()<>`$]*)', command):
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


def settings_for(project):
    """Only default-branch policy is authoritative; an unmerged worker edit grants nothing."""
    repo = run('gh', 'repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner', cwd=project)
    default = api(f'repos/{repo}')['default_branch']
    commit = api(f'repos/{repo}/branches/{quote(default, safe="")}')['commit']['sha']
    entries = api(f'repos/{repo}/git/trees/{commit}?recursive=1')
    path = '.github/devstandard-guards.json'
    entry = next((entry for entry in entries['tree'] if entry['path'] == path), None)
    if not entry:
        require(not entries.get('truncated'), 'cannot establish policy absence from truncated tree')
        return repo, {}
    import base64
    blob = api(f'repos/{repo}/git/blobs/{entry["sha"]}')
    settings = json.loads(base64.b64decode(blob['content']))
    require(isinstance(settings, dict), 'guard settings must be an object')
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
