# Windows 本地运行

此方式不需要 Docker Desktop、Docker Engine 或 WSL：React/Vite、Java 21、MySQL 8、Python Judge Worker 均运行在 Windows。提交的 C++17 由独立监督器放入 Windows AppContainer，使用 Job Object 限制资源。原 Compose 方式仍可使用。

## 已检查的本机环境

- Java 21.0.6、Maven 3.9.16、Node.js 24。
- MySQL80 Windows 服务，MySQL 8.0.28，端口 3306。
- Python 3.12.13 位于 D:\miniconda3；项目虚拟环境位于 .runtime\python，不修改 Conda 环境。
- 专用便携 MinGW-w64 工具链放在 D:\CspLabData，不修改系统 PATH 或原有编译器。工具链下载需先获用户许可，脚本固定发行版本并验证官方 SHA-256。

## 初次配置

在项目根目录运行：

```powershell
# 仅在授权下载工具链后执行；下载文件不会自动执行
& 'D:\miniconda3\python.exe' .\scripts\download-windows-toolchain.py

# 配置时在本机安全输入 MySQL root 密码，root 密码不保存
.\scripts\setup-windows.ps1 -CompilerRoot 'D:\CspLabData\winlibs\mingw64'
```

setup-windows.ps1 默认 Python、MySQL 和专用编译器路径适配本机；其他电脑可以指定 Python、MysqlBin、CompilerRoot 和 JudgeDataRoot。下载脚本会先校验再解压 WinLibs GCC16.2.0 / MinGW-w64 14.0.0 UCRT，并准备 Boost1.92.0 头文件及许可证，供202403第3题的大整数参考程序使用。原始 D:\mingw64 的 GCC8.1无法在本机 AppContainer 启动，不作为兼容工具链。链接器对中文命令行路径有限制，因此判题数据与工具链使用 D:\CspLabData 这样的英文路径；项目本身可保留中文目录。

固定下载来源：[WinLibs官方发行](https://github.com/brechtsanders/winlibs_mingw/releases/tag/16.2.0posix-14.0.0-ucrt-r2)、[MSYS2 Boost包](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-boost)。SHA-256写在下载脚本内，校验失败不解压。专用工具链没有写入系统PATH；更换版本后需要重跑沙箱与参考程序兼容测试。

根目录 .env 保留管理员初始密码和内部 API_KEY；.env.windows 保存本地数据库连接与判题配置，两者都在 Git 忽略清单内。后端和 Worker 使用专用 csp_lab_app 账号，只授权 csp_lab 数据库。Flyway 自动初始化业务表，首次创建管理员账户；网页仍采用账号密码登录和 HttpOnly 会话。

## 启动、停止与备份

```powershell
.\scripts\start-windows.ps1
# 修改 Java 后端后重新构建
.\scripts\stop-windows.ps1
.\scripts\start-windows.ps1 -Rebuild

.\scripts\backup-windows.ps1
.\scripts\stop-windows.ps1
```

网页地址：http://127.0.0.1:5173。首次前端安装依赖需在 frontend 执行 npm ci。后台日志在 .runtime；停止脚本按 PID 和进程启动时间核验后只停止本项目进程树，包括Java/Python启动器的实际子进程，不停止 MySQL 服务。scripts/restart-worker-windows.ps1只重启判题Worker，用于更新和恢复测试。

数据库名是 csp_lab，实际数据库文件由现有 MySQL80 服务保管，本机配置为 C:\ProgramData\MySQL\MySQL Server 8.0\Data。SQL 压缩备份在项目根目录 backups，位于普通 Windows 磁盘，不在 Docker 虚拟磁盘中。题包与生成器在 problem-packs。数据库文件本身不适合在服务运行时直接复制；使用 backup-windows.ps1 生成一致的 SQL 备份。

2026-10-10 Docker 重装后，可访问位置未找到旧 CSP Lab 数据库卷或 SQL 备份。重新导入题包可以恢复题目和隐藏测试，不能生成已经丢失的个人账号、提交或考试记录。后续 Windows 数据库的数据与 Docker 卸载无关。

## Windows 判题的差异

Windows 使用 MinGW-w64 g++ 编译 C++17，生成 Windows 可执行文件；Linux 的二进制文件不能复用。数学评分、题包、异步队列和 REST API 保持相同。Windows Job Object 的内存统计是已提交的内存，Linux 原实现主要报告进程 RSS，两者耗时和内存数值不能直接比较；本站评分仍是模拟评分。

编译和每次运行使用不同的AppContainer身份。编译进程可读取公开的专用工具链并写入自己的工作目录，不能读取另一提交的私有目录；运行目录和AppContainer私有目录只读。受限进程不继承数据库密码、API_KEY 或用户 PATH，无网络能力。监督器在进程挂起时绑定不可脱离的 Job Object，核对 AppContainer 令牌后才启动，限制一个逻辑 CPU、进程数量、内存、CPU及墙钟时间和 stdout/stderr 总量。编译固定30秒/1024MiB/16进程，运行使用题目内存和时限/1进程。编译目录64MiB通过轮询检查，可能有短暂超量；运行进程不能创建文件。隔离失败返回基础设施错误，不转为普通宿主进程执行。

判题 Worker 是可信后台程序，持有项目数据库权限；用户代码的隔离由监督器执行，用户代码不在 Java 进程内运行。[微软 AppContainer 说明](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation)和[Job Object 说明](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)解释了所用 Windows 机制。

## 验证

```powershell
# 先读取 .env/.env.windows 的配置（不打印密码）
. .\scripts\windows-common.ps1
$config=Get-CspWindowsConfig
Invoke-CspWithEnv $config {
    & $config.PYTHON_EXE .\tests\test_windows_sandbox.py
    & $config.PYTHON_EXE .\tests\e2e.py
    & $config.PYTHON_EXE .\problem-packs\verify_exam.py --batches 202509 --output problem-packs\generated
}
```

Windows 沙箱的实际测试报告为 test-results/windows-sandbox.json；API和重启验证报告在test-results/windows/。已有 Docker 平台的通过报告不代表 Windows 已通过。迁移验证以新的实际报告为准，汇总见 [Windows验收记录](validation/windows-runtime.json)。

恢复会覆盖csp_lab中的表，应先备份当前数据，停止CSP Lab再运行；脚本会明确要求确认：

```powershell
.\scripts\stop-windows.ps1
.\scripts\restore-windows.ps1 -Backup '.\backups\csp-lab-时间戳.sql.gz'
.\scripts\start-windows.ps1 -SkipImport
```


判题任务优先绑定本机性能等级最高的允许逻辑CPU，每个Job仍限制为一个逻辑CPU。这样避免i5-13500H等混合架构的大小核导致相同代码得到不同的时限结果；没有修改系统电源计划或全局亲和性。等级来自[微软CPU Set字段说明](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-system_cpu_set_information)。Linux专用函数如getchar_unlocked需要改成可移植输入实现；仓库中的参考程序已适配。

旧编译器副本、未完成下载和监督器探针已移到D:\CspLabData\retired，保留可恢复的副本；当前使用的编译器、项目虚拟环境和已校验发行包保留。
