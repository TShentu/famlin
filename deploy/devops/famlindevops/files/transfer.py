"""Bounded, content-addressed upload chunks; enqueue only a verified whole bundle."""
import hashlib
import math
import re
import threading
import uuid
from pathlib import Path

CHUNK = 1024 * 1024
lock = threading.Lock()


def receive(state, checksum, index, count, total, data):
    if (not re.fullmatch(r'[0-9a-f]{64}', checksum) or not 0 < total <= 200_000_000
            or count != math.ceil(total / CHUNK) or not 0 <= index < count
            or len(data) != min(CHUNK, total-index*CHUNK)):
        raise ValueError('Invalid chunk dimensions')
    root = Path(state)/'chunks'/checksum
    root.mkdir(parents=True, exist_ok=True)
    with lock:
        done = root/'complete'
        if done.exists():
            return True
        target = root/str(index)
        if target.exists() and target.read_bytes() != data:
            raise ValueError('Chunk collision')
        target.write_bytes(data)
        if not all((root/str(i)).exists() for i in range(count)):
            return False
        inbox = Path(state)/'inbox'
        inbox.mkdir(exist_ok=True)
        temp = inbox/(uuid.uuid4().hex+'.partial')
        digest = hashlib.sha256()
        try:
            with temp.open('wb') as out:
                for i in range(count):
                    chunk = (root/str(i)).read_bytes()
                    digest.update(chunk)
                    out.write(chunk)
            if digest.hexdigest() != checksum:
                raise ValueError('Complete bundle checksum mismatch')
            temp.replace(temp.with_suffix('.tgz'))
            done.write_text('queued')
            for i in range(count):
                (root/str(i)).unlink()
            return True
        finally:
            temp.unlink(missing_ok=True)
