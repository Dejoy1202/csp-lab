import React from "react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "暂无数据",
  description,
  action,
}) => {
  return (
    <div
      style={{
        padding: "48px 24px",
        textAlign: "center",
        color: "var(--text-tertiary)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "12px",
      }}
    >
      <div style={{ fontSize: "3rem", opacity: 0.5 }}>📭</div>
      <div
        style={{
          fontSize: "1rem",
          fontWeight: 500,
          color: "var(--text-secondary)",
        }}
      >
        {title}
      </div>
      {description && (
        <div
          style={{ fontSize: "0.875rem", maxWidth: "400px", lineHeight: 1.5 }}
        >
          {description}
        </div>
      )}
      {action && <div style={{ marginTop: "8px" }}>{action}</div>}
    </div>
  );
};
