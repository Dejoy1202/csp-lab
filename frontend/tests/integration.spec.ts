import {
  test,
  expect,
  request,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { randomBytes } from "node:crypto";
const env = readFileSync("../.env", "utf8");
const key = env.match(/^API_KEY=(.+)$/m)![1].trim();
const password = randomBytes(18).toString("base64url");
const stamp = Date.now().toString(36);
let counter = 0;
let tool: APIRequestContext;
let paper: { problems: { id: number; code: string }[] };
const clients: APIRequestContext[] = [];
const evidence: {
  test: string;
  submissionId: number;
  status: string;
  score: number;
}[] = [];
async function token(ctx: APIRequestContext) {
  return (await (await ctx.get("/api/auth/csrf")).json()).token;
}
async function post(ctx: APIRequestContext, path: string, data?: unknown) {
  return ctx.post(path, {
    headers: { "X-CSRF-TOKEN": await token(ctx) },
    data,
  });
}
async function put(ctx: APIRequestContext, path: string, data: unknown) {
  return ctx.put(path, { headers: { "X-CSRF-TOKEN": await token(ctx) }, data });
}
async function user() {
  const ctx = await request.newContext({ baseURL: "http://127.0.0.1:8080" });
  clients.push(ctx);
  const username = "qa_" + stamp + "_" + ++counter;
  const r = await post(ctx, "/api/auth/register", { username, password });
  expect(r.status()).toBe(201);
  return { ctx, username, account: await r.json() };
}
async function start(ctx: APIRequestContext, batch = "201312") {
  const r = await post(ctx, "/api/exams", { batch });
  expect(r.status(), await r.text()).toBe(201);
  return r.json();
}
async function result(ctx: APIRequestContext, id: number) {
  let last: any;
  await expect
    .poll(
      async () => {
        last = await (await ctx.get("/api/submissions/" + id)).json();
        return last.status;
      },
      { timeout: 90000, intervals: [500, 1000, 1500] },
    )
    .not.toMatch(/QUEUED|RUNNING/);
  return last;
}
async function submit(
  ctx: APIRequestContext,
  exam: any,
  source: string,
  index = 0,
  sample = false,
) {
  const r = await post(ctx, sample ? "/api/runs" : "/api/submissions", {
    problemId: exam.problems[index].problemId,
    examId: exam.id,
    language: "CPP17",
    sourceCode: source,
  });
  expect(r.status()).toBe(202);
  return result(ctx, (await r.json()).id);
}
const reference = (i: number, batch = "201312") =>
  readFileSync(
    "../problem-packs/" + batch + "/reference/" + i + ".cpp",
    "utf8",
  );
async function login(page: Page, username: string, pw = password) {
  await page.goto("/login");
  await page.getByLabel("用户名", { exact: true }).fill(username);
  await page.getByLabel("密码", { exact: true }).fill(pw);
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "历届模拟考试" }),
  ).toBeVisible();
}
async function writeCode(page: Page, source: string) {
  await expect(
    page.getByRole("button", { name: "提交此题", exact: true }),
  ).toBeEnabled();
  await page
    .locator(".monaco-editor")
    .first()
    .click({ position: { x: 170, y: 42 } });
  await page.keyboard.press("Control+A");
  await page.evaluate((s) => navigator.clipboard.writeText(s), source);
  await page.keyboard.press("Control+V");
}
test.beforeAll(async () => {
  tool = await request.newContext({
    baseURL: "http://127.0.0.1:8080",
    extraHTTPHeaders: { "X-API-Key": key },
  });
  paper = await (await tool.get("/api/papers/201312")).json();
  expect(paper.problems).toHaveLength(5);
});
test.afterEach(async () => {
  for (const ctx of clients) {
    const r = await ctx.get("/api/exams");
    if (r.ok())
      for (const e of await r.json())
        if (e.status === "RUNNING")
          await post(ctx, "/api/exams/" + e.id + "/finish");
  }
});
test.afterAll(async () => {
  mkdirSync("../test-results", { recursive: true });
  if(evidence.length) writeFileSync(
    "../test-results/mock-redesign-judge.json",
    JSON.stringify(evidence, null, 2),
  );
  for (const ctx of clients) await ctx.dispose();
  await tool.dispose();
});

