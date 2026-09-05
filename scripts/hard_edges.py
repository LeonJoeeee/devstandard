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
    return json.loads(run('gh', 'api', endpoint, *args))


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
        old = git(project, 'ls-tree', '-z', old_head, '--', path)
        new = git(project, 'ls-tree', '-z', new_head, '--', path)
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
    runs = api(f'repos/{repo}/commits/{sha}/check-runs?per_page=100').get('check_runs', [])
    statuses = api(f'repos/{repo}/commits/{sha}/status?per_page=100').get('statuses', [])
    # The API returns newest first; an older successful run must not hide a current red run.
    latest = {}
    for row in runs:
        latest.setdefault(row['name'], row.get('conclusion') if row.get('status') == 'completed' else 'pending')
    for row in statuses:
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
    require(re.search(r'^Reviewer: [^\n]+ — reviewed\s+' + re.escape(head) + r'\s*$', body, re.M),
            'latest verdict does not review the exact accepted head')
    require(re.search(r'^### Goal verdict\n(?:Yes' + ('|No' if allow_goal_no else '') + r') — .+', body, re.M),
            'Goal Yes verdict required (or recorded orchestrator ruling)')
    require(re.search(r'^### Floor\n1\. Evidence-backed completion claim: Pass — .+\n'
                      r'2\. Authorization and scope: Pass — .+', body, re.M), 'both Floor checks must Pass')
    require(re.search(r'^### Notes\n.+', body, re.M), 'incomplete verdict: missing Notes')
    require(body.rstrip().endswith('Post this verdict whole on the PR before acting on it.'), 'incomplete whole verdict')
    return row


def classify(command, settings):
    """Recognized command spellings only; this is not a shell interpreter or credential boundary."""
    import shlex
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:
        return 'unparsed'
    # Scan token windows so wrappers and ordinary command chains retain the protected spelling.
    # A quoted prose argument stays one token; do not scan inside it.
    flat = ' '.join(tokens)
    patterns = settings.get('command_patterns', {
        'merge': [r'\bgh\s+pr\s+merge\b', r'\bguard\s+merge\b', r'\bmerge-reviewed\b'],
        'release': [r'\bgit\s+tag\b', r'\bgit\s+push\b.*(?:--tags|--follow-tags|refs/tags/)',
                    r'\bgh\s+release\s+(?:create|upload|edit|delete)\b',
                    r'\b(?:npm|pnpm|yarn)\s+publish\b', r'\btwine\s+upload\b'],
        'irreversible': [r'\brm\s+[^\n]*(?:-[a-zA-Z]*[rf]|--recursive|--force)',
                         r'\bgit\s+push\b.*(?:--force\b|-f\b|--delete|:main\b|\s+main\b)',
                         r'\bgh\s+repo\s+delete\b', r'\bgh\s+api\b.*(?:DELETE|PUT|PATCH|POST)',
                         r'\b(?:terraform\s+destroy|kubectl\s+delete|aws\s+.+\s+delete)\b'],
    })
    for kind in ('merge', 'release', 'irreversible'):
        if any(re.search(pattern, flat) for pattern in patterns[kind]):
            return kind
    return None


def tool_decision(role, tool, arguments, settings):
    read_tools = {'Read', 'Glob', 'Grep'}
    worker_tools = read_tools | {'Bash', 'Edit', 'Write', 'Skill', 'apply_patch', 'exec_command',
                                'write_stdin', 'view_image', 'update_plan'}
    if role == 'reviewer':
        # Codex keeps a shell only for pinned git/read commands; its OS sandbox stays read-only.
        if tool not in read_tools | {'Bash', 'exec_command', 'view_image'}:
            return 'reviewer tool surface refuses this tool'
        if tool in {'Bash', 'exec_command'}:
            command = arguments.get('command', arguments.get('cmd', ''))
            if not re.fullmatch(r'(?:git (?:diff|show|cat-file|rev-parse|ls-tree|status)\b[^;&|<>`$]*|(?:cat|rg|sed|head|tail|ls|pwd)\b[^;&|<>`$]*)', command):
                return 'reviewer tool surface refuses non-read command'
        return None
    if role == 'worker' and tool not in worker_tools:
        return 'worker tool surface refuses this tool'
    if tool not in ('Bash', 'exec_command'):
        if role == 'orchestrator' and re.search(r'(?:merge|release|delete|publish|send)', tool, re.I):
            return 'recognized external operation requires recorded authorization and the guarded CLI'
        return None
    kind = classify(arguments.get('command', arguments.get('cmd', '')), settings)
    if kind:
        if role == 'worker':
            return f'worker role refuses recognized {kind} operation'
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


def authorized(repo, head, command, kind, settings):
    import hashlib
    from datetime import datetime, timezone
    delegation = settings.get('standing_release') or {}
    if kind == 'release' and delegation.get('repo') == repo and re.fullmatch(
            r'https://github.com/[^/]+/[^/]+/(?:issues|pull)/[0-9]+#issuecomment-[0-9]+', delegation.get('source', '')):
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
            continue
    return False
