"use client";

import { useEffect, useState } from "react";

export type ToastVariant = "success" | "error" | "warning" | "info";

export interface ToastData {
  id: string;
  message: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastProps {
  toast: ToastData;
  onDismiss: (id: string) => void;
}

const variantStyles: Record<ToastVariant, string> = {
  success: "bg-support-success text-white",
  error: "bg-support-danger text-white",
  warning: "bg-support-warning text-white",
  info: "bg-support-primary text-white",
};

export function Toast({ toast, onDismiss }: ToastProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const showTimer = setTimeout(() => setVisible(true), 10);
    const dismissTimer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onDismiss(toast.id), 300);
    }, toast.duration ?? 4000);
    return () => {
      clearTimeout(showTimer);
      clearTimeout(dismissTimer);
    };
  }, [toast, onDismiss]);

  return (
    <div
      className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm shadow-lg transition-all duration-300 ${
        variantStyles[toast.variant ?? "info"]
      } ${visible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"}`}
    >
      <span className="flex-1">{toast.message}</span>
      <button
        onClick={() => {
          setVisible(false);
          setTimeout(() => onDismiss(toast.id), 300);
        }}
        className="text-white/80 hover:text-white cursor-pointer"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
}
