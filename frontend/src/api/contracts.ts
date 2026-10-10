import type { Exam, ExamListItem, Paper, PaperListItem } from "../types";

// Wire DTOs describe Spring's actual responses. Keep derived UI labels here,
// rather than pretending the server returns fields that it does not return.
export interface PaperListResponse {
  examNumber: number;
  examDate: string | null;
  problems: Paper["problems"];
  sourceYear: number;
  sourceBatch: string;
  problemCount: number;
  verifiedCount: number;
  ready: boolean;
}

function paperTitle(batch: string): string {
  return /^\d{6}$/.test(batch)
    ? `${batch.slice(0, 4)}年${Number(batch.slice(4))}月 CSP`
    : batch;
}

export function paperListFromResponse(row: PaperListResponse): PaperListItem {
  return {
    ...row,
    batch: row.sourceBatch,
    title: paperTitle(row.sourceBatch),
    ready: row.ready,
  };
}

export type PaperResponse = Omit<Paper, "title" | "problemIds">;

export function paperFromResponse(row: PaperResponse): Paper {
  const problems = [...row.problems].sort(
    (a, b) => a.sourcePosition - b.sourcePosition,
  );
  return {
    ...row,
    problems,
    title: paperTitle(row.batch),
    problemIds: problems.map((p) => p.id),
  };
}

export interface ExamListResponse {
  id: number;
  title: string;
  status: "RUNNING" | "FINISHED";
  startedAt: string;
  finishedAt: string | null;
  totalScore: number;
}

export function examListFromResponse(row: ExamListResponse): ExamListItem {
  return { ...row, createdAt: row.startedAt, maxScore: 500 };
}

export interface ExamResponse extends ExamListResponse {
  endsAt: string;
  serverNow: string;
  remainingSeconds: number;
  durationSeconds: number;
  maxScore: number;
  pendingSubmissions: number;
  problems: {
    ordinal: number;
    problemId: number;
    code: string;
    title: string;
    problemVersion: number;
    score: number;
    pendingSubmissions: number;
  }[];
}

export function examFromResponse(row: ExamResponse): Exam {
  return {
    ...row,
    createdAt: row.startedAt,
    problems: row.problems.map((p) => ({
      ...p,
      problemCode: p.code,
      problemTitle: p.title,
      maxScore: 100,
    })),
  };
}
