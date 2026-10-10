# CSP Lab

> 此目录是 GitHub 源码发布副本。包含前后端、独立判题器、50道已建设题目的题包与验证记录；不包含私人账号数据库、密码配置或本机依赖。上传步骤见 [GITHUB_UPLOAD.md](GITHUB_UPLOAD.md)。新电脑先按 [Windows 部署](docs/WINDOWS.md) 配置；本机日常使用仍通过原有桌面快捷方式启动。

自托管 CCF-CSP 模拟考试平台：账号登录 → 选择历届试卷 → 四小时五题作答 → 独立沙箱判题 → 成绩与代码复盘。当前本机使用 **Windows 本地版，不需要 Docker 或 WSL**：Java 21 / Spring Boot / MySQL 8，React / TypeScript / Vite / 本地 Monaco 与 KaTeX，Python Worker 与 Windows AppContainer / Job Object 判题监督器。代码和数据均保存在你的设备，不调用其他 OJ 判题。

目前目录覆盖 **2013 年至 2026 年 9 月，44 个批次、220 个题号和题名**。已建设并导入 **201312、201403、201409、201412、202403、202509、202512、202603、202605、202609 十套，共 50 题**。其余 34 套仍在建设，无法开启模拟；目录完成不代表题面、参考程序或隐藏测试已经完成。题意独立重述、样例与测试自行构造，成绩为本站模拟评分。来源和核对记录见 [题库来源](problem-packs/SOURCES.md)。

普通界面只保留模拟考试、考试记录和账号设置，管理员另有题库管理。错题本、普通题库列表和训练工作台已取消；已有数据库记录保留。

## 环境要求

Windows 11，JDK 21、Maven、Node.js 22.12+、MySQL 8、Python 3.12+、兼容 AppContainer 的 MinGW-w64。本机已有 Java 21.0.6、Maven 3.9.16、Node 24、MySQL 8.0.28 和 Python 3.12.13；专用工具链已校验并放在 D:\CspLabData\winlibs，原编译器及 PATH 不变。初次配置、软件路径和依赖说明见 [Windows 部署](docs/WINDOWS.md)。

```powershell
java -version
mvn -version
node --version
Get-Service MySQL80
```

## 启动与登录

在项目根目录：

```powershell
# 本机已完成配置；首次在其他电脑运行请先按 docs/WINDOWS.md 配置
.\scripts\start-windows.ps1
```

打开 http://127.0.0.1:5173 。可以直接注册普通账号。管理员用户名为根目录 .env 的 ADMIN_USERNAME（默认 cspadmin），初始密码为 ADMIN_INITIAL_PASSWORD；首次启动写入 BCrypt 哈希，之后修改 .env 不会覆盖已设置的账户密码。登录后点击用户名可修改密码。网页使用 HttpOnly 会话，不需要填写 API_KEY。

配置脚本创建随机密码 .env 和 .env.windows，以及仅有 csp_lab 库权限的本地数据库账户。启动脚本构建 Java、导入仓库中已验证题包并启动三个项目进程；重复导入跳过已验证题目。管理员在本地管理界面导入题包。API_KEY 仅供受信任的题包建设和验收脚本使用，不提供给普通网页。

健康检查：http://127.0.0.1:8080/actuator/health 。Java 后端和 Vite 仅监听回环地址。原 Linux/Docker Compose 方式保留，使用 scripts/start.ps1 或 scripts/start.sh；相关备份操作见 [可选 Docker 部署](docs/DEPLOYMENT.md)。

## 数据库与日常停止

Windows 数据库为本地 MySQL80 服务中的 **csp_lab**，实际文件位于 **C:\ProgramData\MySQL\MySQL Server 8.0\Data**。Flyway 自动顺序执行 backend/src/main/resources/db/migration/V*.sql；新增变更使用新的迁移文件。各用户的草稿、提交和考试按 user_id 隔离。

```powershell
.\scripts\backup-windows.ps1
.\scripts\stop-windows.ps1
.\scripts\start-windows.ps1
# 修改 Java 后重新构建
.\scripts\stop-windows.ps1
.\scripts\start-windows.ps1 -Rebuild
```

停止脚本仅停止本项目进程，保留共享 MySQL 服务和数据。SQL 压缩备份位于项目根目录 backups；数据库与 Docker 的卸载或重装无关。之前未备份的 Docker 个人记录没有恢复，当前50道题由仓库中的已验证题包重新导入。备份与恢复见 [Windows 部署](docs/WINDOWS.md)。

## 题库建设

```powershell
. .\scripts\windows-common.ps1
$config=Get-CspWindowsConfig
Invoke-CspWithEnv $config {
    # 导入已验证题包；普通启动会自动执行
    & $config.PYTHON_EXE problem-packs\build.py --import-existing --output problem-packs\generated
    # 重建时每次编译运行都进入 Windows 沙箱
    & $config.PYTHON_EXE problem-packs\early.py --batch 202509 --output problem-packs\generated --import
    # 普通账户五题满分、部分分、样例不计分及交卷限制
    & $config.PYTHON_EXE problem-packs\verify_exam.py --batches 202509 --output problem-packs\generated
}
```

新批次放在 problem-packs/<batch>/：statements.json、reference/1.cpp 至 5.cpp、data.py（生成器、独立答案校验与输入验证）。early.py 使用相同流程构建：确定性种子 → 验证输入 → 沙箱编译标准程序 → 用标准程序生成答案并与独立算法对拍 → 正式边界测试 → 典型错解检测 → 压缩 JSON 题包及 SHA-256 报告 → 管理接口导入。复杂批次可使用单独构建器，仍输出统一 Problem DTO。

