import React from "react";
import "./Loading.css";

interface LoadingProps {
  text?: string;
  size?: "sm" | "md" | "lg";
  fullScreen?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({
  text = "加载中...",
  size = "md",
  fullScreen = false,
}) => {
  return (
    <div
      className={`loading-container ${fullScreen ? "fullscreen" : ""} size-${size}`}
    >
      <div className="loading-spinner" />
      {text && <span className="loading-text">{text}</span>}
    </div>
  );
};
