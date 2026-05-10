"use client";

import { clsx } from "clsx";
import { useCallback, useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
};

export function Modal({ open, onClose, title, children, footer, className }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      const firstFocusable = dialogRef.current?.querySelector<HTMLElement>(
        'a[href], button:not([disabled]), input, textarea, select, [tabindex]:not([tabindex="-1"])',
      );
      firstFocusable?.focus();
    } else {
      previousFocusRef.current?.focus();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const focusables = dialogRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input, textarea, select, [tabindex]:not([tabindex="-1"])',
        );
        if (!focusables?.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose],
  );

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-[fadeIn_150ms_ease-out]"
        onClick={handleBackdropClick}
      />
      <div
        ref={dialogRef}
        className={clsx(
          "relative z-10 flex max-h-[85vh] w-full min-w-[320px] max-w-lg flex-col rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface-container)] shadow-[0_8px_40px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.04)] animate-[slideInUp_200ms_ease-out]",
          className,
        )}
      >
        {title && (
          <header className="flex items-center justify-between border-b border-[var(--border)] px-5 py-3.5">
            <h2 className="text-[15px] font-semibold tracking-tight text-[var(--on-surface)]">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="flex h-7 w-7 items-center justify-center rounded-[5px] text-[var(--muted)] transition-all hover:bg-[var(--surface-high)] hover:text-[var(--on-surface)]"
              aria-label="Close"
            >
              <X size={15} />
            </button>
          </header>
        )}
        {!title && (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-[5px] text-[var(--muted)] transition-all hover:bg-[var(--surface-high)] hover:text-[var(--on-surface)]"
            aria-label="Close"
          >
            <X size={15} />
          </button>
        )}
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        {footer && (
          <footer className="flex items-center justify-end gap-2 border-t border-[var(--border)] px-5 py-3">
            {footer}
          </footer>
        )}
      </div>
    </div>,
    document.body,
  );
}
