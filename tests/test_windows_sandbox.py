"""Real Windows isolation/resource checks; no submitted binary runs outside the sandbox."""
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "worker"))
from sandbox import Sandbox


@unittest.skipUnless(os.name == "nt", "Windows AppContainer integration")
class WindowsSandboxTests(unittest.TestCase):
    evidence = []

    @classmethod
    def setUpClass(cls):
        cls.sandbox = Sandbox(None, "windows-validation")

    def binary(self, source):
        binary, diagnostic = self.sandbox.compile(source)
        self.assertIsNotNone(binary, diagnostic)
        return binary

    def check(self, name, source, expected="OK", time_ms=1000, memory_mb=64, output_kb=64):
        report = self.sandbox.run(self.binary(source), "2 3\n", time_ms, memory_mb, output_kb)
        self.assertEqual(expected, report["status"], report)
        self.assertTrue(report["app_container"])
        self.assertEqual(1,report['cpu_affinity'].bit_count())
        self.evidence.append({"check":name,"status":report["status"],"timeMs":report["time_ms"],"memoryKb":report["memory_kb"]})
        return report

    def test_correct_output(self):
        report=self.check("correct-output", '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b;}')
        self.assertEqual("5", report["stdout"].strip())

    def test_compile_error(self):
        binary, diagnostic=self.sandbox.compile("int main( { broken }")
        self.assertIsNone(binary)
        self.assertTrue(diagnostic)
        self.evidence.append({"check":"compile-error","status":"CE"})

    def test_time_limit(self):
        self.check("infinite-loop", "int main(){for(;;){}}", "TLE", time_ms=200)

    def test_memory_limit(self):
        self.check("memory-limit", '#include <vector>\nint main(){std::vector<char*> v;for(;;){auto p=new char[1024*1024];for(int i=0;i<1024*1024;i+=4096)p[i]=1;v.push_back(p);}}', "MLE")

    def test_memory_failure_even_if_caught(self):
        self.check("caught-allocation-failure", '#include <vector>\n#include <new>\nint main(){std::vector<char*>v;try{for(;;)v.push_back(new char[1024*1024]);}catch(std::bad_alloc&){return 0;}}', "MLE")

    def test_runtime_error(self):
        self.check("access-violation", 'int main(){volatile int*p=nullptr;*p=1;}', "RE")

    def test_output_limit(self):
        self.check("output-limit", '#include <cstdio>\nint main(){for(;;)puts("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");}', "OLE", output_kb=4)

    def test_host_file_and_credentials_are_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            canary=Path(folder)/"csp-canary.txt"
            canary.write_text("private-canary", encoding="utf-8")
            target=json.dumps(str(canary))
            source=f'''#include <windows.h>
#include <iostream>
#include <fstream>
#include <cstdlib>
int main(){{HANDLE token;DWORD value=0,size=0;OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&token);
GetTokenInformation(token,TokenIsAppContainer,&value,sizeof(value),&size);CloseHandle(token);
std::ifstream file({target});std::cout<<value<<" "<<file.good()<<" "<<(getenv("DB_PASSWORD")!=nullptr)<<" "<<(getenv("API_KEY")!=nullptr);}}'''
            report=self.check("file-and-environment-isolation", source)
            self.assertEqual("1 0 0 0", report["stdout"].strip())

    def test_compiler_cannot_read_host_files(self):
        with tempfile.TemporaryDirectory() as folder:
            canary=Path(folder)/"csp-header.h"
            canary.write_text('#define PRIVATE_VALUE "private-canary"\n',encoding="utf-8")
            target=str(canary).replace('\\','/')
            binary,diagnostic=self.sandbox.compile(f'#include "{target}"\nint main(){{}}')
            self.assertIsNone(binary)
            self.assertNotIn('private-canary',diagnostic)
            self.evidence.append({"check":"compiler-file-isolation","status":"DENIED"})

    def test_runtime_workspace_is_read_only(self):
        report=self.check("readonly-workspace", '#include <fstream>\n#include <iostream>\nint main(){std::ofstream file("scratch.txt");std::cout<<file.good();}')
        self.assertEqual("0",report["stdout"].strip())

    def test_compiler_cannot_read_another_judge_workspace(self):
        with tempfile.TemporaryDirectory(dir=self.sandbox.root) as folder:
            canary=Path(folder)/'private.h'
            canary.write_text('#define PRIVATE_VALUE "other-submission-private"\n',encoding='utf-8')
            binary,diagnostic=self.sandbox.compile(f'#include "{canary.as_posix()}"\nint main(){{}}')
            self.assertIsNone(binary)
            self.assertNotIn('other-submission-private',diagnostic)
            self.evidence.append({'check':'separate-compiler-workspaces','status':'DENIED'})

    def test_profile_filesystem_is_read_only(self):
        source=r'''#include <cstdlib>
#include <fstream>
#include <string>
#include <iostream>
int main(){std::ofstream f(std::string(getenv("USERPROFILE"))+"\\LocalState\\forbidden.txt");std::cout<<f.good();}'''
        report=self.check('readonly-profile',source)
        self.assertEqual('0',report['stdout'].strip())

    def test_compiler_disk_limit(self):
        binary,diagnostic=self.sandbox.compile('asm(".section .data\\n.space 100000000\\n"); int main(){}')
        self.assertIsNone(binary)
        self.assertIn('OLE',diagnostic)
        self.evidence.append({'check':'compiler-disk-limit','status':'CE/OLE','limitMb':64})

    def test_network_is_denied(self):
        # A real listening loopback server avoids confusing connection refusal
        # with sandbox denial; no data is sent to an external service.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1",0));listener.listen()
            port=listener.getsockname()[1]
            source=f'''#include <winsock2.h>
#include <iostream>
int main(){{WSADATA data;WSAStartup(MAKEWORD(2,2),&data);SOCKET s=socket(AF_INET,SOCK_STREAM,0);u_long nonblocking=1;ioctlsocket(s,FIONBIO,&nonblocking);
sockaddr_in address{{}};address.sin_family=AF_INET;address.sin_port=htons({port});address.sin_addr.s_addr=inet_addr("127.0.0.1");
int connected=connect(s,(sockaddr*)&address,sizeof(address));fd_set ready;FD_ZERO(&ready);FD_SET(s,&ready);timeval timeout{{0,200000}};
if(connected==SOCKET_ERROR&&select(0,nullptr,&ready,nullptr,&timeout)>0){{sockaddr_in peer{{}};int length=sizeof(peer);connected=getpeername(s,(sockaddr*)&peer,&length);}}
std::cout<<(connected!=0);closesocket(s);WSACleanup();}}'''
            # Winsock is linked by the sandbox compiler for ordinary C++ code.
            report=self.check("network-isolation", source)
            self.assertEqual("1", report["stdout"].strip())
            listener.settimeout(.2)
            with self.assertRaises(socket.timeout):
                connection,_=listener.accept()
                connection.close()

    def test_child_process_is_denied(self):
        source=r'''#include <windows.h>
#include <iostream>
int main(){STARTUPINFOA s{};s.cb=sizeof(s);PROCESS_INFORMATION p{};char cmd[1024];GetWindowsDirectoryA(cmd,800);lstrcatA(cmd,"\\System32\\cmd.exe /c exit 0");
BOOL ok=CreateProcessA(nullptr,cmd,nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,nullptr,&s,&p);std::cout<<ok;
if(ok){CloseHandle(p.hThread);CloseHandle(p.hProcess);}}'''
        report=self.check("process-limit", source)
        self.assertEqual("0",report["stdout"].strip())


if __name__ == "__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(WindowsSandboxTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    output=Path(__file__).resolve().parents[1]/"test-results/windows-sandbox.json"
    output.write_text(json.dumps({"success":result.wasSuccessful(),"checks":WindowsSandboxTests.evidence},ensure_ascii=False,indent=2),encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
