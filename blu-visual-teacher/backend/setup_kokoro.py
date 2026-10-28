#!/usr/bin/env python3
"""Download and verify the local Kokoro v1.0 int8 model and voice pack once.

Uses only the Python standard library. Run from the backend directory with
``python setup_kokoro.py`` while connected to the internet; after setup the
speech engine does not need the network.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0'
ASSETS = (
    ('kokoro-v1.0.int8.onnx', f'{BASE}/kokoro-v1.0.int8.onnx',
     '6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb'),
    ('kokoro-voices.bin', f'{BASE}/voices-v1.0.bin',
     'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'),
)


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def download_verified(url: str, destination: Path, expected_sha256: str) -> None:
    if destination.is_file() and checksum(destination) == expected_sha256:
        print(f'Already verified: {destination.name}', flush=True)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + '.part')
    print(f'Downloading {destination.name}...', flush=True)
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Blu-Visual-Teacher-Setup/1.0'})
        h = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(request, timeout=90) as response, partial.open('wb') as output:
            while block := response.read(1024 * 1024):
                output.write(block)
                h.update(block)
                size += len(block)
                print(f'  {size / (1024 * 1024):.1f} MiB', end='\r', flush=True)
        print()
        if h.hexdigest() != expected_sha256:
            raise ValueError(f'SHA-256 verification failed for {destination.name}; no unverified file was installed.')
        partial.replace(destination)
        print(f'Verified and saved: {destination}', flush=True)
    finally:
        partial.unlink(missing_ok=True)


def main() -> int:
    try:
        for filename, url, sha256 in ASSETS:
            download_verified(url, ROOT / 'models' / filename, sha256)
    except Exception as exc:
        print(f'Kokoro setup failed: {exc}', file=sys.stderr)
        print('Check your internet connection and free disk space, then run this command again.', file=sys.stderr)
        return 1
    print('Kokoro files are ready. Restart the FastAPI backend to use them.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
