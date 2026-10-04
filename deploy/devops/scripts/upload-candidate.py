#!/usr/bin/env python3
"""Retry bounded chunks in parallel across high-latency publisher connections."""
import concurrent.futures
import hashlib
import os
import sys
import time
import urllib.request
from pathlib import Path


def upload(path, endpoint, token):
    payload = Path(path).read_bytes()
    checksum = hashlib.sha256(payload).hexdigest()
    size = 1024*1024
    count = (len(payload)+size-1)//size
    def send(index):
        data = payload[index*size:(index+1)*size]
        for attempt in range(4):
            try:
                request = urllib.request.Request(endpoint, data=data, method='POST', headers={
                    'Authorization': 'Bearer '+token, 'Content-Type': 'application/octet-stream',
                    'X-Content-SHA256': checksum, 'X-Chunk-Index': str(index),
                    'X-Chunk-Count': str(count), 'X-Total-Size': str(len(payload))})
                with urllib.request.urlopen(request, timeout=180) as response:
                    response.read()
                print(f'Uploaded chunk {index+1}/{count}', flush=True)
                return
            except Exception:
                if attempt == 3:
                    raise RuntimeError(f'Chunk {index+1} could not be uploaded') from None
                time.sleep(2**attempt)
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(send, range(count)))
    print('All chunks uploaded; publisher verifies whole-bundle SHA-256.', flush=True)


if __name__ == '__main__':
    upload(sys.argv[1], 'https://08c91481.hzfystt.olares.cn/candidates', os.environ['DEPLOY_TOKEN'])
