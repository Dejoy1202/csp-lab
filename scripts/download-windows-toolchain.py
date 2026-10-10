"""Pinned official WinLibs portable toolchain; resumable downloads with SHA-256."""
import concurrent.futures
import hashlib
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request

URL="https://github.com/brechtsanders/winlibs_mingw/releases/download/16.2.0posix-14.0.0-ucrt-r2/winlibs-x86_64-posix-seh-gcc-16.2.0-mingw-w64ucrt-14.0.0-r2.7z"
SHA256="53fb6773fbdf87cdf22b69a6b2a07ee33d3ada413b42d83044bc7cc6481400d2"
SIZE=109762824
CHUNK=4*1024*1024
ROOT=Path("D:/CspLabData")
PARTS=ROOT/"download-parts"
BOOST_URL="https://mirror.msys2.org/mingw/ucrt64/mingw-w64-ucrt-x86_64-boost-1.92.0-4-any.pkg.tar.zst"
BOOST_SHA256="2f9935335e17f9930cba7e93a8db95bf699df2dd1c250cffe6dce89c7ea70154"

def checksum(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file,'sha256').hexdigest()

def prepare_headers():
    archive=ROOT/'boost-1.92.0.pkg.tar.zst'
    if not archive.exists() or checksum(archive)!=BOOST_SHA256:
        temporary=archive.with_suffix('.part')
        with urllib.request.urlopen(BOOST_URL,timeout=45) as response, temporary.open('wb') as output:
            shutil.copyfileobj(response,output)
        if checksum(temporary)!=BOOST_SHA256:raise RuntimeError('Boost checksum mismatch; do not extract')
        temporary.replace(archive)
    destination=ROOT/'winlibs/mingw64/include/boost'
    if not (destination/'multiprecision/cpp_int.hpp').is_file():
        staging=ROOT/'boost-package'
        staging.mkdir(exist_ok=True)
        subprocess.run(['tar.exe','-xf',str(archive),'-C',str(staging),'ucrt64/include/boost','ucrt64/share/licenses/boost'],check=True)
        shutil.copytree(staging/'ucrt64/include/boost',destination,dirs_exist_ok=True)
    licenses=ROOT/'winlibs/licenses/boost'
    if not licenses.exists():
        staging=ROOT/'boost-package'
        staging.mkdir(exist_ok=True)
        subprocess.run(['tar.exe','-xf',str(archive),'-C',str(staging),'ucrt64/share/licenses/boost'],check=True)
        shutil.copytree(staging/'ucrt64/share/licenses/boost',licenses,dirs_exist_ok=True)
    print('Verified Boost 1.92.0 headers prepared for the existing big-integer reference program.',flush=True)

def download(index):
    begin=index*CHUNK
    end=min(SIZE-1,begin+CHUNK-1)
    complete=PARTS/f"{index}.done"
    partial=PARTS/f"{index}.part"
    if complete.exists() and complete.stat().st_size==end-begin+1:return
    for attempt in range(4):
        have=partial.stat().st_size if partial.exists() else 0
        if have==end-begin+1:partial.replace(complete);return
        if have>end-begin+1:raise RuntimeError("Invalid existing download part")
        request=urllib.request.Request(URL,headers={"Range":f"bytes={begin+have}-{end}"})
        try:
            with urllib.request.urlopen(request,timeout=45) as response:
                if response.status!=206 or response.headers.get('Content-Range')!=f"bytes {begin+have}-{end}/{SIZE}":
                    raise RuntimeError("Server did not honor download range")
                with partial.open("ab") as output:
                    while data:=response.read(65536):output.write(data)
            if partial.stat().st_size==end-begin+1:partial.replace(complete);return
        except Exception:
            if attempt==3:raise
            time.sleep(1)
    raise RuntimeError("Incomplete toolchain part")

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    target=ROOT/"winlibs-verified.7z"
    if target.exists() and checksum(target)==SHA256:
        print('Using the already verified portable toolchain archive.',flush=True)
    else:
        download_archive(target)
    tools=ROOT/'winlibs'
    if not (tools/'mingw64/bin/g++.exe').is_file():
        tools.mkdir(exist_ok=True)
        subprocess.run(['tar.exe','-xf',str(target),'-C',str(tools)],check=True)
    prepare_headers()
    print(f'CompilerRoot: {tools / "mingw64"}',flush=True)

def download_archive(target):
    PARTS.mkdir(parents=True,exist_ok=True)
    count=(SIZE+CHUNK-1)//CHUNK
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures=[executor.submit(download,index) for index in range(count)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
            done=sum(p.stat().st_size for p in PARTS.glob('*.done'))
            print(f"Toolchain download: {done*100//SIZE}%",flush=True)
    digest=hashlib.sha256()
    with target.open('wb') as output:
        for index in range(count):
            with (PARTS/f'{index}.done').open('rb') as part:
                while data:=part.read(65536):digest.update(data);output.write(data)
    if digest.hexdigest()!=SHA256:raise RuntimeError("Toolchain checksum mismatch; do not extract")
    print(f"Verified {target}: SHA-256 {SHA256}",flush=True)

if __name__=='__main__':main()
