import { useCallback, useEffect, useRef, useState } from "react";
import { getDraft, saveDraft } from "../api/endpoints";
import { ApiError } from "../api/client";
import { useAuthStore } from "../store/authStore";
import { DEFAULT_CPP_CODE } from "../editor/defaultCode";

type SaveStatus = "saved" | "saving" | "unsaved" | "conflict";
interface DraftActions {
  change: (value: string) => void;
  save: () => Promise<void>;
  resolve: (keepLocal: boolean) => Promise<void>;
}

// Serialize writes and preserve pending edits in this tab across reloads.
export function useDraft(problemId: number | null) {
  const userId = useAuthStore((s) => s.user?.id);
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<SaveStatus>("saved");
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const actions = useRef<DraftActions | null>(null);

  useEffect(() => {
    setReady(false);
    setCode("");
    setError(null);
    if (!problemId || !userId) {
      actions.current = null;
      return;
    }
    const key = `csp-lab-pending-draft:${userId}:${problemId}`;
    let disposed = false,
      loaded = false,
      dirty = false,
      conflict = false;
    let currentCode = "",
      revision = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let writing: Promise<void> | null = null;
    const update = (next: SaveStatus) => {
      if (!disposed) setStatus(next);
    };
    const backup = () => {
      try {
        sessionStorage.setItem(
          key,
          JSON.stringify({ sourceCode: currentCode, revision }),
        );
      } catch {
        /* Server saving still works if browser storage is unavailable. */
      }
    };
    const save = async (): Promise<void> => {
      if (timer) clearTimeout(timer);
      if (writing) return writing;
      if (
        !loaded ||
        !dirty ||
        conflict ||
        useAuthStore.getState().user?.id !== userId
      )
        return;
      writing = (async () => {
        while (dirty && !conflict) {
          const snapshot = currentCode;
          update("saving");
          try {
            const saved = await saveDraft(problemId, {
              sourceCode: snapshot,
              revision,
            });
            revision = saved.revision;
            dirty = snapshot !== currentCode;
            if (dirty) backup();
            else {
              sessionStorage.removeItem(key);
              update("saved");
            }
            if (!disposed) setError(null);
          } catch (err) {
            conflict = err instanceof ApiError && err.status === 409;
            update(conflict ? "conflict" : "unsaved");
            if (!disposed)
              setError(err instanceof Error ? err.message : "草稿保存失败");
            break;
          }
        }
      })();
      await writing;
      writing = null;
    };
    const change = (value: string) => {
      if (!loaded) return;
      currentCode = value;
      dirty = true;
      setCode(value);
      backup();
      update(conflict ? "conflict" : "unsaved");
      if (timer) clearTimeout(timer);
      if (!conflict)
        timer = setTimeout(() => {
          void save();
        }, 1500);
    };
    const resolve = async (keepLocal: boolean) => {
      try {
        if (writing) await writing;
        const server = await getDraft(problemId);
        if (disposed) return;
        revision = server.revision;
        conflict = false;
        setError(null);
        if (keepLocal) {
          dirty = true;
          backup();
          await save();
        } else {
          currentCode = server.sourceCode;
          dirty = false;
          sessionStorage.removeItem(key);
          setCode(currentCode);
          update("saved");
        }
      } catch (err) {
        if (!disposed)
          setError(err instanceof Error ? err.message : "读取服务端草稿失败");
      }
    };
    actions.current = { change, save, resolve };
    void (async () => {
      try {
        const draft = await getDraft(problemId);
        if (disposed) return;
        revision = draft.revision;
        currentCode = revision === 0 ? DEFAULT_CPP_CODE : draft.sourceCode;
        let pending: { sourceCode: string; revision: number } | null = null;
        try {
          pending = JSON.parse(sessionStorage.getItem(key) || "null");
        } catch {
          /* Ignore malformed local backup. */
        }
        if (
          pending &&
          typeof pending.sourceCode === "string" &&
          Number.isInteger(pending.revision)
        ) {
          currentCode = pending.sourceCode;
          dirty = currentCode !== draft.sourceCode;
          conflict = dirty && pending.revision !== revision;
        }
        loaded = true;
        setCode(currentCode);
        setReady(true);
        update(conflict ? "conflict" : dirty ? "unsaved" : "saved");
        if (dirty && !conflict) void save();
      } catch (err) {
        if (!disposed)
          setError(
            err instanceof Error ? err.message : "草稿读取失败，请刷新重试",
          );
      }
    })();
    return () => {
      if (timer) clearTimeout(timer);
      void save();
      disposed = true;
      actions.current = null;
    };
  }, [problemId, userId]);

  const changeCode = useCallback(
    (value?: string) => actions.current?.change(value ?? ""),
    [],
  );
  const saveNow = useCallback(async () => {
    await actions.current?.save();
  }, []);
  const resolveConflict = useCallback(async (keepLocal: boolean) => {
    await actions.current?.resolve(keepLocal);
  }, []);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void saveNow();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [saveNow]);
  return { code, changeCode, saveNow, resolveConflict, ready, status, error };
}
