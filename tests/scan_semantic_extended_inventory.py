"""Root CI-only offline Grype scan of the supplemental public Syft document."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import review_semantic_image_vulnerabilities as reviewer
from tools import prepare_semantic_image_sbom as sbom

parser = argparse.ArgumentParser()
parser.add_argument('--sbom', type=Path, required=True)
args = parser.parse_args()
assert os.geteuid() == 0
root = Path('/root/ouf-ci-vulnerability')
pin = reviewer.database_pin(sbom.decode((root / 'database-pin.json').read_bytes()))
scanner = root / 'grype'
sbom.executable(scanner, '4de6935c80c111d3d37b2b09f86d1a30b3d10a2f7146d4dbe74ed86c81f35790')
reviewer.hash_file(root / 'database.tar.zst', pin['checksum'][7:], 1073741824)
home = root / ('extended-scan-' + args.sbom.stem)
home.mkdir(mode=0o700)
env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'HOME': str(home),
       'XDG_CONFIG_HOME': str(home), 'GRYPE_CHECK_FOR_APP_UPDATE': 'false',
       'GRYPE_DB_AUTO_UPDATE': 'false', 'GRYPE_DB_CACHE_DIR': str(home / 'database'),
       'GRYPE_DB_VALIDATE_BY_HASH_ON_START': 'true', 'GRYPE_DB_VALIDATE_AGE': 'true',
       'GRYPE_DB_MAX_ALLOWED_BUILT_AGE': '48h', 'GRYPE_EXTERNAL_SOURCES_ENABLE': 'false',
       'GRYPE_ONLY_FIXED': 'false', 'GRYPE_ONLY_NOTFIXED': 'false'}
command = ['/usr/bin/unshare', '--net', '--', str(scanner)]
subprocess.run(command + ['db', 'import', str(root / 'database.tar.zst')], env=env,
               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True, timeout=180)
scan = subprocess.run(command + ['sbom:' + str(args.sbom.resolve()), '--quiet', '-o', 'json'],
                      env=env, stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=180)
assert 0 < len(scan.stdout) <= 67108864
report = json.loads(scan.stdout)
assert report['descriptor']['version'] == reviewer.GRYPE_VERSION
db = report['descriptor']['db']['status']
assert db['built'] == pin['built'] and db['schemaVersion'] == pin['schemaVersion'] and db['valid'] is True
assert not db.get('error') and not report.get('ignoredMatches')
reviewer.database_pin(pin)
sys.stdout.buffer.write(scan.stdout)

