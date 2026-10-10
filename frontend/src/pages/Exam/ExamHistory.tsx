import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { getExams } from "../../api/endpoints";
import type { ExamListItem } from "../../types";
import { Loading } from "../../components/common/Loading";
import { ErrorState } from "../../components/common/ErrorState";
import { formatDate } from "../../utils/format";
import "./ExamLobby.css";
export function ExamHistory() {
  const [exams, setExams] = useState<ExamListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const load = async () => {
    setError("");
    try {
      setExams(await getExams());
    } catch (e) {
      setError(e instanceof Error ? e.message : "无法读取考试记录");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    void load();
  }, []);
  if (loading) return <Loading text="正在读取考试记录…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  const finished = exams.filter((e) => e.status === "FINISHED").reverse();
  return (
    <div className="history-page">
      <div className="lobby-heading">
        <div>
          <h1>考试记录</h1>
          <p>查看每次成绩，回看提交代码与测试点结果。</p>
        </div>
        <span className="exam-format">本站模拟评分</span>
      </div>
      {finished.length > 1 && (
        <div
          className="history-chart"
          role="img"
          aria-label="历次模拟考试分数变化，目标300分"
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={finished.map((e, i) => ({
                场次: i + 1,
                分数: e.totalScore,
              }))}
              margin={{ top: 14, right: 16, left: -15, bottom: 0 }}
            >
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis
                dataKey="场次"
                stroke="var(--text-secondary)"
                fontSize={12}
              />
              <YAxis
                domain={[0, 500]}
                ticks={[0, 100, 200, 300, 400, 500]}
                stroke="var(--text-secondary)"
                fontSize={12}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--bg-secondary)",
                  borderColor: "var(--border)",
                  color: "var(--text-primary)",
                }}
              />
              <ReferenceLine
                y={300}
                stroke="var(--success)"
                strokeDasharray="4 4"
              />
              <Line
                dataKey="分数"
                stroke="var(--accent)"
                strokeWidth={2}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      {exams.length === 0 ? (
        <div className="history-empty">
          <h2>还没有考试记录</h2>
          <p>完成第一次模拟后，成绩与提交会保存在这里。</p>
          <Link className="btn btn-primary" to="/">
            选择试卷
          </Link>
        </div>
      ) : (
        <div className="history-table-wrap">
          <table>
            <thead>
              <tr>
                <th>试卷</th>
                <th>状态</th>
                <th>得分</th>
                <th>开始时间</th>
                <th>
                  <span className="sr-only">操作</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {exams.map((e) => (
                <tr key={e.id}>
                  <td>{e.title}</td>
                  <td>{e.status === "RUNNING" ? "进行中" : "已交卷"}</td>
                  <td>
                    <span className="score-number">{e.totalScore}</span>
                    <span className="text-muted"> / 500</span>
                  </td>
                  <td>{formatDate(e.createdAt)}</td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => navigate("/exam/" + e.id)}
                    >
                      {e.status === "RUNNING" ? "继续考试" : "成绩与复盘"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
