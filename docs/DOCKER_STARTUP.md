# 本机 Docker Desktop 启动问题

2026-10-09，本机 Docker Desktop 出现 AF_UNIX 残留套接字错误，日志指向 Docker/run/dockerInference 或 docker-secrets-engine/engine.sock。修复后 docker info 已能正常返回 Engine 29.6.2，CSP Lab 的 MySQL、Spring Boot 与 Judge Worker 均已恢复。

本轮只备份并重建运行目录，未删除 WSL 虚拟磁盘、Docker 数据卷或数据库。Docker Desktop 位于本机的用户安装目录：

C:\Users\Hp\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe

同类错误有 Docker 官方仓库的用户报告：[问题625](https://github.com/docker/desktop-feedback/issues/625)、[问题531](https://github.com/docker/desktop-feedback/issues/531)。这是针对这次启动故障的处理办法，尚不能保证后续 Windows / Docker 更新不会再次触发。

## 相同故障再次出现时

仅在日志仍明确指向这两个残留套接字、且 Engine 无法启动时，用本人 PowerShell 运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Users\Hp\Documents\ChatGPT\计算机视觉\csp-lab\scripts\repair-docker-runtime.ps1"
```

脚本先检测 Engine，正常运行时拒绝修复；它只关闭匹配本机 Docker 安装路径的 Desktop/backend 进程，将两个运行目录改名备份，再隐藏启动 Desktop。Codex 执行账户没有写入 secrets 目录的权限时，须由本机用户执行，不能绕过权限或重置系统配置。

恢复后执行：

```powershell
docker info
docker compose up -d --wait mysql backend worker
```

## 重装与备份

本次已经恢复，无须重装。若日后确实需要卸载，请先按 README 导出数据库并妥善保存文件。[Docker 官方卸载说明](https://docs.docker.com/desktop/uninstall/)提示卸载会破坏本地容器、镜像和卷；恢复出厂设置、删除 WSL 磁盘或 down -v 都不能代替上述运行目录修复。

Docker Desktop 的 Builds 页会显示其他项目之前的构建记录。判断本项目状态应执行 docker compose ps 并查看 backend/worker 日志；截图里的 evaluator/runner 构建记录对应另一仓库。
