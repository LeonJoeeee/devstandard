"""Exercise native Codex install/discovery/removal without changing existing configuration."""
from pathlib import Path
import argparse, difflib, json, os, shutil, subprocess, sys, tempfile, tomllib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--log-dir', type=Path)
args = parser.parse_args()
source = Path(__file__).resolve().parents[1]
config_path = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'config.toml'
before_config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}

def cli(*args):
    p = subprocess.run(['codex','plugin',*args,'--json'], capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)

def report(claim, before, after):
    """Say what a cleanup assertion saw, not merely that it saw a change.

    A restoration check that reports only *that* state moved forces the guessing it exists to
    prevent, so both cleanup assertions below render their message through here: the captured
    value, the observed value, and a unified diff of the two. `default=str` keeps TOML dates
    printable; the message is built only when the assertion has already failed.
    """
    def show(value):
        return json.dumps(value, indent=2, sort_keys=True, default=str).splitlines()
    before, after = show(before), show(after)
    return '\n'.join([claim, 'captured before:', *before, 'observed after:', *after,
                      'difference (- captured, + observed):',
                      *difflib.unified_diff(before, after, 'captured', 'observed', lineterm='')])

def assert_cleaned(what, section, key, before, after, mine):
    """Judge one registry listing on what this test is responsible for, and on nothing else.

    This check owns the probe's own registrations: every entry this run added must be gone
    afterwards, and every entry that was already there must still be there, unchanged. It
    deliberately does not own an entry it did not create, so a new, unrelated one appearing
    mid-run passes. The pinned Codex CLI registers its own curated marketplace from a
    background startup sync during any session; the older claim that the whole listing was
    byte-identical therefore made green depend on out-running a third party's process, which
    is what #391 diagnosed and #394 narrowed. Widening it back reinstates that race.

    Nothing this repository can cause escapes as a result: `marketplace add` writes
    `[marketplaces.<name>]` and `plugin add` writes `[plugins."<id>"]` into `config.toml`,
    so a registration of ours that outlives the run still fails the unnarrowed config
    comparison above. The CLI's curated sync writes no config at all — it materialises under
    `$CODEX_HOME/.tmp/` — which is exactly why that comparison keeps its whole-file scope.
    """
    before_rows = {row[key]: row for row in before[section]}
    after_rows = {row[key]: row for row in after[section]}
    left = sorted(row[key] for row in after[section] if mine(row))
    lost = sorted(k for k, row in before_rows.items() if after_rows.get(k) != row)
    assert not left and not lost, report(
        what + ': this probe did not clean up after itself.'
        ' Left behind by this probe: ' + (', '.join(left) or 'none') + '.'
        ' Present before and now missing or altered: ' + (', '.join(lost) or 'none') + '.'
        ' This check owns only the probe\'s own entries and the ones it found; an unrelated'
        ' entry appearing is a third party\'s registration, outside it, and not a failure.',
        before, after)

before_markets = cli('marketplace','list')
before_plugins = cli('list')
with tempfile.TemporaryDirectory(prefix='codex-plugin-probe-') as temp:
    root = Path(temp) / 'devstandard'
    shutil.copytree(source, root, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    name = 'devstandard-probe-' + Path(temp).name.rsplit('-', 1)[-1]
    path = root / '.agents/plugins/marketplace.json'
    document = json.loads(path.read_text()); document['name'] = name
    path.write_text(json.dumps(document, indent=2) + '\n')
    added = installed = False
    try:
        result = cli('marketplace','add',str(root)); added = True
        print('MARKETPLACE', json.dumps(result))
        result = cli('add','devstandard@'+name); installed = True
        print('INSTALL', json.dumps(result))
        print('DISCOVERY', json.dumps(cli('list','--marketplace',name)))
        cache = config_path.parent / 'plugins/cache' / name / 'devstandard'
        for candidate in cache.glob('*/.codex-plugin/plugin.json'):
            package = candidate.parent.parent
            for rel in ('.codex-plugin/plugin.json','hooks/hooks.json','hooks/session-start','hooks/pre-tool-use','skills/devstandard/SKILL.md'):
                assert (package / rel).read_bytes() == (root / rel).read_bytes(), rel
            assert os.access(package / 'hooks/session-start', os.X_OK)
            assert os.access(package / 'hooks/pre-tool-use', os.X_OK)
            print('CACHE', str(package), 'exact package bytes and executable modes verified', flush=True)
            command = [sys.executable, str(source / '.github/test-codex-runtime.py'),
                       '--native-plugin', 'devstandard@' + name, '--plugin-root', str(package)]
            if args.log_dir:
                command += ['--log-dir', str(args.log_dir)]
            subprocess.run(command, check=True, timeout=300)
            # Run the emitted receipt through both actual native spawn protocols
            # while this exact cached plugin is installed, before removing it.
            command = [sys.executable, str(source / '.github/test-codex-native.py'),
                       '--native-plugin', 'devstandard@' + name, '--plugin-root', str(package),
                       '--log-dir', str(args.log_dir / 'workers' if args.log_dir
                                        else Path(temp) / 'native-workers')]
            subprocess.run(command, check=True, timeout=300)
            break
        else:
            raise AssertionError('installed plugin cache was not found')
    finally:
        # Check restoration even when a runtime assertion fails, and still remove
        # the temporary marketplace if plugin removal itself reports an error.
        try:
            if installed:
                print('REMOVE', json.dumps(cli('remove','devstandard@'+name)))
        finally:
            try:
                if added:
                    print('REMOVE_MARKETPLACE', json.dumps(cli('marketplace','remove',name)))
            finally:
                after_config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
                assert after_config == before_config, report(
                    'user config changed semantically; inspect only probe entry before cleanup',
                    before_config, after_config)
                after_markets = cli('marketplace','list')
                assert_cleaned('marketplace registry', 'marketplaces', 'name',
                               before_markets, after_markets, lambda row: row['name'] == name)
                after_plugins = cli('list')
                assert_cleaned('installed plugins', 'installed', 'pluginId', before_plugins,
                               after_plugins, lambda row: row['marketplaceName'] == name)
                print('CLEANUP: user configuration unchanged; probe marketplace and plugin gone,'
                      ' pre-existing entries intact', flush=True)
    print('PASS: installed/discovered/cached/removed; user configuration unchanged and this'
          ' probe left no marketplace or plugin behind')
