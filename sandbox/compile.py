"""Trusted compiler driver. Invoked only inside a restricted Docker container."""
import json
import os
import resource
import subprocess
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))
with tempfile.TemporaryFile(dir="/work") as diagnostic:
    try:
        result = subprocess.run(
            ["g++", "-std=c++17", "-O2", "-pipe", "-DONLINE_JUDGE", "/work/main.cpp", "-o", "/work/main"],
            stdout=diagnostic, stderr=diagnostic, timeout=25, cwd="/work",
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "TMPDIR": "/work"},
        )
        diagnostic.seek(0)
        text = diagnostic.read(32768).decode("utf-8", "replace")
        success = result.returncode == 0 and os.path.isfile("/work/main")
        if success:
            os.chmod("/work/main", 0o555)
        print(json.dumps({"success": success, "diagnostic": text}, ensure_ascii=True))
    except subprocess.TimeoutExpired:
        print(json.dumps({"success": False, "diagnostic": "Compilation exceeded the 25-second limit"}))