test("匿名访问、CSRF、注册登录和普通用户权限", async () => {
  const anon = await request.newContext({ baseURL: "http://127.0.0.1:8080" });
  expect((await anon.get("/api/papers")).status()).toBe(401);
  expect(
    (
      await anon.post("/api/auth/register", {
        data: { username: "blocked", password },
      })
    ).status(),
  ).toBe(403);
  await anon.dispose();
  const { ctx, username, account } = await user();
  expect(account.role).toBe("USER");
  expect((await ctx.get("/api/auth/me")).status()).toBe(200);
  expect((await post(ctx, "/api/admin/problems", {})).status()).toBe(403);
  expect(
    (
      await post(ctx, "/api/auth/register", {
        username: username.toUpperCase(),
        password,
      })
    ).status(),
  ).toBe(409);
  const state = await ctx.storageState();
  expect(state.cookies.find((c) => c.name === "JSESSIONID")?.httpOnly).toBe(
    true,
  );
  expect(state.cookies.find((c) => c.name === "JSESSIONID")?.sameSite).toBe(
    "Lax",
  );
  await post(ctx, "/api/auth/logout");
  expect((await ctx.get("/api/auth/me")).status()).toBe(401);
  expect(
    (
      await post(ctx, "/api/auth/login", {
        username,
        password: "wrong_password",
      })
    ).status(),
  ).toBe(401);
  expect(
    (await post(ctx, "/api/auth/login", { username, password })).status(),
  ).toBe(200);
  expect((await ctx.get("/api/notes")).status()).toBe(404);
  expect((await ctx.get("/api/dashboard")).status()).toBe(404);
});

test("登录轮换会话ID，修改密码使所有旧会话失效", async () => {
  const { ctx, username } = await user();
  const other = await request.newContext({ baseURL: "http://127.0.0.1:8080" });
  clients.push(other);
  await token(other);
  const old = (await other.storageState()).cookies.find(
    (c) => c.name === "JSESSIONID",
  )?.value;
  await post(other, "/api/auth/login", { username, password });
  expect(
    (await other.storageState()).cookies.find((c) => c.name === "JSESSIONID")
      ?.value,
  ).not.toBe(old);
  const next = randomBytes(16).toString("base64url");
  expect(
    (
      await post(ctx, "/api/auth/password", {
        previousPassword: password,
        newPassword: next,
      })
    ).status(),
  ).toBe(204);
  expect((await other.get("/api/auth/me")).status()).toBe(401);
  expect(
    (await post(ctx, "/api/auth/login", { username, password })).status(),
  ).toBe(401);
  expect(
    (await post(ctx, "/api/auth/login", { username, password: next })).status(),
  ).toBe(200);
});

test("44个批次、220道题名；建设中的试卷不能创建考试", async () => {
  const { ctx } = await user();
  const list = await (await ctx.get("/api/papers")).json();
  expect(list).toHaveLength(44);
  expect(list.flatMap((p: any) => p.problems)).toHaveLength(220);
  expect(
    list
      .flatMap((p: any) => p.problems)
      .every((p: any) => !p.title.includes("待核对")),
  ).toBe(true);
  expect(list[0].sourceBatch).toBe("202609");
  expect(list[0].examNumber).toBe(43);
  expect(
    list
      .filter((p: any) => p.ready)
      .map((p: any) => p.sourceBatch)
      .sort(),
  ).toEqual(["201312", "201403", "201409", "201412", "202403", "202509", "202512", "202603", "202605", "202609"]);
  const building = list.find((p: any) => !p.ready);
  expect(building).toBeTruthy();
  expect((await post(ctx, "/api/exams", { batch: building.sourceBatch })).status()).toBe(
    400,
  );
  expect((await post(ctx, "/api/exams", { batch: "209901" })).status()).toBe(
    404,
  );
});

