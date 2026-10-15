"""Read-only verification of the deployed snapshot and frontend against Git."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
FILES = ('data/latest.json', 'index.html', 'script.js', 'style.css', 'publicity.html', 'publicity-article.html', 'publicity.js', 'publicity.css', 'publicity-config.js')


def compare(expected, actual, name=''):
    if name == 'index.html':
        # The Seoul clock is replaced by script.js at runtime. Builders in UTC
        # and Seoul can render different fallback dates for the same source.
        pattern = rb'(<div class="hero-meta" id="heroSeoulClock">).*?(</div>)'
        expected = re.sub(pattern, rb'\1CLOCK\2', expected, flags=re.S)
        actual = re.sub(pattern, rb'\1CLOCK\2', actual, flags=re.S)
    return expected == actual


def verify(origin):
    records = []
    for name in FILES:
        expected = (ROOT / 'site' / name).read_bytes()
        result = subprocess.run(
            ['curl', '--fail', '--silent', '--show-error', '--location',
             '--connect-timeout', '5', '--max-time', '10',
             '--header', 'Cache-Control: no-cache', origin.rstrip('/') + ('/' if name == 'index.html' else '/' + name)],
            capture_output=True, check=False)
        item = {'path': name, 'expected_sha256': hashlib.sha256(expected).hexdigest(),
                'comparison': 'clock-normalized' if name == 'index.html' else 'exact',
                'ok': result.returncode == 0 and compare(expected, result.stdout, name)}
        if result.returncode:
            item['error'] = result.stderr.decode(errors='replace')[:500]
        else:
            item['actual_sha256'] = hashlib.sha256(result.stdout).hexdigest()
        records.append(item)
    return {'ok': all(x['ok'] for x in records), 'origin': origin, 'files': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', default='https://bridgebrand.co.kr')
    parser.add_argument('--attempts', type=int, default=1)
    parser.add_argument('--delay', type=int, default=30)
    args = parser.parse_args()
    if args.attempts < 1 or args.delay < 0:
        parser.error('attempts must be positive and delay nonnegative')
    for attempt in range(args.attempts):
        report = verify(args.origin)
        report['attempt'] = attempt + 1
        print(json.dumps(report, ensure_ascii=False), flush=True)
        if report['ok']:
            return 0
        if attempt + 1 < args.attempts:
            time.sleep(args.delay)
    return 1


if __name__ == '__main__':
    sys.exit(main())
