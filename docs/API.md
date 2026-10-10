# CSP Lab API 契约

基址 /api，JSON 字段使用 camelCase，UTF-8。网页通过同源 Vite 代理访问 8080。浏览器账号鉴权使用 HttpOnly JSESSIONID，会话有效期 8 小时。仅 /actuator/health 和 /api/auth/csrf、login、register 允许匿名访问。

## 账号

| 请求 | 参数 / 响应 |
| --- | --- |
| GET /auth/csrf | 返回 token、headerName，创建或读取当前会话的 CSRF token |
| POST /auth/register | username、password；201，注册普通 USER 并登录 |
| POST /auth/login | username、password；200，返回 id、username、displayName、role |
| GET /auth/me | 当前账号，不含密码哈希 |
| POST /auth/logout | 204，销毁会话 |
| POST /auth/password | previousPassword、newPassword；204，旧会话全部失效，需重新登录 |

所有浏览器写请求带 X-CSRF-TOKEN，登录后重新获取 token。用户名 3–32 位字母、数字或下划线，统一小写；密码至少 8 位且 UTF-8 不超过 72 字节。密码使用 BCrypt cost 12。连续失败 10 次后，账号限流 15 分钟。注册不能选择管理员角色。

## 试卷与考试

| 请求 | 响应 / 参数 |
| --- | --- |
| GET /papers | 按批次降序：sourceBatch、sourceYear、examNumber、examDate、problems、verifiedCount、ready |
| GET /papers/{batch} | batch、problems（id、code、title、sourcePosition、建设状态）、ready、durationSeconds=14400、maxScore=500 |
| POST /exams | 普通用户传 {batch:"202403"}；服务器选取同批次的五题、验证建设状态，创建四小时考试 |
| GET /exams | 当前用户的考试列表（startedAt、status、totalScore 等） |
| GET /exams/{id} | 当前用户的考试、remainingSeconds、serverNow、problems 和 totalScore |
| POST /exams/{id}/finish | 交卷，返回最新考试详情 |

每个账户只允许一场进行中的考试。BUILDING、题目缺失或不满足 FULL + VERIFIED 时拒绝创建。管理工具兼容 title / problemIds 自定义验收组卷；普通用户只能选 CSP 批次。其他用户的考试返回404。

## 代码与判题

| 请求 | 参数 / 响应 |
| --- | --- |
| GET /problems/{id} | 当前公开题面，含 samples / scoring / subtasks，不含隐藏输入与答案 |
| GET /problems/{id}/versions/{version} | 固定版本题面；考试使用此接口 |
| GET /problems/{id}/draft | 当前用户 sourceCode、revision |
| PUT /problems/{id}/draft | sourceCode、revision；版本冲突409，成功返回新 revision |
| POST /runs | problemId、sourceCode、language:"CPP17"、examId；202，返回任务 id |
| POST /submissions | 同上，正式评测；202，返回任务 id |
| GET /submissions/{id} | 当前用户代码、状态、score、compileOutput、results、subtasks |
| GET /submissions | 按 problemId、examId、status、page、size 分页；仅当前用户 |

普通用户提交必须绑定自己的未结束考试。编译与执行全部在独立 Docker 沙箱，异步任务 QUEUED → RUNNING → 终态。终态 AC、WA、CE、TLE、MLE、RE、OLE、SYSTEM_ERROR。SAMPLE 不计分，只返回公开样例上用户的截断输出；JUDGE 不返回隐藏输入、标准输出或隐藏点用户输出。捆绑子任务的分数不与测试点分数重复累加。成绩标识 SITE_SIMULATION。

## 管理

/api/admin/** 仅 ADMIN 可访问。保留新增、更新、批量、JSON / gzip 题包导入和资产读取接口。Problem DTO 的字段和验证约束以 backend/src/main/java/dev/csplab/dto/Requests.java 为准。每题最多100项评分检查；相同输入的组数/构造检查分别计数，捆绑子任务与独立点的总分仍为100。内存限制memoryLimitMb为32–1024MiB，API和数据库均拒绝越界。POST /api/admin/problems/import-pack接受JSON或gzip的file字段，压缩文件上限64MiB、multipart请求上限65MiB、解压后上限128MiB；重复题号返回409，批量失败回滚。完整建设题须提供合法题意、范围、评分、参考/生成/验证资产及报告；活动考试或任务使用中的题不可编辑。题包脚本采用 X-API-Key 内部凭据，浏览器不使用或存储该凭据。

样例和正式测试点都可带可选字段checkerType，省略或null时为TOKENS。允许值仅为TOKENS、FLOAT_ABS_1E_3、CSP_GROUP_COUNT、CSP_GROUP_PARTITION：FLOAT_ABS_1E_3用于202603第2题，一个有限数值且绝对误差严格小于0.001；普通小数与科学计数法均可，NaN/Infinity/多余token/过长数值拒绝。后两种用于202609第4题的组数及合法划分检查，不接收任意可执行判题代码。样例一般使用完整划分检查，正式点可按子任务分别配组数与构造分。公开接口不会因为使用专用判题而暴露隐藏输入或答案。

错题本、训练首页和练习会话接口已经取消；数据库旧记录保留。
