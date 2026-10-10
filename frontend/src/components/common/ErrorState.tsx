import React from "react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "加载失败",
  message = "网络请求出现问题，请检查网络或后端服务。",
  onRetry,
}) => {
  return (
    <div
      style={{
        padding: "48px 24px",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "12px",
      }}
    >
      <div style={{ fontSize: "2.5rem" }}>⚠️</div>
      <div
        style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--error)" }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: "0.875rem",
          color: "var(--text-secondary)",
          maxWidth: "420px",
          lineHeight: 1.5,
        }}
      >
        {message}
      </div>
      {onRetry && (
        <button
          className="btn btn-secondary btn-sm"
          onClick={onRetry}
          style={{ marginTop: "12px" }}
        >
          重试
        </button>
      )}
    </div>
  );
};
