import type {
  SubmissionStatus,
  Difficulty,
  EvaluationType,
  ConstructionStatus,
  CompletionStatus,
} from "../types";

export function formatStatus(status: SubmissionStatus): string {
  const map: Record<SubmissionStatus, string> = {
    AC: "通过",
    WA: "答案错误",
    TLE: "超时",
    MLE: "内存超限",
    RE: "运行错误",
    CE: "编译错误",
    OLE: "输出超限",
    QUEUED: "排队中",
    RUNNING: "判题中",
    SYSTEM_ERROR: "系统错误",
  };
  return map[status] || status;
}

export function formatDifficulty(d: Difficulty): string {
  return { EASY: "基础", MEDIUM: "中等", HARD: "困难" }[d] || d;
}

export function formatEvaluationType(t: EvaluationType): string {
  return (
    {
      FULL: "本站完整数据评测",
      SAMPLE_ONLY: "仅样例测试",
      EXTERNAL_LINK: "外部来源链接",
    }[t] || t
  );
}

export function formatConstructionStatus(s: ConstructionStatus): string {
  return { BUILDING: "建设中", VERIFIED: "已验证" }[s] || s;
}

export function formatCompletionStatus(s: CompletionStatus): string {
  return { UNSOLVED: "未提交", ATTEMPTED: "已尝试", SOLVED: "已通过" }[s] || s;
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatScore(score: number, maxScore: number): string {
  return `${score}/${maxScore}`;
}

export function formatMemory(kb: number | null): string {
  if (kb === null) return "-";
  if (kb < 1024) return `${kb} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function formatTime(ms: number | null): string {
  if (ms === null) return "-";
  return `${ms} ms`;
}

export function isTerminalStatus(status: SubmissionStatus): boolean {
  return !["QUEUED", "RUNNING"].includes(status);
}

export function getStatusColor(status: SubmissionStatus): string {
  switch (status) {
    case "AC":
      return "status-ac";
    case "WA":
      return "status-wa";
    case "RE":
      return "status-re";
    case "TLE":
    case "MLE":
    case "OLE":
      return "status-tle";
    case "CE":
      return "status-ce";
    case "QUEUED":
    case "RUNNING":
      return "status-running";
    case "SYSTEM_ERROR":
      return "status-system-error";
    default:
      return "";
  }
}

export function getDifficultyColor(d: Difficulty): string {
  return (
    { EASY: "diff-easy", MEDIUM: "diff-medium", HARD: "diff-hard" }[d] || ""
  );
}

export function getCompletionColor(s: CompletionStatus): string {
  return { UNSOLVED: "", ATTEMPTED: "status-wa", SOLVED: "status-ac" }[s] || "";
}

export function getSignalName(exitCode: number): string {
  const signals: Record<number, string> = {
    [-6]: "SIGABRT",
    [-8]: "SIGFPE",
    [-9]: "SIGKILL",
    [-11]: "SIGSEGV",
    [-13]: "SIGPIPE",
    [-14]: "SIGALRM",
  };
  return signals[exitCode] || `信号 ${Math.abs(exitCode)}`;
}
