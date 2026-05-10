"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CircleHelp, UserCircle } from "lucide-react";
import { clsx } from "clsx";
import { navItems } from "@/lib/mock-data";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed bottom-0 left-0 top-12 z-40 flex w-20 flex-col items-center gap-3 border-r border-[var(--border)] bg-[var(--surface)] py-3">
      <div className="mb-1 flex flex-col items-center gap-0.5 px-2">
        <div className="flex size-8 items-center justify-center overflow-hidden rounded-full border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] text-[11px] font-bold text-[var(--accent)]">
          MC
        </div>
        <span className="max-w-16 truncate text-center text-[8px] font-bold text-[var(--muted)]/70">
          Studio
        </span>
      </div>
      <nav className="flex w-full flex-1 flex-col gap-1 px-2">
        {navItems.map((item) => {
          const active = pathname.startsWith(item.match);
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={clsx(
                "flex min-h-14 flex-col items-center justify-center gap-1 rounded-[6px] p-2 text-center transition-all duration-150",
                active
                  ? "bg-[var(--accent)]/8 text-[var(--accent)] shadow-[inset_0_1px_0_rgba(107,92,255,0.1)]"
                  : "text-[var(--muted)] hover:bg-[var(--surface-container)] hover:text-[var(--on-surface)]",
              )}
            >
              <Icon className="size-5" strokeWidth={active ? 2 : 1.7} />
              <span className="label-caps">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="flex w-full flex-col gap-1 px-2 pb-2">
        {[CircleHelp, UserCircle].map((Icon, index) => (
          <button
            key={index}
            type="button"
            className="flex min-h-10 items-center justify-center rounded-[6px] text-[var(--muted)] transition-colors hover:bg-[var(--surface-container)] hover:text-[var(--on-surface)]"
          >
            <Icon className="size-5" strokeWidth={1.7} />
          </button>
        ))}
      </div>
    </aside>
  );
}