test("不同账号草稿、提交、考试隔离及并发考试限制", async () => {
  const a = await user(),
    b = await user();
  const pid = paper.problems[0].id;
  expect(
    (
      await put(a.ctx, "/api/problems/" + pid + "/draft", {
        sourceCode: "// account A private code",
        revision: 0,
      })
    ).status(),
  ).toBe(200);
  expect(
    (
      await put(a.ctx, "/api/problems/" + pid + "/draft", {
        sourceCode: "// updated",
        revision: 1,
      })
    ).status(),
  ).toBe(200);
  expect(
    (
      await put(a.ctx, "/api/problems/" + pid + "/draft", {
        sourceCode: "// stale",
        revision: 1,
      })
    ).status(),
  ).toBe(409);
  expect(
    (await (await b.ctx.get("/api/problems/" + pid + "/draft")).json())
      .sourceCode,
  ).toBe("");
  const exam = await start(a.ctx);
  expect((await post(a.ctx, "/api/exams", { batch: "201312" })).status()).toBe(
    409,
  );
  expect((await b.ctx.get("/api/exams/" + exam.id)).status()).toBe(404);
  expect((await start(b.ctx)).id).not.toBe(exam.id);
  const judged = await submit(a.ctx, exam, reference(1));
  expect(judged.status).toBe("AC");
  expect((await b.ctx.get("/api/submissions/" + judged.id)).status()).toBe(404);
  expect((await (await b.ctx.get("/api/submissions")).json()).total).toBe(0);
  expect(
    (
      await a.ctx.put("/api/problems/" + pid + "/draft", {
        data: { sourceCode: "attack", revision: 2 },
      })
    ).status(),
  ).toBe(403);
  expect(
    (
      await post(a.ctx, "/api/submissions", {
        problemId: pid,
        language: "CPP17",
        sourceCode: reference(1),
      })
    ).status(),
  ).toBe(400);
});

for (const [status, source, score] of [
  ["AC", reference(1), 100],
  ["WA", "#include <iostream>\nint main(){std::cout<<0;}\n", 0],
  ["CE", "int main( { broken", 0],
  ["TLE", "int main(){for(;;){}}\n", 0],
  [
    "MLE",
    "#include <cstdlib>\n#include <cstring>\nint main(){for(;;){auto p=(volatile char*)malloc(8*1024*1024);if(!p)continue;for(int i=0;i<8*1024*1024;i+=4096)p[i]=1;}}\n",
    0,
  ],
  ["RE", "int main(){return 1;}\n", 0],
  [
    "WA",
    "#include <iostream>\nint main(){int n,x;std::cin>>n>>x;if(n==1)std::cout<<x;else std::cout<<0;}\n",
    20,
  ],
] as const)
  test("真实Docker判题 " + status + " " + score + "分", async () => {
    const { ctx } = await user();
    const exam = await start(ctx);
    const r = await submit(ctx, exam, source);
    expect(r.status).toBe(status);
    expect(r.score).toBe(score);
    if (status === "CE") expect(r.compileOutput).toBeTruthy();
    if (status !== "CE") expect(r.results).toHaveLength(10);
    expect(r.results.every((c: any) => c.stdout == null)).toBe(true);
    evidence.push({
      test: status + " " + score,
      submissionId: r.id,
      status: r.status,
      score: r.score,
    });
  });

test("两套完整模拟考试：五题各100，总分500及交卷后的提交限制", async () => {
  for (const batch of ["201312", "202403"]) {
    const { ctx } = await user();
    const exam = await start(ctx, batch);
    expect(exam.durationSeconds).toBe(14400);
    expect(exam.remainingSeconds).toBeGreaterThan(14390);
    for (let i = 0; i < 5; i++) {
      const r = await submit(ctx, exam, reference(i + 1, batch), i);
      expect(r.status).toBe("AC");
      expect(r.score).toBe(100);
      evidence.push({
        test: batch + " T" + (i + 1),
        submissionId: r.id,
        status: r.status,
        score: r.score,
      });
    }
    const done = await post(ctx, "/api/exams/" + exam.id + "/finish");
    expect(done.status()).toBe(200);
    expect((await done.json()).totalScore).toBe(500);
    expect(
      (
        await post(ctx, "/api/submissions", {
          problemId: exam.problems[0].problemId,
          examId: exam.id,
          language: "CPP17",
          sourceCode: reference(1, batch),
        })
      ).status(),
    ).toBe(409);
  }
});

test("浏览器注册、登录、历史筛选与旧入口移除", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "创建账号", exact: true }).click();
  const username = "ui_" + stamp + "_" + ++counter;
  await page.getByLabel("用户名", { exact: true }).fill(username);
  await page.getByLabel("密码", { exact: true }).fill(password);
  await page.getByLabel("确认密码", { exact: true }).fill(password);
  await page.getByRole("button", { name: "注册并进入" }).click();
  await expect(
    page.getByRole("heading", { name: "历届模拟考试" }),
  ).toBeVisible();
  await expect(page.locator(".paper-row")).toHaveCount(44);
  expect(await page.locator("nav").innerText()).not.toMatch(
    /工作台|错题|题库列表|题库管理/,
  );
  expect(
    await page.evaluate(() => localStorage.getItem("csp-lab-api-key")),
  ).toBeNull();
  await page.getByLabel("年份", { exact: true }).selectOption("2013");
  await expect(page.locator(".paper-row")).toHaveCount(1);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "历届模拟考试" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "退出", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  await login(page, username);
  await page.goto("/admin");
  await expect(page).toHaveURL("/");
});

