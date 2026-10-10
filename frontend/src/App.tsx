import React, { useEffect, lazy, Suspense } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useParams,
} from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { useThemeStore } from "./store/themeStore";
import { Layout } from "./components/Layout/Layout";
import { LoginPage } from "./pages/Login/LoginPage";
import { AccountPage } from "./pages/Account/AccountPage";
import { ExamLobby } from "./pages/Exam/ExamLobby";
import { Loading } from "./components/common/Loading";
import { ToastContainer } from "./components/common/Toast";
import "./index.css";
const ExamPage = lazy(() =>
  import("./pages/Exam/ExamPage").then((m) => ({ default: m.ExamPage })),
);
const ExamHistory = lazy(() =>
  import("./pages/Exam/ExamHistory").then((m) => ({ default: m.ExamHistory })),
);
const AdminPage = lazy(() =>
  import("./pages/Admin/AdminPage").then((m) => ({ default: m.AdminPage })),
);
function Protected({
  children,
  admin = false,
}: {
  children: React.ReactNode;
  admin?: boolean;
}) {
  const a = useAuthStore();
  if (!a.initialized) return <Loading text="正在读取登录状态…" />;
  if (!a.isAuthenticated) return <Navigate to="/login" replace />;
  if (admin && a.user?.role !== "ADMIN") return <Navigate to="/" replace />;
  return children;
}
function ExamRoute() {
  const { id } = useParams();
  return <ExamPage key={id} />;
}
export default function App() {
  const initialize = useAuthStore((s) => s.initialize);
  const theme = useThemeStore((s) => s.theme);
  useEffect(() => {
    void initialize();
    const expired = () =>
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
        initialized: true,
      });
    window.addEventListener("csp-lab-unauthorized", expired);
    return () => window.removeEventListener("csp-lab-unauthorized", expired);
  }, [initialize]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  return (
    <BrowserRouter>
      <Suspense fallback={<Loading text="正在加载页面…" />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <Protected>
                <Layout />
              </Protected>
            }
          >
            <Route index element={<ExamLobby />} />
            <Route path="exam" element={<Navigate to="/" replace />} />
            <Route path="exam/:id" element={<ExamRoute />} />
            <Route path="account" element={<AccountPage />} />
            <Route path="history" element={<ExamHistory />} />
            <Route
              path="admin"
              element={
                <Protected admin>
                  <AdminPage />
                </Protected>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
      <ToastContainer />
    </BrowserRouter>
  );
}
