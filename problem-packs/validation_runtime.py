"""Fast offline validation of repository-authored reference/mutant programs.

A paper-builder container is reused only for our known local programs. Each input
starts a fresh restricted child via the production supervisor. Official user
submissions still use Sandbox.run: a fresh container for every test point.
No expected answers, credentials or host directories are mounted into the runner.
"""
import json
import os

class ValidationRuntime:
    def __init__(self, sandbox, binary, time_ms, memory_mb, output_limit_kb=1024):
        self.sandbox=sandbox
        self.time_ms=time_ms
        self.memory_mb=memory_mb
        self.binary=binary
        self.output_limit=output_limit_kb*1024
        if os.name=='nt':
            self.container=None
            return
        self.container=sandbox.container(False,memory_mb)
        self.input_exists=False
        try:
            self.container.start()
            sandbox.upload(self.container,{"main":(binary,0o555)})
        except BaseException:
            self.container.remove(force=True)
            raise

    def run(self, data):
        if self.container is None:
            return self.sandbox.run(self.binary,data,self.time_ms,self.memory_mb,self.output_limit//1024)
        if self.input_exists:
            result=self.container.exec_run(["chmod","600","/work/input"])
            if result.exit_code!=0:
                raise RuntimeError("Validation input replacement failed")
        self.sandbox.upload(self.container,{"input":(data.encode("utf-8"),0o444)})
        self.input_exists=True
        result=self.container.exec_run(["python","/sandbox/run.py",str(self.time_ms),str(self.output_limit)])
        if result.exit_code!=0:
            raise RuntimeError("Reference validation supervisor failed")
        report=json.loads(result.output)
        if report["status"] in ("MLE","SYSTEM_ERROR"):
            raise RuntimeError("Repository program broke the validation sandbox: "+report["status"])
        return report

    def close(self):
        if self.container is not None:self.container.remove(force=True)

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.close()
