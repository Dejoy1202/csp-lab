# 上传 CSP Lab 到 GitHub

这是独立的源码发布副本。原工程、当前运行的网站和本地 MySQL 数据库没有移动或修改。

## 已整理的内容

- `backend/`：Java 21、Spring Boot、Flyway 数据库迁移。
- `frontend/`：React、TypeScript、Vite、Monaco 和 KaTeX，包含依赖锁文件。
- `worker/`、`sandbox/`：异步判题及 Windows/Linux 隔离实现。
- `problem-packs/`：题库目录、参考程序、生成器、校验器和50道完整CSP题包，包含最新三处漏测修复。
- `scripts/`、`tests/`、`docs/`：部署、备份和测试代码，架构/API说明及验证记录。
- `.env.example`、`.env.windows.example`、`compose.yaml`：配置示例和可选Docker部署。

实际 `.env`、`.env.windows`、数据库备份、浏览器登录状态、`.runtime`、`node_modules`、Java构建产物和临时结果没有复制。已按本机配置中的密码和密钥扫描发布文件（包含解压后的题包），未发现这些配置值；50个题包与原工程逐文件哈希一致。

总大小约227 MiB，最大单文件约44.8 MiB。两个题包超过GitHub网页上传的25 MiB限制，请使用Git上传；全部文件低于50 MiB，当前无需Git LFS。依据：[GitHub大文件说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)。

## 上传步骤

1. 在GitHub创建一个空仓库，例如 `csp-lab`。不要预先勾选生成README、.gitignore或许可证，以免与本地首次提交冲突。
2. 在这个文件夹中打开PowerShell。目录已初始化为独立Git仓库，尚未创建提交或连接远程仓库。
3. 执行以下命令。将邮箱、用户名和仓库地址改为自己的信息；只设置这个仓库的提交身份。

```powershell
git config user.name "你的GitHub用户名"
git config user.email "你的GitHub提交邮箱"
git branch -M main
git add .
git commit -m "Initial import of CSP Lab"
git remote add origin https://github.com/你的用户名/csp-lab.git
git push -u origin main
```

Git如果打开登录窗口，在窗口中登录GitHub即可，不要把密码写入上述命令。创建仓库后复制它显示的HTTPS地址，替换 `git remote add origin` 中的示例地址。

上传前可以运行 `git status --short` 查看提交内容。配置密码的文件已被 `.gitignore` 排除，但不要使用 `git add -f` 强制添加它们。

## 后续更新和运行

这个目录是整理时的副本，原工程之后的修改不会自动同步到这里。更新时复制相应源码、说明及已验证题包，再执行 `git add .`、`git commit -m "描述本次修改"`、`git push`。

GitHub保存源码与自建题包，不保存你的私人账号、提交代码和模拟考试成绩数据库。个人记录仍在本地MySQL，使用原工程的 `scripts/backup-windows.ps1` 单独备份。

新电脑部署请先安装README中的运行依赖，在 `frontend/` 执行 `npm ci`，再按 `docs/WINDOWS.md` 指定自己的Python、MySQL、编译器和判题目录。初始化脚本生成新配置，Flyway创建数据库表，并导入题包；示例环境文件不是可直接使用的个人密码配置。

当前原机的快捷方式仍指向原工程，请继续使用原来的“CSP Lab”桌面文件夹启动和停止网站。
