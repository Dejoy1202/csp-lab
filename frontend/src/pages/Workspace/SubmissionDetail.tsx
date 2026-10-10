import React, { useState, useRef, useEffect } from "react";
import Editor from "@monaco-editor/react";
import "../../editor/setup";
import type { Submission } from "../../types";
import { StatusBadge } from "../../components/common/StatusBadge";
import {
  formatDate,
  formatTime,
  formatMemory,
  getSignalName,
} from "../../utils/format";
import { useThemeStore } from "../../store/themeStore";
import { toast } from "../../components/common/Toast";
import { ConfirmDialog } from "../../components/common/ConfirmDialog";

interface SubmissionDetailProps {
  submission: Submission;
  onClose: () => void;
  onRestoreCode?: (code: string) => void;
}

export const SubmissionDetail: React.FC<SubmissionDetailProps> = ({
  submission,
  onClose,
  onRestoreCode,
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);
  const theme = useThemeStore((s) => s.theme);
  const [confirmRestore, setConfirmRestore] = useState(false);

  const handleCopyCode = () => {
    void navigator.clipboard
      .writeText(submission.sourceCode)
      .then(() => toast.success("源代码已复制到剪贴板"))
      .catch(() => toast.error("无法访问剪贴板，请手动复制源码"));
  };

  const isCE = submission.status === "CE";

  return (
    <dialog
      ref={dialogRef}
      className="submission-dialog"
      aria-label={`提交详情 #${submission.id}`}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <div
        className="card sub-detail-modal"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "100%",
          maxWidth: "850px",
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          padding: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <h3 style={{ margin: 0, fontSize: "1.1rem" }}>
              提交详情 #{submission.id}
            </h3>
            <StatusBadge status={submission.status} />
            <span style={{ fontWeight: 600, color: "var(--accent)" }}>
              得分: {submission.score} / {submission.maxScore}
            </span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            ✕ 关闭
          </button>
        </div>

        <div
          style={{
            padding: "20px",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          <div
            style={{
              fontSize: "0.85rem",
              color: "var(--text-secondary)",
              display: "flex",
              gap: "20px",
            }}
          >
            <span>
              题目：{submission.problemCode} - {submission.problemTitle}
            </span>
            <span>语言：C++17</span>
            <span>时间：{formatDate(submission.createdAt)}</span>
          </div>

          {/* Compile error block */}
          {isCE && submission.compileOutput && (
            <div>
              <h4
                style={{
                  fontSize: "0.9rem",
                  marginBottom: "6px",
                  color: "var(--error)",
                }}
              >
                编译诊断信息：
              </h4>
              <pre
                style={{
                  maxHeight: "160px",
                  overflowY: "auto",
                  fontSize: "0.8rem",
                  color: "var(--error)",
                }}
              >
                {submission.compileOutput}
              </pre>
            </div>
          )}

          {/* Test cases results */}
          {submission.subtasks?.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>子任务</th>
                  <th>状态</th>
                  <th>得分</th>
                </tr>
              </thead>
              <tbody>
                {submission.subtasks.map((st) => (
                  <tr key={st.subtaskKey}>
                    <td>
                      {st.label} ({st.subtaskKey})
                    </td>
                    <td>
                      <StatusBadge status={st.status} size="sm" />
                    </td>
                    <td>
                      {st.score}/{st.maxScore}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {submission.results && submission.results.length > 0 && (
            <div>
              <h4 style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
                测试点测评结果：
              </h4>
              <table style={{ fontSize: "0.825rem" }}>
                <thead>
                  <tr>
                    <th>点号</th>
                    <th>状态</th>
                    <th>分值</th>
                    <th>耗时</th>
                    <th>内存</th>
                    <th>信息</th>
                  </tr>
                </thead>
                <tbody>
                  {submission.results.map((r) => (
                    <tr key={r.ordinal}>
                      <td>#{r.ordinal}</td>
                      <td>
                        <StatusBadge status={r.status} size="sm" />
                      </td>
                      <td>
                        {r.score}/{r.maxScore}
                      </td>
                      <td>{formatTime(r.timeMs)}</td>
                      <td>{formatMemory(r.memoryKb)}</td>
                      <td className="text-muted text-xs">
                        {r.exitCode !== null && r.exitCode < 0 ? (
                          <span style={{ color: "var(--error)" }}>
                            {getSignalName(r.exitCode)}
                          </span>
                        ) : (
                          r.message || "-"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {submission.mode === "SAMPLE" &&
            submission.results.map((r) => (
              <section key={"output-" + r.ordinal}>
                <h4>样例 #{r.ordinal} · 程序输出</h4>
                <pre>{r.stdout || "（无输出）"}</pre>
                {r.stderr && (
                  <>
                    <h4>运行诊断</h4>
                    <pre>{r.stderr}</pre>
                  </>
                )}
              </section>
            ))}
          {/* Source Code */}
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "8px",
              }}
            >
              <h4 style={{ fontSize: "0.9rem", margin: 0 }}>
                提交源代码 (C++17)：
              </h4>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={handleCopyCode}
                >
                  复制源码
                </button>
                {onRestoreCode && (
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => {
                      setConfirmRestore(true);
                    }}
                  >
                    恢复到当前草稿
                  </button>
                )}
              </div>
            </div>
            <div
              style={{
                height: "240px",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
              }}
            >
              <Editor
                height="100%"
                language="cpp"
                theme={theme === "dark" ? "vs-dark" : "vs"}
                value={submission.sourceCode}
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  fontSize: 13,
                  scrollBeyondLastLine: false,
                }}
              />
            </div>
          </div>
        </div>
      </div>
      <ConfirmDialog
        open={confirmRestore}
        title="恢复历史代码"
        message="恢复会替换当前草稿。确认使用这次提交的代码？"
        confirmText="确认恢复"
        cancelText="取消"
        variant="warning"
        onCancel={() => setConfirmRestore(false)}
        onConfirm={() => {
          onRestoreCode?.(submission.sourceCode);
          onClose();
        }}
      />
    </dialog>
  );
};
