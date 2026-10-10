import React, { useState } from "react";
import {
  importProblem,
  importPack,
  createProblem,
  batchCreateProblems,
} from "../../api/endpoints";
import type { ProblemCreateRequest } from "../../types";
import { toast } from "../../components/common/Toast";
import "./AdminPage.css";

export const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"import" | "create" | "batch">(
    "import",
  );

  // File Upload states
  const [singleFile, setSingleFile] = useState<File | null>(null);
  const [singleLoading, setSingleLoading] = useState(false);

  const [packFile, setPackFile] = useState<File | null>(null);
  const [packLoading, setPackLoading] = useState(false);

  // Manual Create Problem Form state
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [sourceBatch, setSourceBatch] = useState("ORIGINAL");
  const [difficulty, setDifficulty] = useState<"EASY" | "MEDIUM" | "HARD">(
    "EASY",
  );
  const [tagsStr, setTagsStr] = useState("基础语法, 模拟");
  const [timeLimitMs, setTimeLimitMs] = useState(1000);
  const [memoryLimitMb, setMemoryLimitMb] = useState(256);
  const [outputLimitKb, setOutputLimitKb] = useState(256);
  const [evaluationType, setEvaluationType] = useState<
    "FULL" | "SAMPLE_ONLY" | "EXTERNAL_LINK"
  >("FULL");
  const [constructionStatus, setConstructionStatus] = useState<
    "BUILDING" | "VERIFIED"
  >("BUILDING");
  const [license, setLicense] = useState("");
  const [statement, setStatement] = useState("");
  const [inputDesc, setInputDesc] = useState("");
  const [outputDesc, setOutputDesc] = useState("");
  const [constraintsDesc, setConstraintsDesc] = useState("");
  const [scoringNotes, setScoringNotes] = useState(
    "尚在建设，样例仅用于调试，不计正式得分。",
  );
  const [sampleInput, setSampleInput] = useState("");
  const [sampleOutput, setSampleOutput] = useState("");
  const [createLoading, setCreateLoading] = useState(false);

  // Batch JSON
  const [batchJson, setBatchJson] = useState("");
  const [batchLoading, setBatchLoading] = useState(false);

  // Upload Single Problem JSON
  const handleUploadSingle = async () => {
    if (!singleFile) return;
    try {
      setSingleLoading(true);
      const res = await importProblem(singleFile);
      toast.success(`单题导入成功，题目 ID: ${res.id}`);
      setSingleFile(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "单题导入失败");
    } finally {
      setSingleLoading(false);
    }
  };

  // Upload Compressed .json.gz Pack
  const handleUploadPack = async () => {
    if (!packFile) return;
    try {
      setPackLoading(true);
      const res = await importPack(packFile);
      toast.success(`压缩题包导入成功！共导入 ${res.ids.length} 道题目`);
      setPackFile(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "压缩题包导入失败");
    } finally {
      setPackLoading(false);
    }
  };

  // Submit Manual Creation
  const handleCreateProblem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !title.trim()) {
      toast.warning("题号与题目名称为必填项");
      return;
    }

    if (!license.trim()) {
      toast.warning("请填写实际取得的题面与数据使用许可");
      return;
    }
    if (evaluationType === "FULL" && constructionStatus === "VERIFIED") {
      toast.warning(
        "完整评测必须通过题包导入经过验证的测试数据、参考程序和验证报告",
      );
      return;
    }
    try {
      setCreateLoading(true);
      const payload: ProblemCreateRequest = {
        code: code.trim(),
        title: title.trim(),
        sourceBatch,
        difficulty,
        tags: tagsStr
          .split(/[,，]/)
          .map((t) => t.trim())
          .filter(Boolean),
        timeLimitMs: Number(timeLimitMs),
        memoryLimitMb: Number(memoryLimitMb),
        outputLimitKb: Number(outputLimitKb),
        evaluationType,
        constructionStatus,
        license: license.trim(),
        statement,
        inputDescription: inputDesc,
        outputDescription: outputDesc,
        constraintsDescription: constraintsDesc,
        scoringNotes,
        samples: [{ input: sampleInput, output: sampleOutput }],
        testCases: [],
        subtasks: [],
        assets: [],
        validationReport: null,
      };

      const res = await createProblem(payload);
      toast.success(`题目创建成功：${code.trim()} (ID: ${res.id})`);
      // Reset form
      setCode("");
      setTitle("");
      setStatement("");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "创建题目失败");
    } finally {
      setCreateLoading(false);
    }
  };

  // Submit Batch JSON
  const handleBatchSubmit = async () => {
    if (!batchJson.trim()) return;
    try {
      setBatchLoading(true);
      const parsed = JSON.parse(batchJson);
      const problemsArray = Array.isArray(parsed) ? parsed : parsed.problems;
      if (!Array.isArray(problemsArray) || problemsArray.length === 0) {
        toast.warning("JSON 格式不符：需提供题目数组，单次最多20道");
        return;
      }
      const res = await batchCreateProblems(problemsArray);
      toast.success(`批量创建成功，共入库 ${res.ids.length} 道题目`);
      setBatchJson("");
    } catch (err: unknown) {
      toast.error(
        err instanceof Error ? err.message : "批量创建失败，已全部原子回滚",
      );
    } finally {
      setBatchLoading(false);
    }
  };

  return (
    <div className="admin-page-root">
      <div className="admin-header">
        <div>
          <h1 className="page-title">题库资产管理中心</h1>
          <p className="page-subtitle">
            支持标准题包导入、压缩包上传及单题新建。严禁在有活动评测任务或考试时修改题目。
          </p>
        </div>

        <div className="tab-switcher">
          <button
            className={`tab-btn ${activeTab === "import" ? "active" : ""}`}
            onClick={() => setActiveTab("import")}
          >
            题包导入
          </button>
          <button
            className={`tab-btn ${activeTab === "create" ? "active" : ""}`}
            onClick={() => setActiveTab("create")}
          >
            创建单题
          </button>
          <button
            className={`tab-btn ${activeTab === "batch" ? "active" : ""}`}
            onClick={() => setActiveTab("batch")}
          >
            批量 JSON
          </button>
        </div>
      </div>

      {/* ─── Tab 1: Pack Import ──────────────────────── */}
      {activeTab === "import" && (
        <div className="admin-tab-content">
          <div className="import-grid">
            {/* Compressed Pack (.json.gz) */}
            <div className="card import-card">
              <div className="import-card-head">
                <span className="import-icon">📦</span>
                <div>
                  <h3 className="card-title" style={{ margin: 0 }}>
                    导入压缩批量题包 (.json.gz)
                  </h3>
                  <p className="text-xs text-muted">
                    支持如 202403-1.json.gz 等完整测试数据打包文件
                  </p>
                </div>
              </div>

              <div className="import-dropzone">
                <input
                  type="file"
                  accept=".gz,.json.gz"
                  onChange={(e) => setPackFile(e.target.files?.[0] || null)}
                />
                {packFile && (
                  <div className="selected-file-info">
                    已选择：<strong>{packFile.name}</strong> (
                    {(packFile.size / 1024).toFixed(1)} KB)
                  </div>
                )}
              </div>

              <div className="import-tips">
                <ul>
                  <li>压缩包上限 64 MiB，解压上限 128 MiB</li>
                  <li>数据随包内 JSON 直接入库，不依赖外部网络下载</li>
                  <li>
                    校验字段与评分配置；生成器、参考程序和验证报告可随题包保存
                  </li>
                </ul>
              </div>

              <button
                className="btn btn-primary"
                disabled={!packFile || packLoading}
                onClick={handleUploadPack}
              >
                {packLoading ? "正在解压并校验入库..." : "开始导入题包"}
              </button>
            </div>

            {/* Single Problem JSON */}
            <div className="card import-card">
              <div className="import-card-head">
                <span className="import-icon">📄</span>
                <div>
                  <h3 className="card-title" style={{ margin: 0 }}>
                    上传单题 JSON 文件
                  </h3>
                  <p className="text-xs text-muted">
                    符合 Problem 完整契约规范的单个题目描述与数据
                  </p>
                </div>
              </div>

              <div className="import-dropzone">
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => setSingleFile(e.target.files?.[0] || null)}
                />
                {singleFile && (
                  <div className="selected-file-info">
                    已选择：<strong>{singleFile.name}</strong> (
                    {(singleFile.size / 1024).toFixed(1)} KB)
                  </div>
                )}
              </div>

              <div className="import-tips">
                <ul>
                  <li>文本格式须为 UTF-8</li>
                  <li>
                    必须包含完整 samples、testCases、constraintsDescription
                  </li>
                  <li>
                    VERIFIED 题目独立点分值与子任务分值总和须恰好为 100 分
                  </li>
                </ul>
              </div>

              <button
                className="btn btn-secondary"
                disabled={!singleFile || singleLoading}
                onClick={handleUploadSingle}
              >
                {singleLoading ? "正在校验并入库..." : "上传单题"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Tab 2: Manual Create ────────────────────── */}
      {activeTab === "create" && (
        <div className="admin-tab-content">
          <form className="card create-form" onSubmit={handleCreateProblem}>
            <h3 className="card-title">录入新题目</h3>

            <div className="form-row-2">
              <div className="form-group">
                <label>题目编号 (code) *</label>
                <input
                  type="text"
                  placeholder="例如: 202403-1 或 LAB-013"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>题目名称 (title) *</label>
                <input
                  type="text"
                  placeholder="例如: 词频统计"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-row-3">
              <div className="form-group">
                <label>来源批次</label>
                <input
                  type="text"
                  value={sourceBatch}
                  onChange={(e) => setSourceBatch(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>难度级别</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value as any)}
                >
                  <option value="EASY">基础 (EASY)</option>
                  <option value="MEDIUM">中等 (MEDIUM)</option>
                  <option value="HARD">困难 (HARD)</option>
                </select>
              </div>
              <div className="form-group">
                <label>算法标签 (逗号分隔)</label>
                <input
                  type="text"
                  value={tagsStr}
                  onChange={(e) => setTagsStr(e.target.value)}
                />
              </div>
            </div>

            <div className="form-row-3">
              <div className="form-group">
                <label>时间限制 (ms)</label>
                <input
                  type="number"
                  min="100"
                  max="10000"
                  value={timeLimitMs}
                  onChange={(e) => setTimeLimitMs(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label>内存限制 (MB)</label>
                <input
                  type="number"
                  min="32"
                  max="1024"
                  value={memoryLimitMb}
                  onChange={(e) => setMemoryLimitMb(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label>输出大小限制 (KB)</label>
                <input
                  type="number"
                  min="64"
                  max="16384"
                  value={outputLimitKb}
                  onChange={(e) => setOutputLimitKb(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>评测模式</label>
                <select
                  value={evaluationType}
                  onChange={(e) => {
                    const mode = e.target
                      .value as ProblemCreateRequest["evaluationType"];
                    setEvaluationType(mode);
                    if (mode === "FULL") setConstructionStatus("BUILDING");
                  }}
                >
                  <option value="FULL">本站完整数据评测 (FULL)</option>
                  <option value="SAMPLE_ONLY">仅样例测试 (SAMPLE_ONLY)</option>
                  <option value="EXTERNAL_LINK">
                    外部来源链接 (EXTERNAL_LINK)
                  </option>
                </select>
              </div>
              <div className="form-group">
                <label>建设状态</label>
                <select
                  value={constructionStatus}
                  onChange={(e) => setConstructionStatus(e.target.value as any)}
                >
                  <option value="VERIFIED" disabled={evaluationType === "FULL"}>
                    已验证（完整评测请导入验证题包）
                  </option>
                  <option value="BUILDING">建设中 (BUILDING - 仅供研读)</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="problem-license">题面与测试数据使用许可 *</label>
              <input
                id="problem-license"
                value={license}
                onChange={(e) => setLicense(e.target.value)}
                placeholder="例如：本人原创，允许在本站使用；或填写实际授权范围"
                required
              />
              <p className="text-xs text-muted">
                手动录入只创建建设中题目或样例测试题；样例不会生成正式评分数据。
              </p>
            </div>
            <div className="form-group">
              <label>题面说明 (Markdown)</label>
              <textarea
                rows={5}
                placeholder="详细题目描述..."
                value={statement}
                onChange={(e) => setStatement(e.target.value)}
              />
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>输入说明</label>
                <textarea
                  rows={2}
                  value={inputDesc}
                  onChange={(e) => setInputDesc(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>输出说明</label>
                <textarea
                  rows={2}
                  value={outputDesc}
                  onChange={(e) => setOutputDesc(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>数据规模与约束</label>
              <textarea
                rows={2}
                value={constraintsDesc}
                onChange={(e) => setConstraintsDesc(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="problem-scoring">本站评分说明 *</label>
              <textarea
                id="problem-scoring"
                rows={2}
                value={scoringNotes}
                onChange={(e) => setScoringNotes(e.target.value)}
                required
              />
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>样例 #1 输入</label>
                <textarea
                  rows={3}
                  className="font-mono"
                  value={sampleInput}
                  onChange={(e) => setSampleInput(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>样例 #1 预期输出</label>
                <textarea
                  rows={3}
                  className="font-mono"
                  value={sampleOutput}
                  onChange={(e) => setSampleOutput(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={createLoading}
              style={{ marginTop: "12px", alignSelf: "flex-start" }}
            >
              {createLoading ? "正在创建..." : "提交创建题目"}
            </button>
          </form>
        </div>
      )}

      {/* ─── Tab 3: Batch JSON ───────────────────────── */}
      {activeTab === "batch" && (
        <div className="admin-tab-content">
          <div className="card batch-card">
            <h3 className="card-title">原子批量创建题目 (JSON)</h3>
            <p className="text-xs text-muted" style={{ marginBottom: "12px" }}>
              单次提交最多包含 20
              道题目。若任意一道题校验失败或数据不合法，所有操作将自动原子回滚。
            </p>

            <textarea
              rows={16}
              className="font-mono text-xs"
              placeholder={`{\n  "problems": [\n    {\n      "code": "TEST-01",\n      "title": "测试题",\n      "sourceBatch": "202403",\n      ...\n    }\n  ]\n}`}
              value={batchJson}
              onChange={(e) => setBatchJson(e.target.value)}
            />

            <button
              className="btn btn-primary"
              disabled={!batchJson.trim() || batchLoading}
              onClick={handleBatchSubmit}
              style={{ marginTop: "16px", alignSelf: "flex-start" }}
            >
              {batchLoading ? "正在批量处理..." : "执行批量导入"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
