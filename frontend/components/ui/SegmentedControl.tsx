"use client";

import { clsx } from "clsx";

export function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: readonly T[];
  onChange: (value: T) => void;
}) {
  return (
    <div className="inline-flex rounded-[5px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] p-0.5">
      {options.map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={clsx(
            "h-7 rounded-[4px] px-2.5 text-[11px] font-medium transition-all duration-150",
            option === value
              ? "bg-[var(--accent)]/10 text-[var(--accent)] shadow-[0_0_0_1px_rgba(107,92,255,0.12)]"
              : "text-[var(--muted)] hover:text-[var(--on-surface)]",
          )}
        >
          {option}
        </button>
      ))}
    </div>
  );
}
