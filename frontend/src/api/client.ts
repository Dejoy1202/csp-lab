const API_BASE = "/api";
let csrfToken: string | null = null;
let csrfPromise: Promise<string> | null = null;
let sessionEpoch = 0;
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export function resetSessionRequests() {
  sessionEpoch++;
  csrfToken = null;
  csrfPromise = null;
  localStorage.removeItem("csp-lab-api-key");
}
async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let body: { code?: string; message?: string } = {};
    try {
      body = await res.json();
    } catch {
      /* empty response */
    }
    if (res.status === 401 && !res.url.includes("/auth/login"))
      window.dispatchEvent(new Event("csp-lab-unauthorized"));
    throw new ApiError(
      res.status,
      body.code || "ERROR",
      body.message || "请求失败，请重试",
    );
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
async function csrf() {
  if (csrfToken) return csrfToken;
  if (!csrfPromise)
    csrfPromise = fetch(API_BASE + "/auth/csrf", { credentials: "same-origin" })
      .then(handleResponse<{ token: string }>)
      .then((r) => (csrfToken = r.token))
      .finally(() => {
        csrfPromise = null;
      });
  return csrfPromise;
}
async function mutate<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const epoch = sessionEpoch;
  const token = await csrf();
  if (epoch !== sessionEpoch)
    throw new ApiError(401, "SESSION_CHANGED", "登录状态已改变，请重试");
  const h: Record<string, string> = { "X-CSRF-TOKEN": token };
  const form = body instanceof FormData;
  if (!form) h["Content-Type"] = "application/json";
  const res = await fetch(API_BASE + path, {
    method,
    credentials: "same-origin",
    headers: h,
    body: form ? body : body === undefined ? undefined : JSON.stringify(body),
  });
  return handleResponse<T>(res);
}
export const api = {
  async get<T>(
    path: string,
    params?: Record<string, string | number | boolean | undefined | null>,
  ): Promise<T> {
    const url = new URL(API_BASE + path, window.location.origin);
    for (const [k, v] of Object.entries(params || {}))
      if (v !== undefined && v !== null && v !== "")
        url.searchParams.set(k, String(v));
    return handleResponse<T>(await fetch(url, { credentials: "same-origin" }));
  },
  post: <T>(path: string, body?: unknown) => mutate<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => mutate<T>("PUT", path, body),
  delete: <T>(path: string) => mutate<T>("DELETE", path),
  upload: <T>(path: string, file: File, fieldName = "file") => {
    const form = new FormData();
    form.append(fieldName, file);
    return mutate<T>("POST", path, form);
  },
};
