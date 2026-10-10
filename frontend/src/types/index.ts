// ─── Enums ───────────────────────────────────────────────
export type Difficulty = "EASY" | "MEDIUM" | "HARD";
export type EvaluationType = "FULL" | "SAMPLE_ONLY" | "EXTERNAL_LINK";
export type ConstructionStatus = "BUILDING" | "VERIFIED";
export type CompletionStatus = "UNSOLVED" | "ATTEMPTED" | "SOLVED";
export type SubmissionStatus =
  | "QUEUED"
  | "RUNNING"
  | "AC"
  | "WA"
  | "TLE"
  | "MLE"
  | "RE"
  | "CE"
  | "OLE"
  | "SYSTEM_ERROR";
export type SubmissionMode = "JUDGE" | "SAMPLE";
export type Language = "CPP17";
export type AssetKind = "GENERATOR" | "REFERENCE" | "VALIDATOR" | "REPORT";

// ─── Problem ─────────────────────────────────────────────
export interface Sample {
  ordinal: number;
  inputData: string;
  expectedOutput: string;
}

export interface ScoringEntry {
  ordinal: number;
  score: number;
  subtaskKey: string | null;
}

export interface Subtask {
  subtaskKey: string;
  label: string;
  score: number;
}

export interface Problem {
  id: number;
  code: string;
  title: string;
  sourceBatch: string | null;
  sourceYear: number | null;
  sourcePosition: number | null;
  sourceUrl: string | null;
  difficulty: Difficulty;
  tags: string[];
  timeLimitMs: number;
  memoryLimitMb: number;
  outputLimitKb: number;
  evaluationType: EvaluationType;
  constructionStatus: ConstructionStatus;
  completionStatus: CompletionStatus;
  license: string;
  statement: string | null;
  inputDescription: string | null;
  outputDescription: string | null;
  constraintsDescription: string | null;
  scoringNotes: string | null;
  samples: Sample[];
  scoring: ScoringEntry[];
  subtasks: Subtask[];
  validationReport: string | null;
}

export interface ProblemListItem {
  id: number;
  code: string;
  title: string;
  sourceBatch: string | null;
  difficulty: Difficulty;
  tags: string[];
  timeLimitMs: number;
  memoryLimitMb: number;
  evaluationType: EvaluationType;
  constructionStatus: ConstructionStatus;
  completionStatus: CompletionStatus;
}

// ─── Pagination ──────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

// ─── Submission ──────────────────────────────────────────
export interface TestResult {
  ordinal: number;
  status: SubmissionStatus;
  score: number;
  maxScore: number;
  subtaskKey: string | null;
  timeMs: number | null;
  memoryKb: number | null;
  exitCode: number | null;
  message: string | null;
  stdout: string | null;
  stderr: string | null;
}

export interface SubtaskResult {
  subtaskKey: string;
  label: string;
  score: number;
  maxScore: number;
  status: SubmissionStatus;
}

export interface Submission {
  id: number;
  problemId: number;
  problemCode: string;
  problemTitle: string;
  language: Language;
  status: SubmissionStatus;
  score: number;
  maxScore: number;
  mode: SubmissionMode;
  sourceCode: string;
  compileOutput: string | null;
  results: TestResult[];
  subtasks: SubtaskResult[];
  examId: number | null;
  problemVersion: number | null;
  createdAt: string;
}

export interface SubmissionListItem {
  id: number;
  problemId: number;
  problemCode: string;
  problemTitle: string;
  language: Language;
  status: SubmissionStatus;
  score: number;
  maxScore: number;
  mode: SubmissionMode;
  examId: number | null;
  createdAt: string;
}

// ─── Draft ───────────────────────────────────────────────
export interface Draft {
  sourceCode: string;
  revision: number;
}

// ─── Exam ────────────────────────────────────────────────
export interface ExamProblem {
  problemId: number;
  problemCode: string;
  problemTitle: string;
  score: number;
  maxScore: number;
  problemVersion: number;
}

export interface Exam {
  id: number;
  title: string;
  status: "RUNNING" | "FINISHED";
  endsAt: string;
  serverNow: string;
  remainingSeconds: number;
  durationSeconds: number;
  maxScore: number;
  totalScore: number;
  pendingSubmissions: number;
  problems: ExamProblem[];
  createdAt: string;
  finishedAt: string | null;
}

export interface ExamListItem {
  id: number;
  title: string;
  totalScore: number;
  maxScore: number;
  status: "RUNNING" | "FINISHED";
  createdAt: string;
}

// ─── Paper ───────────────────────────────────────────────
export interface PaperProblem {
  id: number;
  code: string;
  title: string;
  sourcePosition: number;
}

export interface Paper {
  batch: string;
  title: string;
  ready: boolean;
  problemIds: number[];
  problems: PaperProblem[];
}

export interface PaperListItem {
  examNumber: number;
  examDate: string | null;
  verifiedCount: number;
  problems: PaperProblem[];
  batch: string;
  title: string;
  ready: boolean;
}

// ─── Request Types ───────────────────────────────────────
export interface SubmitRequest {
  problemId: number;
  language: Language;
  sourceCode: string;
  examId: number | null;
}

export interface DraftSaveRequest {
  sourceCode: string;
  revision: number;
}

export interface ExamCreateRequest {
  batch?: string;
  title?: string;
  problemIds?: number[];
}

// ─── Admin Types ─────────────────────────────────────────
export interface AssetEntry {
  name: string;
  kind: AssetKind;
  content: string;
}

export type CheckerType = "TOKENS" | "FLOAT_ABS_1E_3" | "FLOAT_ABS_1E_4" | "CSP_GROUP_COUNT" | "CSP_GROUP_PARTITION";

export interface TestCaseEntry {
  input: string;
  output: string;
  score: number;
  subtaskKey: string | null;
  checkerType?: CheckerType;
}

export interface SubtaskEntry {
  key: string;
  label: string;
  score: number;
}

export interface ProblemCreateRequest {
  code: string;
  title: string;
  sourceBatch: string;
  sourceYear?: number | null;
  sourcePosition?: number | null;
  sourceUrl?: string | null;
  difficulty: Difficulty;
  tags: string[];
  timeLimitMs: number;
  memoryLimitMb: number;
  outputLimitKb: number;
  evaluationType: EvaluationType;
  constructionStatus: ConstructionStatus;
  license: string;
  statement?: string | null;
  inputDescription?: string | null;
  outputDescription?: string | null;
  constraintsDescription: string;
  scoringNotes: string;
  samples: { input: string; output: string; checkerType?: CheckerType }[];
  testCases: TestCaseEntry[];
  subtasks: SubtaskEntry[];
  assets: AssetEntry[];
  validationReport?: string | null;
}
