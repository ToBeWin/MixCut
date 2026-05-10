import { clsx } from "clsx";

type BadgeTone = "cyan" | "amber" | "gray" | "green" | "red";

const toneClass: Record<BadgeTone, string> = {
  cyan: "border-[rgba(0,240,255,0.38)] bg-[rgba(0,240,255,0.12)] text-[var(--cyan)]",
  amber: "border-[rgba(254,183,0,0.38)] bg-[rgba(254,183,0,0.12)] text-[var(--amber-soft)]",
  gray: "border-[var(--outline-variant)] bg-[var(--surface-container)] text-[var(--muted)]",
  green: "border-[rgba(110,231,168,0.35)] bg-[rgba(110,231,168,0.12)] text-[var(--ok)]",
  red: "border-[rgba(255,180,171,0.35)] bg-[rgba(255,180,171,0.12)] text-[var(--error)]",
};

export function Badge({
  children,
  tone = "gray",
  className,
}: {
  children: React.ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "label-caps inline-flex h-5 items-center gap-1 rounded-[4px] border px-2",
        toneClass[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
