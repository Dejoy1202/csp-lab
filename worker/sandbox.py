import json
import os
import uuid
import time

LABEL = "dev.csplab.sandbox"

def tokens(data):
    # Byte-level token comparison: whitespace is ignored, invalid UTF-8 is not
    # replaced before comparing to an ASCII/UTF-8 expected answer.
    return data.split()

class Sandbox:
    def __new__(cls, image, owner="validation"):
        if os.name == "nt":
            from windows_sandbox import WindowsSandbox
            return WindowsSandbox(image, owner)
        return super().__new__(cls)

    def __init__(self, image, owner="validation"):
        import docker
        self.docker = docker
        self.client = docker.from_env(timeout=60)
        self.image = self.client.images.get(image).id  # Resolve once, prevent tag races.
        self.owner = owner
        info = self.client.info()
        if info.get("CgroupVersion") != "2" or not info.get("MemoryLimit") or not info.get("PidsLimit"):
            raise RuntimeError("Cgroup v2, memory and PID limits are required")
        if not any("seccomp" in option for option in info.get("SecurityOptions", [])):
            raise RuntimeError("Docker seccomp support is required")

    def upload(self,container,files):
        manifest=[[name,len(data),mode] for name,(data,mode) in files.items()]
        execution=self.client.api.exec_create(container.id,["python","/sandbox/load.py",json.dumps(manifest)],stdin=True,stdout=False,stderr=False)["Id"]
        channel=self.client.api.exec_start(execution,socket=True)
        try:
            channel._sock.settimeout(60)
            for data,_ in files.values():channel._sock.sendall(data)
            deadline=time.monotonic()+60
            while time.monotonic()<deadline:
                state=self.client.api.exec_inspect(execution)
                if not state["Running"]:
                    if state["ExitCode"]!=0:raise RuntimeError("Sandbox upload failed")
                    return
                time.sleep(.02)
            raise TimeoutError("Sandbox upload timeout")
        finally:
            channel.close()

    def container(self, compile_mode, memory_mb):
        return self.client.containers.create(
            self.image, ["sleep", "600"], name="csp-sandbox-" + uuid.uuid4().hex,
            network_disabled=True, network_mode="none", read_only=True,
            cap_drop=["ALL"], cap_add=[] if compile_mode else ["SETUID", "SETGID", "KILL"],
            security_opt=["no-new-privileges:true"], user="65534:65534" if compile_mode else "0:0",
            mem_limit=memory_mb * 1024 * 1024, memswap_limit=memory_mb * 1024 * 1024,
            nano_cpus=1_000_000_000, pids_limit=32 if compile_mode else 16,
            ulimits=[self.docker.types.Ulimit(name="nofile", soft=64, hard=64),
                     self.docker.types.Ulimit(name="core", soft=0, hard=0)],
            tmpfs={"/work": "rw,noexec,nosuid,nodev,size=64m,mode=1777" if compile_mode else "rw,exec,nosuid,nodev,size=96m,mode=755",
                   "/tmp": "rw,noexec,nosuid,nodev,size=16m,mode=1777"},
            init=True, labels={LABEL: "true", "dev.csplab.owner": self.owner},
            log_config=self.docker.types.LogConfig(type="none"),
        )

    def compile(self, source):
        container = self.container(True, 512)
        try:
            container.start()
            self.upload(container,{"main.cpp": (source.encode("utf-8"), 0o444)})
            result = container.exec_run(["python", "/sandbox/compile.py"])
            if result.exit_code != 0:
                return None, "Compiler container exceeded resource limits"
            report = json.loads(result.output)
            if not report["success"]:
                return None, report["diagnostic"]
            result=container.exec_run(["cat","/work/main"])
            if result.exit_code!=0:raise RuntimeError("Compiled artifact could not be read")
            return result.output, report["diagnostic"]
        finally:
            container.remove(force=True)

    def run(self, binary, input_data, time_ms, memory_mb, output_limit_kb=16384):
        container = self.container(False, memory_mb)
        try:
            container.start()
            self.upload(container,{"main": (binary, 0o555),"input": (input_data.encode("utf-8"), 0o444)})
            result = container.exec_run(["python", "/sandbox/run.py", str(time_ms), str(output_limit_kb * 1024)])
            if result.exit_code != 0:
                container.reload()
                if container.attrs["State"].get("OOMKilled"):
                    return {"status": "MLE", "time_ms": 0, "memory_kb": memory_mb * 1024, "stdout": "", "stderr": ""}
                raise RuntimeError("Runtime supervisor failed")
            return json.loads(result.output)
        finally:
            container.remove(force=True)

    def cleanup_owner(self, owner):
        for container in self.client.containers.list(all=True, filters={"label": [LABEL+"=true", "dev.csplab.owner="+owner]}):
            container.remove(force=True)
