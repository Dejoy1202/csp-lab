"""Trusted stdin loader for a read-only rootfs with writable /work tmpfs.

Docker's archive API rejects cp into read-only rootfs on some Engine versions.
Streaming known files through exec stdin avoids relaxing the rootfs policy.
"""
import json
import os
import sys

for entry in json.loads(sys.argv[1]):
    name,size,mode=entry
    if name not in ("main.cpp","main","input") or not 0 <= size <= 64*1024*1024:
        raise ValueError("Invalid sandbox file")
    with open("/work/"+name,"wb") as stream:
        remaining=size
        while remaining:
            chunk=sys.stdin.buffer.read(min(65536,remaining))
            if not chunk:raise EOFError("Incomplete upload")
            stream.write(chunk);remaining-=len(chunk)
    os.chmod("/work/"+name,mode)
