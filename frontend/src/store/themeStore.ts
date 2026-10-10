import { create } from "zustand";
type Theme = "light" | "dark";
const stored = localStorage.getItem("csp-theme");
export const useThemeStore = create<{ theme: Theme; toggleTheme: () => void }>(
  (set) => ({
    theme: stored === '"dark"' ? "dark" : "light",
    toggleTheme: () =>
      set((s) => {
        const theme = s.theme === "light" ? "dark" : "light";
        localStorage.setItem("csp-theme", JSON.stringify(theme));
        return { theme };
      }),
  }),
);
