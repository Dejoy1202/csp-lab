import { api } from "./client";
import {
  examFromResponse,
  examListFromResponse,
  paperFromResponse,
  paperListFromResponse,
} from "./contracts";
import type {
  ExamResponse,
  ExamListResponse,
  PaperResponse,
  PaperListResponse,
} from "./contracts";
import type {
  Problem,
  ProblemListItem,
  PaginatedResponse,
  Submission,
  SubmissionListItem,
  Draft,
  DraftSaveRequest,
  Exam,
  ExamListItem,
  ExamCreateRequest,
  Paper,
  PaperListItem,
  SubmitRequest,
  ProblemCreateRequest,
} from "../types";

// ─── Problems ────────────────────────────────────────────
interface ProblemParams {
  year?: number;
  batch?: string;
  difficulty?: string;
  tag?: string;
  status?: string;
  page?: number;
  size?: number;
}

export function getProblems(params?: ProblemParams) {
  return api.get<PaginatedResponse<ProblemListItem>>(
    "/problems",
    params as Record<string, string | number>,
  );
}

export function getProblem(id: number) {
  return api.get<Problem>(`/problems/${id}`);
}

export function getProblemVersion(id: number, version: number) {
  return api.get<Problem>(`/problems/${id}/versions/${version}`);
}

// ─── Papers ──────────────────────────────────────────────
export async function getPapers(): Promise<PaperListItem[]> {
  return (await api.get<PaperListResponse[]>("/papers")).map(
    paperListFromResponse,
  );
}

export async function getPaper(batch: string): Promise<Paper> {
  return paperFromResponse(await api.get<PaperResponse>(`/papers/${batch}`));
}

// ─── Submissions ─────────────────────────────────────────
export function submitCode(req: SubmitRequest) {
  return api.post<{ id: number; status: string }>("/submissions", req);
}

export function runSample(req: SubmitRequest) {
  return api.post<{ id: number; status: string }>("/runs", req);
}

export function getSubmission(id: number) {
  return api.get<Submission>(`/submissions/${id}`);
}

interface SubmissionParams {
  problemId?: number;
  examId?: number;
  status?: string;
  page?: number;
  size?: number;
}

export function getSubmissions(params?: SubmissionParams) {
  return api.get<PaginatedResponse<SubmissionListItem>>(
    "/submissions",
    params as Record<string, string | number>,
  );
}

// ─── Drafts ──────────────────────────────────────────────
export function getDraft(problemId: number) {
  return api.get<Draft>(`/problems/${problemId}/draft`);
}

export function saveDraft(problemId: number, req: DraftSaveRequest) {
  return api.put<Draft>(`/problems/${problemId}/draft`, req);
}

// ─── Exams ───────────────────────────────────────────────
export async function createExam(req: ExamCreateRequest): Promise<Exam> {
  return examFromResponse(await api.post<ExamResponse>("/exams", req));
}

export async function getExams(): Promise<ExamListItem[]> {
  return (await api.get<ExamListResponse[]>("/exams")).map(
    examListFromResponse,
  );
}

export async function getExam(id: number): Promise<Exam> {
  return examFromResponse(await api.get<ExamResponse>(`/exams/${id}`));
}

export async function finishExam(id: number): Promise<Exam> {
  return examFromResponse(await api.post<ExamResponse>(`/exams/${id}/finish`));
}

// ─── Admin ───────────────────────────────────────────────
export function createProblem(data: ProblemCreateRequest) {
  return api.post<{ id: number }>("/admin/problems", data);
}

export function updateProblem(id: number, data: ProblemCreateRequest) {
  return api.put<{ id: number }>(`/admin/problems/${id}`, data);
}

export function batchCreateProblems(problems: ProblemCreateRequest[]) {
  return api.post<{ ids: number[] }>("/admin/problems/batch", { problems });
}

export function importProblem(file: File) {
  return api.upload<{ id: number }>("/admin/problems/import", file);
}

export function importPack(file: File) {
  return api.upload<{ ids: number[] }>("/admin/problems/import-pack", file);
}

export function getAsset(id: number, name: string) {
  return api.get<{ content: string }>(`/admin/problems/${id}/assets/${name}`);
}
