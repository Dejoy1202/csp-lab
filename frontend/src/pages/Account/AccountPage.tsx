import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, resetSessionRequests } from "../../api/client";
import { useAuthStore } from "../../store/authStore";
export function AccountPage() {
  const user = useAuthStore((s) => s.user);
  const [previous, setPrevious] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  return (
    <section className="account-page">
      <h1>账号设置</h1>
      <p className="text-muted">
        {user?.username} · {user?.role === "ADMIN" ? "管理员" : "普通用户"}
      </p>
      <h2>修改密码</h2>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (next !== confirm) {
            setError("两次新密码不一致");
            return;
          }
          setBusy(true);
          setError("");
          try {
            await api.post("/auth/password", {
              previousPassword: previous,
              newPassword: next,
            });
            resetSessionRequests();
            useAuthStore.setState({
              user: null,
              isAuthenticated: false,
              error: null,
            });
            navigate("/login");
          } catch (e) {
            setError(e instanceof Error ? e.message : "修改失败");
          } finally {
            setBusy(false);
          }
        }}
      >
        <label htmlFor="previous-password">当前密码</label>
        <input
          id="previous-password"
          type="password"
          autoComplete="current-password"
          required
          value={previous}
          onChange={(e) => setPrevious(e.target.value)}
        />
        <label htmlFor="new-password">新密码</label>
        <input
          id="new-password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={72}
          value={next}
          onChange={(e) => setNext(e.target.value)}
        />
        <label htmlFor="confirm-new-password">确认新密码</label>
        <input
          id="confirm-new-password"
          type="password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
        />
        {error && (
          <p role="alert" className="login-error">
            {error}
          </p>
        )}
        <p className="text-muted">修改成功后，请使用新密码重新登录。</p>
        <button className="btn btn-primary" disabled={busy}>
          {busy ? "正在保存…" : "更新密码"}
        </button>
      </form>
    </section>
  );
}
