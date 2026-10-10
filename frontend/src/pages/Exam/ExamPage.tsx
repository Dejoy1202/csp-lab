import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Editor from "@monaco-editor/react";
import "../../editor/setup";
import {
  getExam,
  finishExam,
  getProblemVersion,
  submitCode,
  runSample,
  getSubmissions,
  getSubmission,
} from "../../api/endpoints";
import type {
  Exam,
  Problem,
  Submission,
  SubmissionListItem,
} from "../../types";
import { StatusBadge } from "../../components/common/StatusBadge";
import { Loading } from "../../components/common/Loading";
import { ErrorState } from "../../components/common/ErrorState";
import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import { SubmissionDetail } from "../Workspace/SubmissionDetail";
import { useDraft } from "../../hooks/useDraft";
import { usePolling } from "../../hooks/usePolling";
import { useThemeStore } from "../../store/themeStore";
import { toast } from "../../components/common/Toast";
import { MathMarkdown } from "../../components/Statement/MathMarkdown";
import { formatDuration, formatDate } from "../../utils/format";
import "./ExamPage.css";

export const ExamPage: React.FC = () => {
  const { id: urlExamId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const theme = useThemeStore((s) => s.theme);

  // States
  const [exam, setExam] = useState<Exam | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active Problem inside exam
  const [activeProblemIndex, setActiveProblemIndex] = useState<number>(0);
  const [currentProblem, setCurrentProblem] = useState<Problem | null>(null);
  const activeMeta = exam?.problems[activeProblemIndex];
  const {
    code: currentCode,
    changeCode: setCurrentCode,
    ready: draftReady,
    status: saveStatus,
    error: draftError,
    resolveConflict,
    saveNow,
  } = useDraft(
    exam?.status === "RUNNING" ? (activeMeta?.problemId ?? null) : null,
  );
  const [problemLoading, setProblemLoading] = useState(false);
  const [readingSize, setReadingSize] = useState(16);
  const [showHistory, setShowHistory] = useState(false);

  // Timer
  const [remainingSec, setRemainingSec] = useState<number>(14400);
  const endingRef = useRef(false);

  // Submission & Polling
  const [activeSubId, setActiveSubId] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    submission: activeResult,
    isPolling,
    error: pollingError,
  } = usePolling(activeSubId);

  // Confirm Dialog for Finishing Exam
  const [showFinishConfirm, setShowFinishConfirm] = useState(false);
  const [selectedSubDetail, setSelectedSubDetail] = useState<Submission | null>(
    null,
  );
  const [examSubmissions, setExamSubmissions] = useState<SubmissionListItem[]>(
    [],
  );

  // 1. Initial Load: Check if there is an active exam or load history
  const fetchInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!urlExamId) {
        navigate("/");
        return;
      }
      setExam(await getExam(Number(urlExamId)));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "获取考试信息失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, [urlExamId]);

  // Server remainingSeconds is authoritative; monotonic time ignores wall-clock changes.
  useEffect(() => {
    if (!exam || exam.status !== "RUNNING") return;
    const started = performance.now();
    const remaining = exam.remainingSeconds;
    const tick = () =>
      setRemainingSec(
        Math.max(
          0,
          remaining - Math.floor((performance.now() - started) / 1000),
        ),
      );
    tick();
    const timer = setInterval(tick, 250);
    return () => clearInterval(timer);
  }, [exam?.id, exam?.status, exam?.remainingSeconds, exam?.serverNow]);

  // Keep scores and expiry synchronized, including jobs completing after submission.
  useEffect(() => {
    if (!exam || (exam.status === "FINISHED" && exam.pendingSubmissions === 0))
      return;
    let mounted = true;
    let timer: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      try {
        const latest = await getExam(exam.id);
        if (mounted) setExam(latest);
      } catch {
        /* Retry the next read without duplicating submissions. */
      }
      if (mounted) timer = setTimeout(refresh, 2000);
    };
    timer = setTimeout(refresh, 2000);
    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, [exam?.id, exam?.status, exam?.pendingSubmissions]);

  // Fetch the exam's frozen problem version, without touching the editor draft.
  useEffect(() => {
    if (!activeMeta) return;
    let mounted = true;
    setCurrentProblem(null);
    setProblemLoading(true);
    setActiveSubId(null);
    void getProblemVersion(activeMeta.problemId, activeMeta.problemVersion)
      .then((p) => {
        if (mounted) setCurrentProblem(p);
      })
      .catch(() => {
        if (mounted) toast.error("读取题目失败");
      })
      .finally(() => {
        if (mounted) setProblemLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [activeMeta?.problemId, activeMeta?.problemVersion]);

  // 4. Load exam submissions for review when finished
  useEffect(() => {
    if (exam) {
      getSubmissions({ examId: exam.id, page: 1, size: 50 })
        .then((res) => {
          setExamSubmissions(res.items);
        })
        .catch(() => {});
    }
  }, [exam?.id, activeResult?.status]);

  // Action: Submit Code during Exam
  const handleExamSubmit = async (sample = false) => {
    if (
      !exam ||
      exam.status !== "RUNNING" ||
      !currentProblem ||
      !draftReady ||
      isSubmitting ||
      isPolling
    )
      return;
    try {
      setIsSubmitting(true);
      const res = await (sample ? runSample : submitCode)({
        problemId: currentProblem.id,
        language: "CPP17",
        sourceCode: currentCode,
        examId: exam.id,
      });
      setActiveSubId(res.id);
      toast.info(
        sample ? "样例已提交（不计分）" : "模考代码已提交，正在评测...",
      );
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "提交失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Action: Finish Exam
  const handleFinishExam = async () => {
    if (!exam || endingRef.current) return;
    endingRef.current = true;
    try {
      await saveNow();
      const finished = await finishExam(exam.id);
      setExam(finished);
      setShowFinishConfirm(false);
      toast.success("交卷成功！已生成模考成绩单");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "交卷失败");
    } finally {
      endingRef.current = false;
    }
  };

  if (loading) return <Loading text="正在同步模拟考试数据..." />;
  if (error)
    return (
      <ErrorState
        title="考试模块异常"
        message={error}
        onRetry={fetchInitialData}
      />
    );

  // ─── Case 1: Exam Finished (Review View) ──────
  if (exam && exam.status === "FINISHED") {
    return (
      <div className="exam-root exam-review-container">
        <div className="card exam-report-card">
          <div className="report-header">
            <div>
              <span className="tag tag-success">
                {exam.pendingSubmissions > 0
                  ? "已交卷，等待判题"
                  : "考试已结算"}
              </span>
              <h1 className="report-title">{exam.title}</h1>
              <p className="report-date text-muted text-sm">
                交卷时间：{formatDate(exam.finishedAt || exam.createdAt)}
              </p>
            </div>
            <div className="report-total-score">
              <span className="score-num">{exam.totalScore}</span>
              <span className="score-denom">/ {exam.maxScore}</span>
              <span className="score-sim-tag">
                本站模拟评分，非官方认证成绩
              </span>
            </div>
          </div>

          <div className="report-problems-grid">
            {exam.problems.map((p, idx) => (
              <div key={p.problemId} className="report-problem-item">
                <span className="item-label">
                  第 {idx + 1} 题 ({p.problemCode})
                </span>
                <span className="item-title">{p.problemTitle}</span>
                <span className="item-score">
                  {p.score} / {p.maxScore} 分
                </span>
              </div>
            ))}
          </div>

          {exam.pendingSubmissions > 0 && (
            <div className="pending-notice">
              ⏳ 还有 {exam.pendingSubmissions}{" "}
              个提交处于判题队列中，完成后分数将自动结算。
            </div>
          )}

          <div className="review-actions">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setExam(null);
                navigate("/exam");
              }}
            >
              返回考试列表
            </button>
          </div>
        </div>

        {currentProblem && (
          <details className="review-statement">
            <summary>查看题面与评分 · {currentProblem.title}</summary>
            <div className="statement-body">
              <div className="review-problem-nav">
                {exam.problems.map((p, i) => (
                  <button
                    key={p.problemId}
                    className={activeProblemIndex === i ? "active" : ""}
                    onClick={() => setActiveProblemIndex(i)}
                  >
                    第 {i + 1} 题
                  </button>
                ))}
              </div>
              <h2>{currentProblem.title}</h2>
              {currentProblem.statement && (
                <MathMarkdown content={currentProblem.statement} />
              )}{" "}
              {[
                ["输入格式", currentProblem.inputDescription],
                ["输出格式", currentProblem.outputDescription],
                ["数据范围", currentProblem.constraintsDescription],
                ["本站评分规则", currentProblem.scoringNotes],
              ].map(
                ([label, content]) =>
                  content && (
                    <section key={label}>
                      <h4>{label}</h4>
                      <MathMarkdown content={content} />
                    </section>
                  ),
              )}
              {currentProblem.samples.map((sample) => (
                <section key={sample.ordinal}>
                  <h4>样例 {sample.ordinal}</h4>
                  <pre>{sample.inputData}</pre>
                  <pre>{sample.expectedOutput}</pre>
                </section>
              ))}
            </div>
          </details>
        )}
        {/* Submissions list for review */}
        <div className="card" style={{ marginTop: "24px" }}>
          <h3 className="card-title">
            本场考试提交复盘 ({examSubmissions.length} 次)
          </h3>
          {examSubmissions.length === 0 ? (
            <div className="text-muted text-sm text-center">
              本场考试无提交记录
            </div>
          ) : (
            <table className="results-table">
              <thead>
                <tr>
                  <th>提交ID</th>
                  <th>题目</th>
                  <th>状态</th>
                  <th>得分</th>
                  <th>提交时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {examSubmissions.map((s) => (
                  <tr key={s.id}>
                    <td>#{s.id}</td>
                    <td>
                      {s.problemCode} - {s.problemTitle}
                    </td>
                    <td>
                      <StatusBadge status={s.status} size="sm" />
                    </td>
                    <td>{s.score}分</td>
                    <td className="text-xs text-muted">
                      {formatDate(s.createdAt)}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={async () => {
                          const full = await getSubmission(s.id);
                          setSelectedSubDetail(full);
                        }}
                      >
                        查看代码与测试点
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {selectedSubDetail && (
          <SubmissionDetail
            submission={selectedSubDetail}
            onClose={() => setSelectedSubDetail(null)}
          />
        )}
      </div>
    );
  }

  // ─── Case 2: Active Exam in Progress ──────────
  if (exam && exam.status === "RUNNING") {
    const isUrgent = remainingSec <= 300; // < 5 mins
    const isWarning = remainingSec <= 1800; // < 30 mins

    return (
      <div className="exam-root exam-running-layout">
        {/* Top Control Bar */}
        <div className="exam-top-bar">
          <div className="exam-title-box">
            <span className="exam-status-dot" />
            <span className="exam-name">{exam.title}</span>
            <span className="sim-pill">本站模拟评分</span>
          </div>

          <div
            className={`exam-countdown ${isUrgent ? "urgent" : isWarning ? "warning" : ""}`}
          >
            <span className="clock-icon">剩余</span>
            <span className="countdown-time font-mono">
              {formatDuration(remainingSec)}
            </span>
          </div>

          <div className="exam-top-actions">
            <span className="current-total-score">
              当前累计: <strong>{exam.totalScore}</strong> / {exam.maxScore} 分
            </span>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => setShowFinishConfirm(true)}
            >
              交卷结算
            </button>
          </div>
        </div>

        {/* Problem Navigation Tabs */}
        <div className="exam-tabs-bar" role="tablist" aria-label="五道考试题目">
          {exam.problems.map((p, idx) => (
            <button
              key={p.problemId}
              className={`exam-tab-btn ${activeProblemIndex === idx ? "active" : ""}`}
              role="tab"
              aria-selected={activeProblemIndex === idx}
              onClick={() => setActiveProblemIndex(idx)}
            >
              <span className="tab-order">T{idx + 1}</span>
              <span className="tab-code">{p.problemTitle}</span>
              <span className={`tab-score ${p.score > 0 ? "has-score" : ""}`}>
                {p.score > 0 ? `${p.score}分` : "0分"}
              </span>
            </button>
          ))}
        </div>

        {/* Embedded Workspace for Active Problem */}
        <div className="exam-workspace-area">
          {problemLoading ? (
            <Loading text="加载题目中..." />
          ) : !currentProblem ? (
            <div className="text-center text-muted">题目加载失败</div>
          ) : (
            <div className="exam-split-pane">
              {/* Left Statement */}
              <div className="exam-statement-panel">
                <div className="statement-head">
                  <div className="statement-tools">
                    <span>题目描述</span>
                    <label>
                      字号{" "}
                      <select
                        aria-label="题面字号"
                        value={readingSize}
                        onChange={(e) => setReadingSize(Number(e.target.value))}
                      >
                        {[15, 16, 18, 20].map((n) => (
                          <option key={n}>{n}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <h2>
                    {activeProblemIndex + 1}. {currentProblem.title}
                  </h2>
                  <div className="text-xs text-muted">
                    限时: {currentProblem.timeLimitMs}ms | 内存:{" "}
                    {currentProblem.memoryLimitMb}MB
                  </div>
                </div>
                <div
                  className="statement-body"
                  style={{ fontSize: readingSize }}
                >
                  {currentProblem.statement && (
                    <MathMarkdown content={currentProblem.statement} />
                  )}
                  {[
                    ["输入格式", currentProblem.inputDescription],
                    ["输出格式", currentProblem.outputDescription],
                    ["数据范围", currentProblem.constraintsDescription],
                    ["本站评分规则", currentProblem.scoringNotes],
                  ].map(
                    ([label, content]) =>
                      content && (
                        <section key={label}>
                          <h4>{label}</h4>
                          <MathMarkdown content={content} />
                        </section>
                      ),
                  )}
                  {currentProblem.subtasks.map((st) => (
                    <p key={st.subtaskKey}>
                      {st.label}：{st.score} 分（{st.subtaskKey}）
                    </p>
                  ))}
                  {currentProblem.samples &&
                    currentProblem.samples.length > 0 && (
                      <div className="exam-sample-section">
                        <h4>输入输出样例</h4>
                        {currentProblem.samples.map((s) => (
                          <div key={s.ordinal} className="sample-card">
                            <div className="sample-header">
                              样例 #{s.ordinal}
                            </div>
                            <div className="sample-grid">
                              <div>
                                <span className="sample-label">输入</span>
                                <pre className="sample-pre">{s.inputData}</pre>
                              </div>
                              <div>
                                <span className="sample-label">输出</span>
                                <pre className="sample-pre">
                                  {s.expectedOutput}
                                </pre>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                </div>
              </div>

              {/* Right Editor & Results */}
              <div className="exam-editor-panel">
                <div className="exam-editor-head">
                  <span>
                    C++17 ·{" "}
                    {saveStatus === "saved"
                      ? "草稿已保存"
                      : saveStatus === "saving"
                        ? "保存中"
                        : "有未保存的修改"}
                  </span>
                  {activeResult && <StatusBadge status={activeResult.status} />}
                </div>

                <div className="exam-editor-wrapper">
                  <Editor
                    height="100%"
                    language="cpp"
                    theme={theme === "dark" ? "vs-dark" : "vs"}
                    value={currentCode}
                    onChange={setCurrentCode}
                    options={{
                      readOnly: !draftReady,
                      editContext: false,
                      fontSize: 14,
                      fontFamily: "Consolas, 'Courier New', monospace",
                      lineHeight: 22,
                      padding: { top: 16 },
                      scrollBeyondLastLine: false,
                      minimap: { enabled: false },
                      automaticLayout: true,
                    }}
                  />
                </div>

                {draftError && (
                  <p className="editor-error" role="alert">
                    {draftError}
                  </p>
                )}
                {pollingError && (
                  <p className="editor-error" role="alert">
                    {pollingError}（正在重试查询）
                  </p>
                )}
                <div className="inline-results">
                  <button
                    className="result-tab"
                    aria-expanded={showHistory}
                    onClick={() => setShowHistory(!showHistory)}
                  >
                    本题提交记录 (
                    {
                      examSubmissions.filter(
                        (s) => s.problemId === currentProblem.id,
                      ).length
                    }
                    ) {showHistory ? "收起" : "展开"}
                  </button>
                  {showHistory && (
                    <div className="result-history">
                      {examSubmissions
                        .filter((s) => s.problemId === currentProblem.id)
                        .map((s) => (
                          <button
                            key={s.id}
                            onClick={() => {
                              void getSubmission(s.id)
                                .then(setSelectedSubDetail)
                                .catch((e) => toast.error(e.message));
                            }}
                          >
                            <span>#{s.id}</span>
                            <StatusBadge status={s.status} size="sm" />
                            <span>
                              {s.mode === "SAMPLE"
                                ? "样例"
                                : s.score + " / 100"}
                            </span>
                          </button>
                        ))}
                    </div>
                  )}
                  {activeResult && !isPolling && (
                    <div className="result-summary">
                      <StatusBadge status={activeResult.status} />
                      <span>
                        {activeResult.mode === "SAMPLE"
                          ? "样例测试，不计分"
                          : activeResult.score + " / 100 分"}
                      </span>
                      <button
                        onClick={() => setSelectedSubDetail(activeResult)}
                      >
                        测试点与诊断 →
                      </button>
                    </div>
                  )}
                </div>
                <div className="exam-action-bar">
                  <div className="exam-sub-info">
                    {isPolling && (
                      <span
                        className="text-sm"
                        style={{ color: "var(--accent)" }}
                      >
                        正在判题...
                      </span>
                    )}
                    {activeResult && !isPolling && (
                      <span className="text-sm">
                        {activeResult.mode === "SAMPLE" ? (
                          "样例测试，不计分"
                        ) : (
                          <>
                            本次评测得分: <strong>{activeResult.score}</strong>{" "}
                            分
                          </>
                        )}
                      </span>
                    )}
                  </div>
                  <button
                    className="btn btn-secondary"
                    disabled={
                      isSubmitting ||
                      isPolling ||
                      !draftReady ||
                      remainingSec <= 0
                    }
                    onClick={() => {
                      void handleExamSubmit(true);
                    }}
                  >
                    运行样例
                  </button>
                  {activeResult && !isPolling && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => setSelectedSubDetail(activeResult)}
                    >
                      查看本次结果
                    </button>
                  )}
                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      void handleExamSubmit();
                    }}
                    disabled={
                      isSubmitting ||
                      isPolling ||
                      !draftReady ||
                      remainingSec <= 0
                    }
                  >
                    {isSubmitting ? "正在提交..." : "提交此题"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <ConfirmDialog
          open={saveStatus === "conflict"}
          title="草稿版本冲突提示"
          message="其他窗口更新了草稿。可以保留当前代码，或加载最新服务端版本。"
          confirmText="保留本地修改"
          cancelText="加载服务端版本"
          variant="warning"
          onConfirm={() => {
            void resolveConflict(true);
          }}
          onCancel={() => {
            void resolveConflict(false);
          }}
        />
        {selectedSubDetail && (
          <SubmissionDetail
            submission={selectedSubDetail}
            onClose={() => setSelectedSubDetail(null)}
            onRestoreCode={setCurrentCode}
          />
        )}
        {/* Finish Confirmation Dialog */}
        <ConfirmDialog
          open={showFinishConfirm}
          title="交卷确认"
          message={`确认交卷？当前已得 ${exam.totalScore} 分。交卷后考试立即结束，不能继续作答或提交。`}
          confirmText="确认交卷"
          cancelText="继续作答"
          variant="danger"
          onConfirm={handleFinishExam}
          onCancel={() => setShowFinishConfirm(false)}
        />
      </div>
    );
  }

  return (
    <ErrorState title="考试不存在" message="请返回模拟考试首页选择试卷。" />
  );
};
