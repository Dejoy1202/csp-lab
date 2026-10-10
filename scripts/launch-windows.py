"""Start a hidden component with direct log handles; no shell or pipe lifetime dependency."""
import ctypes
from ctypes import wintypes
import datetime
import json
from pathlib import Path
import subprocess
import sys

spec=json.load(sys.stdin)
assert spec['name'] in ('backend','worker','frontend')
runtime=Path(__file__).resolve().parents[1]/'.runtime'
startup=subprocess.STARTUPINFO()
startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW
startup.wShowWindow=0
with (runtime/(spec['name']+'.log')).open('wb') as output, (runtime/(spec['name']+'-error.log')).open('wb') as error:
    child=subprocess.Popen([spec['executable'],*spec['arguments']],cwd=spec['directory'],stdin=subprocess.DEVNULL,stdout=output,stderr=error,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW,startupinfo=startup)
created=wintypes.FILETIME();exited=wintypes.FILETIME();kernel=wintypes.FILETIME();user=wintypes.FILETIME()
get_times=ctypes.windll.kernel32.GetProcessTimes
get_times.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
get_times.restype=wintypes.BOOL
if not get_times(int(child._handle),ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel),ctypes.byref(user)):
    child.kill()
    raise ctypes.WinError()
ticks=(created.dwHighDateTime<<32)|created.dwLowDateTime
seconds,fraction=divmod(ticks,10000000)
utc=datetime.datetime.fromtimestamp(seconds-11644473600,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{fraction:07d}Z'
print(json.dumps({'name':spec['name'],'pid':child.pid,'startedUtc':utc}))
