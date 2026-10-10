import React from "react";
import type { SubmissionStatus } from "../../types";
import { formatStatus, getStatusColor } from "../../utils/format";
import "./StatusBadge.css";

interface StatusBadgeProps {
  status: SubmissionStatus;
  size?: "sm" | "md";
  showDot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "md",
  showDot = true,
}) => {
  const colorClass = getStatusColor(status);
  const text = formatStatus(status);
  const isPending = status === "QUEUED" || status === "RUNNING";

  return (
    <span
      className={`status-badge-root ${colorClass} size-${size} ${isPending ? "pending" : ""}`}
    >
      {showDot && (
        <span
          className={`status-dot ${status.toLowerCase()} ${isPending ? "pulsing" : ""}`}
        />
      )}
      <span className="status-label">{text}</span>
    </span>
  );
};
