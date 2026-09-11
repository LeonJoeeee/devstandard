"""Exercise native Codex install/discovery/removal without changing existing configuration."""
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys, tempfile, tomllib

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

before_markets = cli('marketplace','list')
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
                assert after_config == before_config, 'user config changed semantically; inspect only probe entry before cleanup'
                assert cli('marketplace','list') == before_markets, 'original marketplace registry changed'
                print('CLEANUP: existing user configuration and marketplaces unchanged', flush=True)
    print('PASS: installed/discovered/cached/removed; existing user configuration and marketplaces unchanged')
