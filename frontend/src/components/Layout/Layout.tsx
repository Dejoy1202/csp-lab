import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { toast } from "../common/Toast";
import "./Layout.css";
export function Layout() {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="app-brand" aria-label="CSP Lab 模拟考试首页">
          <span className="brand-mark">
            C<span>_</span>
          </span>
          <strong>CSP Lab</strong>
        </NavLink>
        <nav aria-label="主导航">
          <NavLink to="/" end>
            模拟考试
          </NavLink>
          <NavLink to="/history">考试记录</NavLink>
          {user?.role === "ADMIN" && <NavLink to="/admin">题库管理</NavLink>}
        </nav>
        <div className="header-tools">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={theme === "light" ? "切换深色模式" : "切换浅色模式"}
          >
            {theme === "light" ? "深色" : "浅色"}
          </button>
          <NavLink to="/account" className="account-name">
            {user?.displayName}
          </NavLink>
          <button
            onClick={() => {
              void logout().catch((e) => toast.error(e.message));
            }}
          >
            退出
          </button>
        </div>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
