import { create } from "zustand";
import { api, ApiError, resetSessionRequests } from "../api/client";
export interface Account {
  id: number;
  username: string;
  displayName: string;
  role: "USER" | "ADMIN";
}
interface AuthState {
  user: Account | null;
  isAuthenticated: boolean;
  initialized: boolean;
  isLoading: boolean;
  error: string | null;
  initialize: () => Promise<void>;
  login: (
    username: string,
    password: string,
    register?: boolean,
  ) => Promise<boolean>;
  logout: () => Promise<void>;
}
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  initialized: false,
  isLoading: false,
  error: null,
  initialize: async () => {
    try {
      const user = await api.get<Account>("/auth/me");
      set({ user, isAuthenticated: true, initialized: true });
    } catch (e) {
      set({
        user: null,
        isAuthenticated: false,
        initialized: true,
        error:
          e instanceof ApiError && e.status === 401
            ? null
            : "服务暂时无法连接，请稍后重试",
      });
    }
  },
  login: async (username, password, register = false) => {
    set({ isLoading: true, error: null });
    resetSessionRequests();
    try {
      const user = await api.post<Account>(
        register ? "/auth/register" : "/auth/login",
        { username, password },
      );
      resetSessionRequests();
      set({ user, isAuthenticated: true, initialized: true, isLoading: false });
      return true;
    } catch (e) {
      set({
        isLoading: false,
        error: e instanceof Error ? e.message : "登录失败，请重试",
      });
      return false;
    }
  },
  logout: async () => {
    await api.post("/auth/logout");
    resetSessionRequests();
    for (const key of Object.keys(sessionStorage))
      if (key.startsWith("csp-lab-pending-draft:"))
        sessionStorage.removeItem(key);
    set({ user: null, isAuthenticated: false, error: null });
  },
}));
