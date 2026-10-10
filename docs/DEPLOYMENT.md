# 本机部署与备份

当前本机使用 **Windows 本地 MySQL 和 AppContainer 判题**，启动、停止、数据位置及备份恢复见 [Windows 部署](WINDOWS.md)。前端 127.0.0.1:5173，后端 127.0.0.1:8080。下面保留原可选 Docker 部署的操作，当前 Windows 版不需要执行。

## 备份

WSL Ubuntu / Bash：

```bash
mkdir -p backups
docker compose exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysqldump --single-transaction --no-tablespaces -u"$MYSQL_USER" "$MYSQL_DATABASE"' > backups/csp-lab.sql
```

备份含账户哈希、个人代码和隐藏测试数据，保存在自己的设备。恢复到已初始化的空库：

```bash
docker compose exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u"$MYSQL_USER" "$MYSQL_DATABASE"' < backups/csp-lab.sql
```

不要通过改 .env 中 MySQL 密码来修改已经初始化的数据库账户；需要在数据库内执行账户密码变更。

## 已有镜像的离线 Java 更新

Docker Desktop 代理不可用时，已有运行镜像仍可使用。需要宿主 JDK 21 / Maven：

```powershell
cd backend
mvn verify
docker build --network none -f Dockerfile.local -t csp-lab-backend:latest .
cd ..
docker compose up -d --no-build --wait mysql backend worker
```

该方式依赖已有 csp-lab-backend 镜像，不用于全新环境。常规 backend/Dockerfile 是多阶段 JDK 构建方案。第一次构建要确保 Docker 使用的代理/网络可以访问所选镜像仓库。

## 发布前端

npm run build 输出 frontend/dist；可交给 Nginx 并将 /api 代理到 backend:8080。会话采用同源 Cookie，公开 HTTPS 部署须启用 Secure Cookie 和匹配的代理配置。当前版本定位本机自托管，判题 Worker 持有 Docker daemon 管理权限；公网部署还需要专用判题宿主及资源策略。
