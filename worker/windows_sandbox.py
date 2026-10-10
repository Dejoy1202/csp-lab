"""Windows 11 AppContainer + Job Object adapter for the existing judge protocol."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile


class WindowsSandbox:
    def __init__(self, image=None, owner="validation"):
        self.owner = owner
        self.root = Path(os.environ.get("WINDOWS_JUDGE_ROOT", "D:/CspLabData/judge")).resolve()
        self.toolchain = Path(os.environ.get("WINDOWS_TOOLCHAIN", "D:/CspLabData/winlibs/mingw64")).resolve()
        default_runner = Path(__file__).resolve().parents[1] / ".runtime/windows-runner.exe"
        self.runner = Path(os.environ.get("WINDOWS_RUNNER", str(default_runner))).resolve()
        if os.name != "nt" or not self.runner.is_file() or not (self.toolchain / "bin/g++.exe").is_file():
            raise RuntimeError("Windows sandbox is not prepared; run scripts/setup-windows.ps1")
        self.root.mkdir(parents=True, exist_ok=True)

    def _execute(self, mode, work, time_ms, memory_mb, output_limit):
        result = subprocess.run(
            [str(self.runner), mode, str(work), str(self.toolchain), str(time_ms), str(memory_mb), str(output_limit), "1"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=time_ms / 1000 + 15, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode:
            raise RuntimeError("Windows sandbox unavailable: " + result.stderr.decode("utf-8", "replace")[:2048])
        report = json.loads(result.stdout)
        if report.get("app_container") is not True or report.get("network_capabilities") != 0:
            raise RuntimeError("AppContainer/network enforcement unavailable")
        stdout = (work / "stdout").read_bytes()
        stderr = (work / "stderr").read_bytes()
        report.update(stdout=stdout.decode("utf-8", "replace"), stderr=stderr.decode("utf-8", "replace"),
                      stdout_b64=base64.b64encode(stdout).decode("ascii"))
        return report

    def compile(self, source):
        with tempfile.TemporaryDirectory(prefix="compile-", dir=self.root) as folder:
            work = Path(folder)
            (work / "main.cpp").write_text(source, encoding="utf-8")
            (work / "input").write_bytes(b"")
            # Recent Boost/GCC templates need more compile-time memory than the
            # executed solution. Runtime limits remain each problem's limits.
            report = self._execute("compile", work, 30000, 1024, 32768)
            diagnostic = report["stderr"]
            if report["status"] != "OK" or not (work / "main.exe").is_file():
                return None, diagnostic or "Compilation exceeded " + report["status"]
            return (work / "main.exe").read_bytes(), diagnostic

    def run(self, binary, input_data, time_ms, memory_mb, output_limit_kb=16384):
        with tempfile.TemporaryDirectory(prefix="run-", dir=self.root) as folder:
            work = Path(folder)
            (work / "main.exe").write_bytes(binary)
            (work / "input").write_bytes(input_data.encode("utf-8"))
            return self._execute("run", work, time_ms, memory_mb, output_limit_kb * 1024)

    def cleanup_owner(self, owner):
        # Each attempt uses a unique temporary directory. The supervisor's
        # KILL_ON_JOB_CLOSE also terminates the child if the worker is interrupted.
        pass
