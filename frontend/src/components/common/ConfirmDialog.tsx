import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import "./ConfirmDialog.css";
interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "warning" | "info";
  onConfirm: () => void;
  onCancel: () => void;
}
export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "确定",
  cancelText = "取消",
  variant = "info",
  onConfirm,
  onCancel,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    if (open && !ref.current?.open) ref.current?.showModal();
    if (!open && ref.current?.open) ref.current.close();
  }, [open]);
  return createPortal(
    <dialog
      ref={ref}
      className="confirm-modal native-dialog"
      aria-labelledby={id}
      aria-describedby={id + "-message"}
      onCancel={(e) => {
        e.preventDefault();
        onCancel();
      }}
    >
      <div className="confirm-header">
        <h3 className="confirm-title" id={id}>
          {title}
        </h3>
      </div>
      <div className="confirm-body">
        <p id={id + "-message"}>{message}</p>
      </div>
      <div className="confirm-actions">
        <button autoFocus className="btn btn-secondary" onClick={onCancel}>
          {cancelText}
        </button>
        <button
          className={
            "btn " + (variant === "danger" ? "btn-danger" : "btn-primary")
          }
          onClick={onConfirm}
        >
          {confirmText}
        </button>
      </div>
    </dialog>,
    document.body,
  );
}
