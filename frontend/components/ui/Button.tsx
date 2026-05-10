import type { ButtonHTMLAttributes, ReactNode } from "react";
import { clsx } from "clsx";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
};

const variantClass: Record<ButtonVariant, string> = {
  primary:
    "border-[var(--accent)] bg-[var(--accent)] text-white shadow-[0_0_0_1px_rgba(107,92,255,0.3),0_2px_8px_rgba(107,92,255,0.2)] hover:bg-[var(--accent-hover)] hover:shadow-[0_0_0_1px_rgba(107,92,255,0.4),0_4px_16px_rgba(107,92,255,0.3)] active:shadow-[0_0_0_1px_rgba(107,92,255,0.2)]",
  secondary:
    "border-[var(--outline-variant)] bg-[var(--surface-container)] text-[var(--on-surface)] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] hover:border-[var(--accent)]/50 hover:text-[var(--accent)] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.04),0_0_0_1px_rgba(107,92,255,0.1)]",
  ghost:
    "border-transparent bg-transparent text-[var(--muted)] hover:bg-[var(--surface-container)] hover:text-[var(--on-surface)]",
  danger:
    "border-[rgba(255,77,79,0.2)] bg-[rgba(255,77,79,0.08)] text-[var(--danger)] hover:border-[rgba(255,77,79,0.4)] hover:bg-[rgba(255,77,79,0.12)]",
};

const sizeClass: Record<ButtonSize, string> = {
  sm: "h-7 gap-1.5 rounded-[4px] px-2 text-[11px]",
  md: "h-8 gap-2 rounded-[5px] px-3 text-[12px]",
  lg: "h-9 gap-2 rounded-[6px] px-4 text-[13px]",
};

export function Button({
  className,
  variant = "secondary",
  size = "md",
  icon,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={clsx(
        "inline-flex items-center justify-center font-semibold transition-all duration-150 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100",
        variantClass[variant],
        sizeClass[size],
        className,
      )}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}
