import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import "./LoginPage.css";
export function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [register, setRegister] = useState(false);
  const [show, setShow] = useState(false);
  const [localError, setLocalError] = useState("");
  const { login, isLoading, error, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useThemeStore();
  if (isAuthenticated) return <Navigate to="/" replace />;
  return (
    <div className="login-root">
      <header className="login-top">
        <span className="app-brand">
          <span className="brand-mark">
            C<span>_</span>
          </span>
          <strong>CSP Lab</strong>
        </span>
        <button onClick={toggleTheme}>
          {theme === "light" ? "深色模式" : "浅色模式"}
        </button>
      </header>
      <div className="login-main">
        <div className="login-intro">
          <span className="login-caption">CCF-CSP · 模拟考试</span>
          <h1>
            给自己一场
            <br />
            完整的模拟。
          </h1>
          <p>
            选择历届试卷，留出四小时。
            <br />
            从第一题到第五题，专注完成每一次作答。
          </p>
          <div className="login-facts">
            <span>
              <b>4</b> 小时
            </span>
            <span>
              <b>5</b> 道题
            </span>
            <span>
              <b>500</b> 分
            </span>
          </div>
        </div>
        <section className="login-form-panel">
          <h2>{register ? "创建账号" : "欢迎回来"}</h2>
          <p className="text-muted">
            {register
              ? "保存你的代码、提交与每次考试成绩。"
              : "登录，继续你的 CSP 模拟考试。"}
          </p>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setLocalError("");
              if (register && password !== confirm) {
                setLocalError("两次密码不一致");
                return;
              }
              if (await login(username.trim(), password, register))
                navigate("/");
            }}
          >
            <label htmlFor="username">用户名</label>
            <input
              id="username"
              autoComplete="username"
              required
              minLength={3}
              maxLength={32}
              pattern="[A-Za-z0-9_]{3,32}"
              placeholder="3–32 位字母、数字或下划线"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
            />
            <label htmlFor="password">密码</label>
            <div className="password-input">
              <input
                id="password"
                type={show ? "text" : "password"}
                autoComplete={register ? "new-password" : "current-password"}
                required
                minLength={8}
                maxLength={72}
                placeholder="至少 8 个字符"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShow(!show)}
                aria-label={show ? "隐藏密码" : "显示密码"}
              >
                {show ? "隐藏" : "显示"}
              </button>
            </div>
            {register && (
              <>
                <label htmlFor="confirm-password">确认密码</label>
                <input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                />
              </>
            )}
            {(localError || error) && (
              <p role="alert" className="login-error">
                {localError || error}
              </p>
            )}
            <button
              className="btn btn-primary login-submit"
              disabled={isLoading}
            >
              {isLoading ? "正在验证…" : register ? "注册并进入" : "登录"}
            </button>
          </form>
          <p className="switch-auth">
            {register ? "已有账号？" : "还没有账号？"}
            <button
              onClick={() => {
                setRegister(!register);
                setLocalError("");
                useAuthStore.setState({ error: null });
              }}
            >
              {register ? "返回登录" : "创建账号"}
            </button>
          </p>
        </section>
      </div>
      <footer className="login-bottom">
        独立判题 · 本站模拟评分，非官方认证成绩
      </footer>
    </div>
  );
}
