"use client";

import { clsx } from "clsx";
import { forwardRef, type InputHTMLAttributes } from "react";

type InputVariant = "default" | "ghost";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  variant?: InputVariant;
  label?: string;
  error?: string;
  inputClassName?: string;
};

const variantClass: Record<InputVariant, string> = {
  default:
    "border-[var(--outline-variant)] bg-[var(--surface-lowest)] text-[var(--on-surface)] shadow-[inset_0_1px_2px_rgba(0,0,0,0.2)] focus:border-[var(--accent)] focus:shadow-[inset_0_1px_2px_rgba(0,0,0,0.2),0_0_0_2px_rgba(107,92,255,0.15)]",
  ghost:
    "border-transparent bg-transparent text-[var(--on-surface)] focus:border-[var(--outline-variant)] focus:shadow-[0_0_0_2px_rgba(107,92,255,0.1)]",
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant = "default", label, error, inputClassName, id, disabled, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className={clsx("flex flex-col gap-1.5", className)}>
        {label && (
          <label htmlFor={inputId} className="label-caps text-[var(--muted-dim)]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          disabled={disabled}
          className={clsx(
            "h-8 rounded-[5px] border px-3 text-[13px] outline-none transition-all duration-150 placeholder:text-[var(--muted-dim)] disabled:cursor-not-allowed disabled:opacity-40",
            variantClass[variant],
            error && "border-[var(--error)] focus:border-[var(--error)] focus:shadow-[0_0_0_2px_rgba(255,77,79,0.15)]",
            inputClassName,
          )}
          {...props}
        />
        {error && (
          <p className="flex items-center gap-1 text-[11px] text-[var(--error)]">
            <span className="inline-block size-1 rounded-full bg-[var(--error)]" />
            {error}
          </p>
        )}
      </div>
    );
  },
);

Input.displayName = "Input";