test("浏览器作答：本地公式、自动保存、样例、正式提交与成绩复盘", async ({
  page,
}) => {
  const { ctx, username } = await user();
  await login(page, username);
  await page.getByLabel("年份", { exact: true }).selectOption("2024");
  const row = page.locator(".paper-row").filter({ hasText: "第 33 次 CSP" });
  await row.getByRole("button", { name: "开始模拟" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "确认开始" })
    .click();
  await expect(page).toHaveURL(/exam\/\d+/);
  const examId = Number(page.url().split("/").pop());
  await expect(page.locator(".statement-body .katex")).not.toHaveCount(0);
  await expect(
    page.locator(".statement-body .katex .msupsub").first(),
  ).toBeVisible();
  await expect(page.locator('.statement-body annotation').filter({hasText:'\\le'})).not.toHaveCount(0);
  await page.getByLabel("题面字号").selectOption("18");
  await expect(page.locator(".statement-body")).toHaveCSS("font-size", "18px");
  await writeCode(page, reference(1, "202403"));
  await expect
    .poll(async () => {
      const p = await (await ctx.get("/api/exams/" + examId)).json();
      return (
        await (
          await ctx.get("/api/problems/" + p.problems[0].problemId + "/draft")
        ).json()
      ).sourceCode.replace(/\r\n/g, "\n");
    })
    .toBe(reference(1, "202403").replace(/\r\n/g, "\n"));
  await page.reload();
  await expect(
    page.getByRole("button", { name: "提交此题", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "运行样例", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText(
    "样例测试，不计分",
  );
  expect(
    (await (await ctx.get("/api/exams/" + examId)).json()).totalScore,
  ).toBe(0);
  await page.getByRole("button", { name: "提交此题", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText("100 / 100 分");
  await page.getByRole("button", { name: "查看本次结果" }).click();
  await expect(page.getByRole("dialog", { name: /提交详情/ })).toContainText(
    "测试点测评结果",
  );
  await page.getByRole("dialog").getByRole("button", { name: /关闭/ }).click();
  await page.getByRole("button", { name: "交卷结算" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "确认交卷" })
    .click();
  await expect(page.locator(".score-num")).toHaveText("100");
  await expect(
    page.getByRole("button", { name: "查看代码与测试点" }),
  ).toHaveCount(2);
  await page.getByRole("link", { name: "考试记录", exact: true }).click();
  await expect(page.getByRole("heading", { name: "考试记录" })).toBeVisible();
});

test("浏览器切换账号不恢复其他人的待保存草稿", async ({ page }) => {
  const a = await user(),
    b = await user();
  const examA = await start(a.ctx),
    examB = await start(b.ctx);
  await login(page, a.username);
  await page.goto("/exam/" + examA.id);
  await writeCode(page, "// Only account A\nint main(){}");
  await page.getByRole("button", { name: "退出", exact: true }).click();
  await login(page, b.username);
  await page.goto("/exam/" + examB.id);
  await expect(
    page.getByRole("button", { name: "提交此题", exact: true }),
  ).toBeEnabled();
  expect(await page.locator(".monaco-editor").innerText()).not.toContain(
    "Only account A",
  );
});


test("最新43次试卷：五题公式、样例与构造判题在网页可用", async ({ page }) => {
  const { ctx, username } = await user();
  await login(page, username);
  const row = page.locator(".paper-row").filter({ hasText: "第 43 次 CSP" });
  await row.getByRole("button", { name: "开始模拟" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认开始" }).click();
  await expect(page).toHaveURL(/exam\/\d+/);
  const examId = Number(page.url().split("/").pop());
  const titles = ["流程规划（其一）", "流程规划（其二）", "轮转调度", "数字分组", "奇"];
  await expect(page.getByRole("tab")).toHaveCount(5);
  for (let i = 0; i < titles.length; ++i) {
    await page.getByRole("tab").nth(i).click();
    await expect(page.locator(".statement-head h2")).toHaveText((i + 1) + ". " + titles[i]);
    await expect(page.locator(".statement-body .katex")).not.toHaveCount(0);
    await expect(page.locator(".statement-body .katex-error")).toHaveCount(0);
    await expect(page.locator(".statement-body")).toContainText("数据范围");
    await expect(page.locator(".statement-body")).toContainText("本站评分规则");
    await expect(page.locator(".sample-card")).toHaveCount(1);
  }
  await page.getByRole("tab").nth(3).click();
  await expect(page.locator(".statement-head h2")).toContainText("数字分组");
  await writeCode(page, reference(4, "202609"));
  await page.getByRole("button", { name: "运行样例", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText("样例测试，不计分");
  await expect(page.locator(".result-summary")).toContainText("通过");
  expect((await (await ctx.get("/api/exams/" + examId)).json()).totalScore).toBe(0);
  await page.getByRole("button", { name: "交卷结算" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认交卷" }).click();
  await expect(page.locator(".score-num")).toHaveText("0");
});


test("201412试卷：五题题面、公式和样例在网页可用", async ({ page }) => {
  const { ctx, username } = await user();
  await login(page, username);
  await page.getByLabel("年份", { exact: true }).selectOption("2014");
  const row = page.locator(".paper-row").filter({ hasText: "第 3 次 CSP" });
  await row.getByRole("button", { name: "开始模拟" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认开始" }).click();
  await expect(page).toHaveURL(/exam\/\d+/);
  const examId = Number(page.url().split("/").pop());
  const titles = ["门禁系统", "Z字形扫描", "集合竞价", "最优灌溉", "货物调度"];
  await expect(page.getByRole("tab")).toHaveCount(5);
  for (let i = 0; i < titles.length; ++i) {
    await page.getByRole("tab").nth(i).click();
    await expect(page.locator(".statement-head h2")).toHaveText((i + 1) + ". " + titles[i]);
    await expect(page.locator(".statement-body .katex")).not.toHaveCount(0);
    await expect(page.locator(".statement-body .katex-error")).toHaveCount(0);
    await expect(page.locator(".statement-body")).toContainText("数据范围");
    await expect(page.locator(".sample-card")).toHaveCount(1);
  }
  await writeCode(page, reference(5, "201412"));
  await page.getByRole("button", { name: "运行样例", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText("样例测试，不计分");
  await expect(page.locator(".result-summary")).toContainText("通过");
  expect((await (await ctx.get("/api/exams/" + examId)).json()).totalScore).toBe(0);
  await page.getByRole("button", { name: "交卷结算" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认交卷" }).click();
  await expect(page.locator(".score-num")).toHaveText("0");
});

test("202605试卷：五题题面、公式和样例在网页可用", async ({ page }) => {
  const { ctx, username } = await user();
  await login(page, username);
  await page.getByLabel("年份", { exact: true }).selectOption("2026");
  const row = page.locator(".paper-row").filter({ hasText: "第 42 次 CSP" });
  await row.getByRole("button", { name: "开始模拟" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认开始" }).click();
  await expect(page).toHaveURL(/exam\/\d+/);
  const examId = Number(page.url().split("/").pop());
  const titles = ["银行家舍入", "机器人宿管指南", "死锁优化", "石子游戏", "绝世好串"];
  await expect(page.getByRole("tab")).toHaveCount(5);
  for (let i = 0; i < titles.length; ++i) {
    await page.getByRole("tab").nth(i).click();
    await expect(page.locator(".statement-head h2")).toHaveText((i + 1) + ". " + titles[i]);
    await expect(page.locator(".statement-body .katex")).not.toHaveCount(0);
    await expect(page.locator(".statement-body .katex-error")).toHaveCount(0);
    await expect(page.locator(".statement-body")).toContainText("数据范围");
    await expect(page.locator(".sample-card")).toHaveCount(1);
  }
  await writeCode(page, reference(5, "202605"));
  await page.getByRole("button", { name: "运行样例", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText("样例测试，不计分");
  await expect(page.locator(".result-summary")).toContainText("通过");
  expect((await (await ctx.get("/api/exams/" + examId)).json()).totalScore).toBe(0);
  await page.getByRole("button", { name: "交卷结算" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认交卷" }).click();
  await expect(page.locator(".score-num")).toHaveText("0");
});

test("202603试卷：五题题面、公式和样例在网页可用", async ({ page }) => {
  const { ctx, username } = await user();
  await login(page, username);
  await page.getByLabel("年份", { exact: true }).selectOption("2026");
  const row = page.locator(".paper-row").filter({ hasText: "第 41 次 CSP" });
  await row.getByRole("button", { name: "开始模拟" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认开始" }).click();
  await expect(page).toHaveURL(/exam\/\d+/);
  const examId = Number(page.url().split("/").pop());
  const titles = ["平衡数", "机器人项目管理", "进程通信", "异或", "旅游计划 - Easy Ver."];
  await expect(page.getByRole("tab")).toHaveCount(5);
  for (let i = 0; i < titles.length; ++i) {
    await page.getByRole("tab").nth(i).click();
    await expect(page.locator(".statement-head h2")).toHaveText((i + 1) + ". " + titles[i]);
    await expect(page.locator(".statement-body .katex")).not.toHaveCount(0);
    await expect(page.locator(".statement-body .katex-error")).toHaveCount(0);
    await expect(page.locator(".statement-body")).toContainText("数据范围");
    await expect(page.locator(".sample-card")).toHaveCount(1);
  }
  await writeCode(page, reference(5, "202603"));
  await page.getByRole("button", { name: "运行样例", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText("样例测试，不计分");
  await expect(page.locator(".result-summary")).toContainText("通过");
  expect((await (await ctx.get("/api/exams/" + examId)).json()).totalScore).toBe(0);
  await page.getByRole("button", { name: "交卷结算" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认交卷" }).click();
  await expect(page.locator(".score-num")).toHaveText("0");
});

test("202512试卷：五题题面、公式和样例在网页可用", async ({ page }) => {
  const { ctx, username } = await user();
  await login(page, username);
  await page.getByLabel("年份", { exact: true }).selectOption("2025");
  const row = page.locator(".paper-row").filter({ hasText: "第 40 次 CSP" });
  await row.getByRole("button", { name: "开始模拟" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认开始" }).click();
  await expect(page).toHaveURL(/exam\/\d+/);
  const examId = Number(page.url().split("/").pop());
  const titles = ["集合", "数字变换", "图片解码", "C 形阵", "数据抢修"];
  await expect(page.getByRole("tab")).toHaveCount(5);
  for (let i = 0; i < titles.length; ++i) {
    await page.getByRole("tab").nth(i).click();
    await expect(page.locator(".statement-head h2")).toHaveText((i + 1) + ". " + titles[i]);
    await expect(page.locator(".statement-body .katex")).not.toHaveCount(0);
    await expect(page.locator(".statement-body .katex-error")).toHaveCount(0);
    await expect(page.locator(".statement-body")).toContainText("数据范围");
    await expect(page.locator(".sample-card")).toHaveCount(1);
  }
  await writeCode(page, reference(5, "202512"));
  await page.getByRole("button", { name: "运行样例", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText("样例测试，不计分", { timeout: 90000 });
  await expect(page.locator(".result-summary")).toContainText("通过");
  expect((await (await ctx.get("/api/exams/" + examId)).json()).totalScore).toBe(0);
  await page.getByRole("button", { name: "交卷结算" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认交卷" }).click();
  await expect(page.locator(".score-num")).toHaveText("0");
});

test("202509试卷：五题题面、公式和样例在网页可用", async ({ page }) => {
  const { ctx, username } = await user();
  await login(page, username);
  await page.getByLabel("年份", { exact: true }).selectOption("2025");
  const row = page.locator(".paper-row").filter({ hasText: "第 39 次 CSP" });
  await row.getByRole("button", { name: "开始模拟" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认开始" }).click();
  await expect(page).toHaveURL(/exam\/\d+/);
  const examId = Number(page.url().split("/").pop());
  const titles = ["蒙特卡洛", "水印检查", "HTTP 头信息", "造题计划（上）", "造题计划（下）"];
  await expect(page.getByRole("tab")).toHaveCount(5);
  for (let i = 0; i < titles.length; ++i) {
    await page.getByRole("tab").nth(i).click();
    await expect(page.locator(".statement-head h2")).toHaveText((i + 1) + ". " + titles[i]);
    await expect(page.locator(".statement-body .katex")).not.toHaveCount(0);
    await expect(page.locator(".statement-body .katex-error")).toHaveCount(0);
    await expect(page.locator(".statement-body")).toContainText("数据范围");
    await expect(page.locator(".sample-card")).toHaveCount(1);
  }
  await writeCode(page, reference(5, "202509"));
  await page.getByRole("button", { name: "运行样例", exact: true }).click();
  await expect(page.locator(".result-summary")).toContainText("样例测试，不计分", { timeout: 90000 });
  await expect(page.locator(".result-summary")).toContainText("通过");
  expect((await (await ctx.get("/api/exams/" + examId)).json()).totalScore).toBe(0);
  await page.getByRole("button", { name: "交卷结算" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "确认交卷" }).click();
  await expect(page.locator(".score-num")).toHaveText("0");
});
