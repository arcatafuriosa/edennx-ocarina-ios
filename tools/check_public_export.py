#!/usr/bin/env python3
"""Check this source-only export without reading game data or contacting a device."""
from pathlib import Path
import re
import sys

BLOCKED_SUFFIXES = {
    '.nsp', '.xci', '.nsz', '.xcz', '.nup', '.nca', '.tik', '.keys', '.sav',
    '.p12', '.p8', '.pem', '.mobileprovision', '.ipa', '.metallib', '.spv',
    '.img', '.bin', '.dll', '.pdb', '.dylib', '.air', '.mov', '.mp4', '.log',
    '.bgyml', '.byml', '.bfsha', '.zs', '.pack',
}
PATTERNS = {
    'absolute personal/workstation path': rb'/(?:Users|Volumes)/[^\s"\'<>]+',
    'Apple device identifier': rb'\b0000[0-9a-fA-F]{4}-[0-9a-fA-F]{16}\b',
    'GitHub credential': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'private key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'personal mailbox': rb'\b[A-Za-z0-9._%+-]+@(?:icloud|gmail|outlook|hotmail)\.[A-Za-z]{2,}\b',
    'binary patch': rb'(?m)^GIT binary patch$',
}


def problems(name, data):
    found = []
    if Path(name).suffix.lower() in BLOCKED_SUFFIXES:
        found.append('disallowed file type')
    if b'\0' in data:
        found.append('binary content')
    if len(data) > 10 * 1024 * 1024:
        found.append('file exceeds source-export size limit')
    for label, pattern in PATTERNS.items():
        if re.search(pattern, data):
            found.append(label)
    return found


def main():
    root = Path(__file__).resolve().parents[1]
    failures, checked = [], 0
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if any(part in {'.git', '.venv', '__pycache__'} for part in rel.parts):
            continue
        if path.is_symlink():
            failures.append((str(rel), 'symlink requires review'))
        elif path.is_file():
            checked += 1
            failures.extend((str(rel), why) for why in problems(str(rel), path.read_bytes()))
    for name, why in failures:
        print(name + ': ' + why)
    print(f'Public export: {checked} files checked, {len(failures)} violations')
    return bool(failures)


if __name__ == '__main__':
    sys.exit(main())
