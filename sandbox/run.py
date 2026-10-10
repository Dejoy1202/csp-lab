"""Trusted runtime supervisor. Submitted programs run as UID/GID 65534.

The supervisor runs as root with only SETUID, SETGID and KILL capabilities.
The child has no capabilities, cannot signal/modify the supervisor and receives
neither database credentials nor expected output. Each test uses a fresh container.
"""
import ctypes
import base64
import errno
import json
import math
import os
import resource
import selectors
import signal
import subprocess
import sys
import time

LIMIT_MS = int(sys.argv[1])
OUTPUT_LIMIT = int(sys.argv[2])
lib = ctypes.CDLL("libseccomp.so.2", use_errno=True)
lib.seccomp_init.argtypes = [ctypes.c_uint32]
lib.seccomp_init.restype = ctypes.c_void_p
lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
lib.seccomp_load.argtypes = [ctypes.c_void_p]
lib.seccomp_release.argtypes = [ctypes.c_void_p]

def child_setup():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_LIMIT, OUTPUT_LIMIT))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(LIMIT_MS / 1000) + 1,) * 2)
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
    # Deny process/thread creation and network access after the supervisor forks.
    ctx = lib.seccomp_init(0x7FFF0000)  # SCMP_ACT_ALLOW
    if not ctx:
        os._exit(125)
    for name in ("clone", "clone3", "fork", "vfork", "socket", "socketpair", "ptrace",
                 "mount", "umount2", "unshare", "setns", "bpf", "keyctl", "userfaultfd"):
        number = lib.seccomp_syscall_resolve_name(name.encode("ascii"))
        if number >= 0 and lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, number, 0) != 0:
            os._exit(125)
    if lib.seccomp_load(ctx) != 0:
        os._exit(125)
    lib.seccomp_release(ctx)

def oom_kills():
    try:
        with open("/sys/fs/cgroup/memory.events", encoding="ascii") as stream:
            return int(dict(line.split() for line in stream)["oom_kill"])
    except (OSError, KeyError):
        return None

before_oom = oom_kills()
start = time.monotonic()
buffers = {"stdout": bytearray(), "stderr": bytearray()}
status = "OK"
with open("/work/input", "rb") as input_file:
    proc = subprocess.Popen(["/work/main"], stdin=input_file, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, cwd="/tmp", env={"LANG": "C.UTF-8"},
                            preexec_fn=child_setup, start_new_session=True)
    selector = selectors.DefaultSelector()
    for channel, stream in (("stdout", proc.stdout), ("stderr", proc.stderr)):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, channel)
    total = 0
    while selector.get_map():
        if (time.monotonic() - start) * 1000 > LIMIT_MS:
            status = "TLE"
            break
        for key, _ in selector.select(timeout=0.005):
            chunk = os.read(key.fileobj.fileno(), 16384)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            total += len(chunk)
            if total > OUTPUT_LIMIT:
                status = "OLE"
                break
            buffers[key.data].extend(chunk)
        if status != "OK":
            break
    if status != "OK":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=max(0.01, LIMIT_MS / 1000 - (time.monotonic() - start)))
    except subprocess.TimeoutExpired:
        status = "TLE"
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    selector.close()
    after_oom = oom_kills()
    if before_oom is None or after_oom is None:
        status = "SYSTEM_ERROR"  # Fail closed; do not guess MLE from exit 137.
    elif after_oom > before_oom:
        status = "MLE"
    elif status == "OK" and proc.returncode != 0:
        status = "SYSTEM_ERROR" if proc.returncode == 125 else "RE"
    elapsed = int((time.monotonic() - start) * 1000)
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    print(json.dumps({"status": status, "time_ms": elapsed, "memory_kb": usage.ru_maxrss,
                      "exit_code": proc.returncode,
                      "stdout_b64": base64.b64encode(buffers["stdout"]).decode("ascii"),
                      "stdout": buffers["stdout"].decode("utf-8", "replace"),
                      "stderr": buffers["stderr"].decode("utf-8", "replace")}, ensure_ascii=True))
