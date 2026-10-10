import React, { useEffect } from "react";
import { create } from "zustand";
import "./Toast.css";

export interface ToastItem {
  id: string;
  type: "success" | "error" | "info" | "warning";
  message: string;
}

interface ToastState {
  toasts: ToastItem[];
  addToast: (message: string, type?: ToastItem["type"]) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (message, type = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    set((state) => ({
      toasts: [...state.toasts.slice(-2), { id, type, message }],
    }));
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, 3200);
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));

export const toast = {
  success: (msg: string) => useToastStore.getState().addToast(msg, "success"),
  error: (msg: string) => useToastStore.getState().addToast(msg, "error"),
  info: (msg: string) => useToastStore.getState().addToast(msg, "info"),
  warning: (msg: string) => useToastStore.getState().addToast(msg, "warning"),
};

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`toast-item toast-${t.type}`}
          onClick={() => removeToast(t.id)}
        >
          <span className="toast-icon">
            {t.type === "success" && "✓"}
            {t.type === "error" && "✕"}
            {t.type === "warning" && "!"}
            {t.type === "info" && "ℹ"}
          </span>
          <span className="toast-msg">{t.message}</span>
        </div>
      ))}
    </div>
  );
};
