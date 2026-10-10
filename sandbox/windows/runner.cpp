#define _WIN32_WINNT 0x0A00
#include <windows.h>
#include <userenv.h>
#include <sddl.h>
#include <aclapi.h>
#include <objbase.h>
#include <algorithm>
#include <atomic>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
namespace fs {
    struct path {
        std::wstring value;
        path(const std::wstring& s):value(s){std::replace(value.begin(),value.end(),L'/',L'\\');}
        const wchar_t* c_str() const{return value.c_str();}
        const std::wstring& wstring() const{return value;}
        path operator/(const wchar_t* tail) const{return path(value+L"\\"+tail);}
    };
    path absolute(const std::wstring& value) {
        wchar_t buffer[32768]; DWORD count=GetFullPathNameW(value.c_str(),32768,buffer,nullptr);
        if(!count||count>=32768) throw std::runtime_error("Invalid sandbox path");
        return path(buffer);
    }
}

// Trusted supervisor. Submitted source/executables are never launched without
// an AppContainer token and a resource-limited, non-breakaway job.
struct Handle {
    HANDLE h = nullptr;
    Handle() = default;
    explicit Handle(HANDLE value): h(value) {}
    ~Handle() { if (h && h != INVALID_HANDLE_VALUE) CloseHandle(h); }
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;
};
void require(bool ok, const char* operation) {
    if (!ok) throw std::runtime_error(std::string(operation)+" failed (Windows "+std::to_string(GetLastError())+")");
}
struct AclLock {
    Handle mutex;
    AclLock():mutex(CreateMutexW(nullptr,FALSE,L"Local\\CspLabJudgeAcl")) {
        require(mutex.h,"Create ACL mutex");
        DWORD result=WaitForSingleObject(mutex.h,30000);
        require(result==WAIT_OBJECT_0||result==WAIT_ABANDONED,"Lock sandbox ACL");
    }
    ~AclLock(){ReleaseMutex(mutex.h);}
};
std::wstring wide(const std::string& value) {
    int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),(int)value.size(),nullptr,0);
    require(n>0,"UTF-8 argument"); std::wstring result(n,0);
    MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),(int)value.size(),result.data(),n);
    return result;
}
std::wstring quote(const std::wstring& s) {
    std::wstring out=L"\""; unsigned slashes=0;
    for (wchar_t c:s) { if (c==L'\\') { ++slashes; continue; }
        out.append(c==L'"' ? slashes*2+1 : slashes,L'\\'); out+=c; slashes=0; }
    out.append(slashes*2,L'\\'); return out+L"\"";
}
void grant(const fs::path& target, PSID sid, DWORD permissions, bool inherit=true) {
    AclLock lock;
    PACL oldAcl=nullptr,newAcl=nullptr; PSECURITY_DESCRIPTOR descriptor=nullptr;
    DWORD error=GetNamedSecurityInfoW(const_cast<wchar_t*>(target.c_str()),SE_FILE_OBJECT,DACL_SECURITY_INFORMATION,
                                    nullptr,nullptr,&oldAcl,nullptr,&descriptor);
    require(error==ERROR_SUCCESS,"Read sandbox ACL");
    EXPLICIT_ACCESSW access{}; access.grfAccessPermissions=permissions; access.grfAccessMode=GRANT_ACCESS;
    access.grfInheritance=inherit ? SUB_CONTAINERS_AND_OBJECTS_INHERIT : NO_INHERITANCE;
    access.Trustee.TrusteeForm=TRUSTEE_IS_SID; access.Trustee.TrusteeType=TRUSTEE_IS_UNKNOWN;
    access.Trustee.ptstrName=static_cast<LPWSTR>(sid);
    error=SetEntriesInAclW(1,&access,oldAcl,&newAcl);
    if (error==ERROR_SUCCESS) error=SetNamedSecurityInfoW(const_cast<wchar_t*>(target.c_str()),SE_FILE_OBJECT,
                                                       DACL_SECURITY_INFORMATION,nullptr,nullptr,newAcl,nullptr);
    if(newAcl) LocalFree(newAcl); if(descriptor) LocalFree(descriptor);
    require(error==ERROR_SUCCESS,"Grant sandbox ACL");
}
void revoke(const fs::path& target,PSID sid) {
    AclLock lock;
    PACL oldAcl=nullptr,newAcl=nullptr; PSECURITY_DESCRIPTOR descriptor=nullptr;
    if(GetNamedSecurityInfoW(const_cast<wchar_t*>(target.c_str()),SE_FILE_OBJECT,DACL_SECURITY_INFORMATION,
        nullptr,nullptr,&oldAcl,nullptr,&descriptor)!=ERROR_SUCCESS) return;
    EXPLICIT_ACCESSW access{}; access.grfAccessMode=REVOKE_ACCESS; access.Trustee.TrusteeForm=TRUSTEE_IS_SID;
    access.Trustee.ptstrName=static_cast<LPWSTR>(sid);
    if(SetEntriesInAclW(1,&access,oldAcl,&newAcl)==ERROR_SUCCESS)
        SetNamedSecurityInfoW(const_cast<wchar_t*>(target.c_str()),SE_FILE_OBJECT,DACL_SECURITY_INFORMATION,nullptr,nullptr,newAcl,nullptr);
    if(newAcl) LocalFree(newAcl); if(descriptor) LocalFree(descriptor);
}
void denyWrites(const fs::path& target,PSID sid) {
    PACL oldAcl=nullptr,newAcl=nullptr; PSECURITY_DESCRIPTOR descriptor=nullptr;
    DWORD error=GetNamedSecurityInfoW(const_cast<wchar_t*>(target.c_str()),SE_FILE_OBJECT,DACL_SECURITY_INFORMATION,nullptr,nullptr,&oldAcl,nullptr,&descriptor);
    if(error!=ERROR_SUCCESS) throw std::runtime_error("Read profile ACL failed");
    EXPLICIT_ACCESSW access{}; access.grfAccessMode=DENY_ACCESS;
    access.grfAccessPermissions=FILE_GENERIC_WRITE|DELETE|FILE_DELETE_CHILD;
    access.grfInheritance=SUB_CONTAINERS_AND_OBJECTS_INHERIT;
    access.Trustee.TrusteeForm=TRUSTEE_IS_SID;access.Trustee.ptstrName=static_cast<LPWSTR>(sid);
    error=SetEntriesInAclW(1,&access,oldAcl,&newAcl);
    if(error==ERROR_SUCCESS) error=SetNamedSecurityInfoW(const_cast<wchar_t*>(target.c_str()),SE_FILE_OBJECT,DACL_SECURITY_INFORMATION,nullptr,nullptr,newAcl,nullptr);
    if(newAcl) LocalFree(newAcl);if(descriptor)LocalFree(descriptor);
    if(error!=ERROR_SUCCESS)throw std::runtime_error("Protect AppContainer profile from disk writes failed");
}
void lowIntegrity(const fs::path& target) {
    PSECURITY_DESCRIPTOR descriptor=nullptr; PACL sacl=nullptr; BOOL present=FALSE,defaulted=FALSE;
    require(ConvertStringSecurityDescriptorToSecurityDescriptorW(L"S:(ML;OICI;NW;;;LW)",SDDL_REVISION_1,&descriptor,nullptr),"Create low integrity label");
    require(GetSecurityDescriptorSacl(descriptor,&present,&sacl,&defaulted),"Read integrity label");
    DWORD error=SetNamedSecurityInfoW(const_cast<wchar_t*>(target.c_str()),SE_FILE_OBJECT,LABEL_SECURITY_INFORMATION,
                                    nullptr,nullptr,nullptr,sacl);
    LocalFree(descriptor);
    if(error!=ERROR_SUCCESS) throw std::runtime_error("Set compiler workspace integrity failed (Windows "+std::to_string(error)+")");
}
struct Profile {
    PSID sid=nullptr; std::wstring name;
    Profile(bool compiler) {
        GUID id{}; require(SUCCEEDED(CoCreateGuid(&id)),"Create profile ID"); wchar_t buf[64];
        StringFromGUID2(id,buf,64); name=compiler?L"csplab.compile.":L"csplab.run.";
        for (wchar_t c:std::wstring(buf)) if(c!=L'{'&&c!=L'}') name+=c;
        HRESULT result=CreateAppContainerProfile(name.c_str(),L"CSP Lab judge",L"Local C++17 sandbox",nullptr,0,&sid);
        if (result==HRESULT_FROM_WIN32(ERROR_ALREADY_EXISTS)) result=DeriveAppContainerSidFromAppContainerName(name.c_str(),&sid);
        require(SUCCEEDED(result),"Create AppContainer");
    }
    ~Profile() {
        if(sid) DeleteAppContainerProfile(name.c_str());
        if(sid) FreeSid(sid);
    }
};
void limits(HANDLE job,unsigned ms,unsigned mb,bool compiler) {
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION settings{};
    settings.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_ACTIVE_PROCESS |
        JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_AFFINITY |
        JOB_OBJECT_LIMIT_JOB_TIME | JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION;
    settings.BasicLimitInformation.ActiveProcessLimit=compiler?16:1;
    settings.BasicLimitInformation.PerJobUserTimeLimit.QuadPart=(LONGLONG)ms*10000;
    DWORD_PTR processMask=0,systemMask=0;
    require(GetProcessAffinityMask(GetCurrentProcess(),&processMask,&systemMask),"CPU affinity");
    // One logical CPU per job, distributed across allowed CPUs. Pinning every
    // compiler and solution to CPU0 creates artificial timeouts under load.
    std::vector<DWORD_PTR> cpus;
    for(unsigned i=0;i<sizeof(DWORD_PTR)*8;++i) if(processMask&(DWORD_PTR(1)<<i)) cpus.push_back(DWORD_PTR(1)<<i);
    // Hybrid laptops have unequal P/E cores. Use the fastest allowed class
    // reported by Windows so equal submissions do not get random time limits.
    ULONG cpuBytes=0;
    GetSystemCpuSetInformation(nullptr,0,&cpuBytes,GetCurrentProcess(),0);
    if(cpuBytes&&cpuBytes<1024*1024) {
        std::vector<unsigned char> topology(cpuBytes);
        if(GetSystemCpuSetInformation(reinterpret_cast<PSYSTEM_CPU_SET_INFORMATION>(topology.data()),cpuBytes,&cpuBytes,GetCurrentProcess(),0)) {
            PROCESSOR_NUMBER current{};GetCurrentProcessorNumberEx(&current);
            std::vector<DWORD_PTR> performance;int bestClass=-1;
            for(size_t offset=0;offset+sizeof(SYSTEM_CPU_SET_INFORMATION)<=cpuBytes;) {
                auto* info=reinterpret_cast<PSYSTEM_CPU_SET_INFORMATION>(topology.data()+offset);
                if(info->Size<sizeof(SYSTEM_CPU_SET_INFORMATION)||offset+info->Size>cpuBytes)break;
                if(info->Type==CpuSetInformation&&info->CpuSet.Group==current.Group&&info->CpuSet.LogicalProcessorIndex<sizeof(DWORD_PTR)*8) {
                    DWORD_PTR bit=DWORD_PTR(1)<<info->CpuSet.LogicalProcessorIndex;
                    if((processMask&bit)&&(!info->CpuSet.Allocated||info->CpuSet.AllocatedToTargetProcess)) {
                        int level=info->CpuSet.EfficiencyClass;
                        if(level>bestClass){performance.clear();bestClass=level;}
                        if(level==bestClass)performance.push_back(bit);
                    }
                }
                offset+=info->Size;
            }
            if(!performance.empty())cpus=performance;
        }
    }
    settings.BasicLimitInformation.Affinity=cpus.at((GetCurrentProcessId()/4)%cpus.size());
    settings.JobMemoryLimit=settings.ProcessMemoryLimit=(SIZE_T)mb*1024*1024;
    require(SetInformationJobObject(job,JobObjectExtendedLimitInformation,&settings,sizeof(settings)),"Set job limits");
    JOBOBJECT_BASIC_UI_RESTRICTIONS ui{}; ui.UIRestrictionsClass=0xff;
    require(SetInformationJobObject(job,JobObjectBasicUIRestrictions,&ui,sizeof(ui)),"Set UI restrictions");
}
void drain(HANDLE pipe,HANDLE file,std::atomic<size_t>& total,size_t cap,std::atomic<bool>& overflow,std::atomic<bool>& ioFailed) {
    char buffer[4096]; DWORD count;
    while(ReadFile(pipe,buffer,sizeof(buffer),&count,nullptr)&&count) {
        size_t before=total.fetch_add(count); if(before+count>cap) overflow=true;
        size_t allowed=before>=cap?0:std::min<size_t>(count,cap-before);
        DWORD written=0;
        if(allowed&&(!WriteFile(file,buffer,(DWORD)allowed,&written,nullptr)||written!=allowed)) ioFailed=true;
    }
}
// Fixed-size compiler workspace; assembler directives must not fill the disk.
unsigned long long workspaceBytes(const fs::path& folder) {
    WIN32_FIND_DATAW entry{};
    HANDLE search=FindFirstFileW((folder/L"*").c_str(),&entry);
    if(search==INVALID_HANDLE_VALUE) return 0;
    unsigned long long bytes=0;
    do {
        if(entry.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT) continue;
        if(entry.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY) {
            if(wcscmp(entry.cFileName,L".")&&wcscmp(entry.cFileName,L"..")) bytes+=workspaceBytes(folder/entry.cFileName);
        } else bytes+=((unsigned long long)entry.nFileSizeHigh<<32)|entry.nFileSizeLow;
    } while(FindNextFileW(search,&entry));
    FindClose(search); return bytes;
}
int supervise(bool compiler,const fs::path& work,const fs::path& toolchain,unsigned ms,unsigned mb,size_t outputCap) {
    Profile profile(compiler);
    // Parent traversal is prepared once. Rewriting the data-root ACL per test
    // needlessly propagates ACLs through thousands of public toolchain files.
    grant(work,profile.sid,compiler?FILE_ALL_ACCESS:(FILE_GENERIC_READ|FILE_GENERIC_EXECUTE));
    if(compiler) lowIntegrity(work);
    Handle job(CreateJobObjectW(nullptr,nullptr)); require(job.h,"Create job"); limits(job.h,ms,mb,compiler);
    Handle completion(CreateIoCompletionPort(INVALID_HANDLE_VALUE,nullptr,0,1)); require(completion.h,"Create completion port");
    JOBOBJECT_ASSOCIATE_COMPLETION_PORT association{}; association.CompletionKey=job.h; association.CompletionPort=completion.h;
    require(SetInformationJobObject(job.h,JobObjectAssociateCompletionPortInformation,&association,sizeof(association)),"Associate job events");
    SECURITY_ATTRIBUTES sa{sizeof(sa),nullptr,TRUE};
    Handle input(CreateFileW((work/L"input").c_str(),GENERIC_READ,FILE_SHARE_READ,&sa,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr));
    require(input.h!=INVALID_HANDLE_VALUE,"Open sandbox input");
    Handle outRead,outWrite,errRead,errWrite;
    require(CreatePipe(&outRead.h,&outWrite.h,&sa,0),"Create stdout pipe");
    require(CreatePipe(&errRead.h,&errWrite.h,&sa,0),"Create stderr pipe");
    require(SetHandleInformation(outRead.h,HANDLE_FLAG_INHERIT,0),"Protect stdout reader");
    require(SetHandleInformation(errRead.h,HANDLE_FLAG_INHERIT,0),"Protect stderr reader");
    SIZE_T size=0; InitializeProcThreadAttributeList(nullptr,2,0,&size);
    std::vector<unsigned char> attributeStorage(size);
    STARTUPINFOEXW startup{}; startup.StartupInfo.cb=sizeof(startup);
    startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
    startup.StartupInfo.hStdInput=input.h; startup.StartupInfo.hStdOutput=outWrite.h; startup.StartupInfo.hStdError=errWrite.h;
    startup.lpAttributeList=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attributeStorage.data());
    require(InitializeProcThreadAttributeList(startup.lpAttributeList,2,0,&size),"Initialize process attributes");
    SECURITY_CAPABILITIES capabilities{}; capabilities.AppContainerSid=profile.sid; // No network/device capabilities.
    HANDLE inherited[]={input.h,outWrite.h,errWrite.h};
    require(UpdateProcThreadAttribute(startup.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,&capabilities,sizeof(capabilities),nullptr,nullptr),"Set AppContainer");
    require(UpdateProcThreadAttribute(startup.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,inherited,sizeof(inherited),nullptr,nullptr),"Restrict inherited handles");
    fs::path executable=compiler?toolchain/L"bin/g++.exe":work/L"main.exe";
    std::wstring command=quote(executable.wstring());
    if(compiler) command+=L" -std=c++17 -O2 -pipe -DONLINE_JUDGE -static -static-libgcc -static-libstdc++ -fmax-errors=20 -I"+
        quote((toolchain/L"include").wstring())+L" main.cpp -o main.exe -lws2_32 -ladvapi32";
    // Do not inherit database passwords, API keys, or the user's PATH.
    wchar_t windowsDir[MAX_PATH]; require(GetWindowsDirectoryW(windowsDir,MAX_PATH)>0,"Windows directory");
    LPWSTR sidString=nullptr,profileFolder=nullptr;
    require(ConvertSidToStringSidW(profile.sid,&sidString),"Format profile SID");
    HRESULT folderResult=GetAppContainerFolderPath(sidString,&profileFolder); LocalFree(sidString);
    require(SUCCEEDED(folderResult),"Resolve AppContainer folder");
    std::wstring profilePath=profileFolder; CoTaskMemFree(profileFolder);
    wchar_t localAppData[32768];
    require(GetEnvironmentVariableW(L"LOCALAPPDATA",localAppData,32768)>0,"Resolve Windows LOCALAPPDATA");
    std::vector<std::wstring> variables={L"PATH="+(compiler?(toolchain/L"bin").wstring()+L";":L"")+windowsDir+L"\\System32",
        L"SystemRoot="+std::wstring(windowsDir),L"windir="+std::wstring(windowsDir),L"TEMP="+work.wstring(),L"TMP="+work.wstring(),
        L"USERPROFILE="+profilePath,L"LOCALAPPDATA="+std::wstring(localAppData),L"APPDATA="+profilePath+L"\\RoamingState"};
    std::sort(variables.begin(),variables.end()); std::wstring environment;
    for(auto& variable:variables) { environment+=variable; environment+=L'\0'; } environment+=L'\0';
    PROCESS_INFORMATION process{};
    BOOL created=CreateProcessW(executable.c_str(),command.data(),nullptr,nullptr,TRUE,
        CREATE_SUSPENDED|CREATE_NO_WINDOW|CREATE_UNICODE_ENVIRONMENT|EXTENDED_STARTUPINFO_PRESENT,
        environment.data(),work.c_str(),&startup.StartupInfo,&process);
    DWORD createError=GetLastError(); DeleteProcThreadAttributeList(startup.lpAttributeList);
    if(!created) { SetLastError(createError); require(false,"Create isolated process"); }
    Handle child(process.hProcess),thread(process.hThread);
    if(!AssignProcessToJobObject(job.h,child.h)) { TerminateProcess(child.h,1); require(false,"Attach process to job"); }
    // Verify the kernel token before any submitted instruction can run.
    Handle token; DWORD isContainer=0,returned=0;
    require(OpenProcessToken(child.h,TOKEN_QUERY,&token.h),"Inspect process token");
    if(!GetTokenInformation(token.h,TokenIsAppContainer,&isContainer,sizeof(isContainer),&returned)||!isContainer) {
        TerminateJobObject(job.h,1); throw std::runtime_error("AppContainer enforcement unavailable"); }
    denyWrites(fs::path(profilePath),profile.sid);
    CloseHandle(outWrite.h); outWrite.h=nullptr; CloseHandle(errWrite.h); errWrite.h=nullptr;
    Handle stdoutFile(CreateFileW((work/L"stdout").c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr));
    Handle stderrFile(CreateFileW((work/L"stderr").c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr));
    require(stdoutFile.h!=INVALID_HANDLE_VALUE&&stderrFile.h!=INVALID_HANDLE_VALUE,"Create output files");
    std::atomic<size_t> outputSize{0}; std::atomic<bool> overflow{false},ioFailed{false};
    std::thread stdoutReader(drain,outRead.h,stdoutFile.h,std::ref(outputSize),outputCap,std::ref(overflow),std::ref(ioFailed));
    std::thread stderrReader(drain,errRead.h,stderrFile.h,std::ref(outputSize),outputCap,std::ref(overflow),std::ref(ioFailed));
    ULONGLONG started=GetTickCount64(); std::string status="OK"; bool memoryHit=false,cpuHit=false;
    if(ResumeThread(thread.h)==(DWORD)-1) {
        TerminateJobObject(job.h,1); stdoutReader.join(); stderrReader.join();
        throw std::runtime_error("Resume isolated process failed");
    }
    auto events=[&]() { DWORD message; ULONG_PTR key; LPOVERLAPPED pid;
        while(GetQueuedCompletionStatus(completion.h,&message,&key,&pid,0)) {
            if(message==JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT||message==JOB_OBJECT_MSG_JOB_MEMORY_LIMIT) memoryHit=true;
            if(message==JOB_OBJECT_MSG_END_OF_JOB_TIME||message==JOB_OBJECT_MSG_END_OF_PROCESS_TIME) cpuHit=true;
        }
    };
    while(true) {
        events();
        if(memoryHit) { status="MLE"; TerminateJobObject(job.h,1); break; }
        if(overflow.load()) { status="OLE"; TerminateJobObject(job.h,1); break; }
        if(compiler&&workspaceBytes(work)>64ULL*1024*1024) { status="OLE"; TerminateJobObject(job.h,1); break; }
        if(cpuHit||GetTickCount64()-started>=ms) { status="TLE"; TerminateJobObject(job.h,1); break; }
        if(WaitForSingleObject(child.h,5)==WAIT_OBJECT_0) break;
    }
    WaitForSingleObject(child.h,5000); events();
    DWORD exitCode=0; GetExitCodeProcess(child.h,&exitCode);
    TerminateJobObject(job.h,1); // Compiler descendants cannot survive their driver.
    stdoutReader.join(); stderrReader.join(); events();
    require(!ioFailed.load(),"Capture program output");
    if(memoryHit) status="MLE"; else if(overflow.load()) status="OLE"; else if(cpuHit) status="TLE";
    else if(status=="OK"&&exitCode!=0) status="RE";
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION info{};
    require(QueryInformationJobObject(job.h,JobObjectExtendedLimitInformation,&info,sizeof(info),nullptr),"Read memory usage");
    std::cout<<"{\"status\":\""<<status<<"\",\"time_ms\":"<<(GetTickCount64()-started)
        <<",\"memory_kb\":"<<(info.PeakJobMemoryUsed/1024)<<",\"exit_code\":"<<exitCode
        <<",\"app_container\":true,\"network_capabilities\":0,\"cpu_affinity\":"<<info.BasicLimitInformation.Affinity<<"}"<<std::endl;
    return 0;
}
int main(int argc,char** argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
    try {
        if(argc==4&&std::string(argv[1])=="prepare") {
            // Only public compiler binaries/headers are readable by app packages.
            // Each compilation still has its own private workspace/package SID.
            unsigned char sidBuffer[SECURITY_MAX_SID_SIZE]; DWORD sidSize=sizeof(sidBuffer);
            require(CreateWellKnownSid(WinBuiltinAnyPackageSid,nullptr,sidBuffer,&sidSize),"Create packages SID");
            fs::path tools=fs::absolute(wide(argv[2]));
            grant(fs::path(tools.wstring().substr(0,tools.wstring().find_last_of(L'\\'))),sidBuffer,FILE_TRAVERSE,false);
            grant(tools,sidBuffer,FILE_GENERIC_READ|FILE_GENERIC_EXECUTE);
            fs::path judge=fs::absolute(wide(argv[3]));
            grant(judge,sidBuffer,FILE_TRAVERSE,false);
            grant(fs::path(judge.wstring().substr(0,judge.wstring().find_last_of(L'\\'))),sidBuffer,FILE_TRAVERSE,false);
            std::cout<<"{\"prepared\":true}"<<std::endl; return 0;
        }
        if(argc!=8) throw std::runtime_error("Expected mode, work, toolchain, milliseconds, memory MB, output bytes, protocol version");
        bool compiler=std::string(argv[1])=="compile";
        if(!compiler&&std::string(argv[1])!="run") throw std::runtime_error("Invalid mode");
        unsigned ms=std::stoul(argv[4]),mb=std::stoul(argv[5]); size_t cap=std::stoull(argv[6]);
        if(ms<1||ms>60000||mb<16||mb>2048||cap<1||cap>64*1024*1024||std::string(argv[7])!="1") throw std::runtime_error("Invalid supervisor limits");
        return supervise(compiler,fs::absolute(wide(argv[2])),fs::absolute(wide(argv[3])),ms,mb,cap);
    } catch(const std::exception& error) { std::cerr<<error.what()<<std::endl; return 2; }
}
