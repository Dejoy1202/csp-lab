import { useState, useEffect, useRef, useCallback } from "react";
import { getSubmission } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { Submission, SubmissionStatus } from "../types";

const TERMINAL_STATUSES: SubmissionStatus[] = [
  "AC",
  "WA",
  "TLE",
  "MLE",
  "RE",
  "CE",
  "OLE",
  "SYSTEM_ERROR",
];

export function usePolling(submissionId: number | null) {
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const generation = useRef(0);

  const stopPolling = useCallback(() => {
    generation.current++;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setIsPolling(false);
  }, []);

  useEffect(() => {
    const current = ++generation.current;
    setSubmission(null);
    setError(null);
    if (!submissionId) {
      stopPolling();
      return;
    }

    setIsPolling(true);
    setError(null);

    const poll = async () => {
      try {
        const data = await getSubmission(submissionId);
        if (current !== generation.current) return;
        setSubmission(data);
        setError(null);

        if (TERMINAL_STATUSES.includes(data.status)) {
          setIsPolling(false);
          return;
        }

        timerRef.current = setTimeout(poll, 800);
      } catch (err) {
        if (current !== generation.current) return;
        setError(err instanceof Error ? err.message : "查询提交状态失败");
        if (err instanceof ApiError && [401, 403, 404].includes(err.status)) {
          setIsPolling(false);
          return;
        }
        timerRef.current = setTimeout(poll, 2000);
      }
    };

    poll();

    return () => {
      generation.current++;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [submissionId, stopPolling]);

  return { submission, isPolling, error, stopPolling };
}
