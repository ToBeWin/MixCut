"use client";

import { clsx } from "clsx";

type ProgressVariant = "default" | "accent" | "success";

type ProgressProps = {
  value: number;
  label?: string;
  variant?: ProgressVariant;
  className?: string;
};

const variantBarClass: Record<ProgressVariant, string> = {
  default: "bg-[var(--cyan)]",
  accent: "bg-gradient-to-r from-[var(--accent)] to-[var(--accent-hover)]",
  success: "bg-[var(--ok)]",
};

export function Progress({ value, label, variant = "default", className }: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className={clsx("flex flex-col gap-1.5", className)}>
      {label && (
        <div className="flex items-center justify-between">
          <span className="label-caps text-[var(--muted-dim)]">{label}</span>
          <span className="mono tabular-nums text-[10px] text-[var(--muted)]">{Math.round(clamped)}%</span>
        </div>
      )}
      <div
        className="h-1 w-full overflow-hidden rounded-full bg-[var(--outline-variant)]/60"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div
          className={clsx(
            "h-full rounded-full transition-[width] duration-300 ease-out",
            variantBarClass[variant],
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}