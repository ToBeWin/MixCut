import { clsx } from "clsx";

type PanelProps = {
  title?: string;
  eyebrow?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
};

export function Panel({ title, eyebrow, action, children, className, bodyClassName }: PanelProps) {
  return (
    <section className={clsx("panel flex min-h-0 flex-col overflow-hidden rounded-[6px]", className)}>
      {(title || eyebrow || action) && (
        <header className="flex min-h-10 items-center justify-between border-b border-[var(--border)] px-3 py-2">
          <div className="min-w-0">
            {eyebrow && <p className="label-caps mb-0.5 text-[var(--muted-dim)]">{eyebrow}</p>}
            {title && <h2 className="truncate text-[13px] font-semibold tracking-tight text-[var(--on-surface)]">{title}</h2>}
          </div>
          {action}
        </header>
      )}
      <div className={clsx("min-h-0 flex-1", bodyClassName)}>{children}</div>
    </section>
  );
}
