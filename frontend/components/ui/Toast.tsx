"use client";

import { clsx } from "clsx";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Check, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

type Toast = {
  id: string;
  message: string;
  type: ToastType;
};

type ToastItemProps = {
  toast: Toast;
  onDismiss: (id: string) => void;
};

const typeConfig: Record<ToastType, { icon: typeof Check; borderClass: string; iconClass: string }> = {
  success: {
    icon: Check,
    borderClass: "border-l-[var(--ok)]",
    iconClass: "text-[var(--ok)]",
  },
  error: {
    icon: X,
    borderClass: "border-l-[var(--error)]",
    iconClass: "text-[var(--error)]",
  },
  info: {
    icon: Info,
    borderClass: "border-l-[var(--cyan)]",
    iconClass: "text-[var(--cyan)]",
  },
};

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const { icon: Icon, borderClass, iconClass } = typeConfig[toast.type];

  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), 5000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <div
      className={clsx(
        "flex w-80 items-start gap-3 rounded-[6px] border border-[var(--border)] border-l-2 bg-[var(--surface-container)] px-4 py-3 shadow-[0_8px_24px_rgba(0,0,0,0.3)] animate-[slideInRight_150ms_ease-out]",
        borderClass,
      )}
      role="alert"
    >
      <Icon size={15} className={clsx("mt-0.5 shrink-0", iconClass)} />
      <p className="flex-1 text-[12px] leading-5 text-[var(--on-surface)]">{toast.message}</p>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 text-[var(--muted)] transition-colors hover:text-[var(--on-surface)]"
        aria-label="Dismiss"
      >
        <X size={13} />
      </button>
    </div>
  );
}

type ToastContextValue = {
  addToast: (message: string, type?: ToastType) => void;
};

import { createContext, useContext } from "react";

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a ToastProvider");
  return ctx;
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: ToastType = "info") => {
    const id = `toast-${nextId++}`;
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed right-4 top-4 z-[100] flex flex-col gap-2">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}