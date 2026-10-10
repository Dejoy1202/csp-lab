import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { getPapers, getExams, createExam } from "../../api/endpoints";
import type { PaperListItem, ExamListItem } from "../../types";
import { Loading } from "../../components/common/Loading";
import { ErrorState } from "../../components/common/ErrorState";
import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import { toast } from "../../components/common/Toast";
import "./ExamLobby.css";
export function ExamLobby() {
  const [papers, setPapers] = useState<PaperListItem[]>([]);
  const [active, setActive] = useState<ExamListItem | null>(null);
  const [year, setYear] = useState("all");
  const [readyOnly, setReadyOnly] = useState(false);
  const [selected, setSelected] = useState<PaperListItem | null>(null);
  const [pending, setPending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [p, e] = await Promise.all([getPapers(), getExams()]);
      setPapers(p);
      setActive(e.find((x) => x.status === "RUNNING") || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "无法读取试卷");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    void load();
  }, []);
  if (loading) return <Loading text="正在读取历届试卷…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  const years = [...new Set(papers.map((p) => p.batch.slice(0, 4)))];
  const filtered = papers
    .filter(
      (p) =>
        (year === "all" || p.batch.startsWith(year)) && (!readyOnly || p.ready),
    )
    .sort(
      (a, b) =>
        Number(b.ready) - Number(a.ready) || b.batch.localeCompare(a.batch),
    );
  return (
    <div className="paper-lobby">
      <div className="lobby-heading">
        <div>
          <h1>历届模拟考试</h1>
          <p>选择一套试卷，开始四小时的完整作答。</p>
        </div>
        <span className="exam-format">4 小时 · 5 道题 · 500 分</span>
      </div>
      {active && (
        <div className="running-banner">
          <div>
            <strong>你有一场进行中的考试</strong>
            <p>{active.title} · 离开页面后计时继续</p>
          </div>
          <Link className="btn btn-primary" to={"/exam/" + active.id}>
            继续考试
          </Link>
        </div>
      )}
      <div className="catalog-toolbar">
        <div className="year-selector">
          <label htmlFor="paper-year">年份</label>
          <select
            id="paper-year"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          >
            <option value="all">全部年份</option>
            {years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>
          <label className="ready-filter">
            <input
              type="checkbox"
              checked={readyOnly}
              onChange={(e) => setReadyOnly(e.target.checked)}
            />
            只看可模拟
          </label>
        </div>
        <span className="coverage-note">
          {papers.filter((p) => p.ready).length} 套可模拟 / {papers.length}{" "}
          个历史批次
        </span>
      </div>
      <div className="paper-list">
        {filtered.length === 0 ? (
          <div className="lobby-empty">
            该年份尚无已验证的完整试卷，取消筛选可查看建设进度。
          </div>
        ) : (
          filtered.map((p) => (
            <article key={p.batch} className="paper-row">
              <div className="paper-date">
                <span>{p.batch.slice(0, 4)}</span>
                <strong>{Number(p.batch.slice(4))} 月</strong>
              </div>
              <div className="paper-content">
                <div className="paper-title">
                  <h2>
                    {p.examNumber === 0
                      ? "2013 年试题"
                      : "第 " + p.examNumber + " 次 CSP"}
                  </h2>
                  <span className={p.ready ? "readiness ready" : "readiness"}>
                    {p.ready
                      ? "可模拟"
                      : "建设中 · " + p.verifiedCount + "/5 已验证"}
                  </span>
                </div>
                <ol className="paper-problems">
                  {p.problems.map((q) => (
                    <li key={q.id}>
                      <span>{q.sourcePosition}</span>
                      {q.title}
                    </li>
                  ))}
                </ol>
                <p className="paper-meta">
                  {p.examDate ? "认证日期 " + p.examDate : p.batch + " 批次"} ·{" "}
                  {p.ready ? "本站独立测试数据" : "题意与独立测试数据尚待完成"}
                </p>
              </div>
              <button
                className="btn btn-primary paper-start"
                disabled={!p.ready || !!active || pending}
                onClick={() => setSelected(p)}
              >
                {p.ready ? "开始模拟" : "暂未开放"}
              </button>
            </article>
          ))
        )}
      </div>
      <p className="catalog-footnote">
        每套试卷的五题及自建数据全部验证后才开放。本站模拟评分与官方认证成绩不同。
      </p>
      <ConfirmDialog
        open={!!selected}
        title="开始模拟考试"
        message={
          (selected?.title || "") +
          "：确认后立即开始四小时计时，离开或刷新页面不会暂停。"
        }
        confirmText={pending ? "正在创建…" : "确认开始"}
        cancelText="稍后再考"
        onCancel={() => {
          if (!pending) setSelected(null);
        }}
        onConfirm={() => {
          if (!selected || pending) return;
          setPending(true);
          void createExam({ batch: selected.batch })
            .then((e) => navigate("/exam/" + e.id))
            .catch((e) => toast.error(e.message))
            .finally(() => setPending(false));
        }}
      />
    </div>
  );
}