整套题必须提供覆盖第1至5题的 `mutations.json`，每个已知错解必须编译成功，并在正式数据上被判错或触发资源限制；不能把编译失败当作有效数据反例。通用构建器和202403构建器都在错解检查通过后才导出和导入新题包；部分重建只检查所选题目，并单独保存证据，避免覆盖整套验证报告。缺少错解、错解仍通过、重复定义或引用题包目录外源码都会阻止构建。`tests/test_mutation_gate.py` 的8项回归检查已通过，包含失败时旧题包不变且不调用数据库导入。

2026-10-10 专项检查“错误程序是否仍能拿满分”：在原119个错解之外，逐题新增52个针对边界和常见实现错误的程序，发现3处原数据漏测（化学方程式消元换行、数字分组单元素、树题零次操作初始答案）。补入反例并导入数据库后，真实普通账号提交这些错解分别为WA/60、WA/90、WA/95，三份参考程序仍为AC/100。旧正式输入全部保留，历史提交没有改写。详见 [修复及实际提交](docs/validation/leakage-repair.json) 和 [修复前的漏测证据](docs/validation/leakage-hunt-before-repair.json)。

修复后的全库审查覆盖50题、944项正式评分检查及54个样例，735份短输入答案重新通过独立模型校验；本轮171个选定错解均实际执行并被识别，其中30个由两套修复流程重跑，其余141个由全库审查重跑。详见 [全库审查](docs/validation/problem-data-audit.json)；[第一轮119个错解记录](docs/validation/problem-data-audit-first-pass.json)保留为历史证据。本次没有重新生成所有大规模答案；大型答案仍使用既有验证证书，加密大型输入的合法性检查使用记录中的答案解码。有限的错解验证不能保证已穷尽漏测，也不等同官方数据。

题库继续使用本站参考程序、独立答案模型及自建数据。2026-10-10用户决定不购买曙梦OJ数据，因此不再等待站方开通权限，也没有下载或导入该站正式数据。保留的可选下载脚本 `scripts/download-shumeng-data.mjs YYYYMM` 不参与启动或判题，仅供将来合法授权且有下载权限时使用；密码不写入源码，下载也不会自动修改数据库。第三方自建数据不能标注为CCF官方隐藏数据。

201312 保留原始单组输入与数据范围，没有照搬来源 OJ 的增强版本；100 次随机对拍和 50 个正式点。202403 使用 150 次随机对拍和 64 个正式点，后三题支持捆绑子任务评分。201403、201409各有100个正式点、200次小数据对拍和10个典型错解见证；已通过真实账号五题500分交卷。202609 最新一套另完成100个不同正式输入、120项评分检查、200次独立对拍及11个典型错解检测；第4题使用专用构造判题器，组数正确可获40分，任意合法划分均可满分。五题真实提交AC/100并交卷500分，详见 [最新一套验证](problem-packs/202609/VERIFICATION.md)。新增201412有100个正式点、200次小数据独立对拍和12个典型错解检测；覆盖大成交量、矩阵完整输出与周期库存，详见 [2014年12月验证](problem-packs/201412/VERIFICATION.md)。202605第42次另完成100个不同正式点、200次常规对拍、295次完整状态对拍和16个错解检测；五题真实AC/100、交卷500/500，第4/5题捆绑部分分30/60与1024MiB超限MLE通过。详见 [第42次验证](problem-packs/202605/VERIFICATION.md)。202603第41次新增100个不同正式点、200次常规对拍、344项树与维修站组合、20组数位边界及12800项字面递推核对；16个错解均被识别，五题真实交卷500/500。第2题支持绝对误差判题，第4/5题小规模解分别50/30分。详见 [第41次验证](problem-packs/202603/VERIFICATION.md)。202512第40次新增100个不同正式点、200次常规对拍、124项矩阵专项、200项数阵字面枚举及7904项小域多重集染色核对；另80条数据包动态轨迹和50万包/近百万元素的联合上限检查。详见 [第40次验证](problem-packs/202512/VERIFICATION.md)。新增批次必须配置 mutations.json，错解未被识别时构建失败，不写出新题包。Windows参考验证与用户提交每点均使用独立AppContainer；保留的Linux实现使用Docker沙箱。参考验证不能保证覆盖所有错误程序，本站分数不等同官方成绩。数据库保留生成器、参考程序与校验器资产，普通用户不能读取隐藏输入或标准答案。

## 测试与学习

```powershell
cd backend
mvn verify
cd ..\frontend
npm run build
npm run lint
npm run test:e2e
```

浏览器测试使用本机 Edge；Linux 可配置 CSP_BROWSER_PATH 或安装 Playwright Chromium。测试实际调用 Spring Boot、MySQL和Judge Worker，不模拟判题响应；Windows使用AppContainer，Linux使用Docker。原始报告位于 test-results/playwright/，验证结论见 [测试说明](docs/FRONTEND_TESTING.md)。Windows沙箱、API与重启测试见 [Windows部署](docs/WINDOWS.md)；scripts/test.ps1保留给Docker部署。

从 AuthController / SecurityConfig 学习会话、CSRF 和密码哈希；从 SubmissionController → SubmissionService → SubmissionRepository 学习请求、事务和参数化 SQL；再看 worker/worker.py 的任务领取、续租、判题和原子完成。耗时编译运行不占用 Spring 请求线程或长数据库事务。[架构说明](docs/ARCHITECTURE.md) 与 [API 契约](docs/API.md) 说明各层职责。

Windows 本地启动不使用 Docker 代理。原 Compose/Dockerfile 留作可选 Linux 部署；Dockerfile.local 仅供已有运行镜像的离线更新，不用于全新环境。
