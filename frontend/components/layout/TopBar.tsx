"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Play, Search, Settings } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/lib/i18n";

export function TopBar() {
  const pathname = usePathname();
  const { locale, setLocale, t } = useI18n();
  const menuItems = [
    t("topbar.file"),
    t("topbar.edit"),
    t("topbar.sequence"),
    t("topbar.view"),
    t("topbar.help"),
  ] as const;

  return (
    <header className="fixed left-0 right-0 top-0 z-50 flex h-12 items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-3">
      <div className="flex min-w-0 items-center gap-5">
        <Link href="/dashboard" className="text-[20px] font-bold leading-none tracking-tight text-[var(--accent)]">
          MixCut
        </Link>
        <nav className="flex h-12 items-center gap-0.5">
          {menuItems.map((item) => (
            <button
              key={item}
              type="button"
              className={
                item === t("topbar.sequence") && pathname.startsWith("/project")
                  ? "h-12 border-b-2 border-[var(--accent)] px-2.5 text-[12px] font-semibold text-[var(--accent)]"
                  : "rounded-[4px] px-2.5 py-1 text-[12px] font-medium text-[var(--muted)] transition-colors hover:bg-[var(--surface-container)] hover:text-[var(--on-surface)]"
              }
            >
              {item}
            </button>
          ))}
        </nav>
      </div>
      <div className="flex items-center gap-2">
        <label className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-[var(--muted-dim)]" />
          <input
            className="h-7 w-48 rounded-[5px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] pl-8 pr-3 text-[11px] text-[var(--on-surface)] outline-none transition-all duration-150 placeholder:text-[var(--muted-dim)] focus:border-[var(--accent)] focus:shadow-[0_0_0_2px_rgba(107,92,255,0.12)]"
            placeholder={t("topbar.search")}
          />
        </label>
        <div className="flex items-center gap-0.5 rounded-[5px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] p-0.5">
          <button
            type="button"
            className={`rounded-[4px] px-2 py-0.5 text-[10px] font-semibold transition-all duration-150 ${
              locale === "zh-CN" ? "bg-[var(--accent)]/10 text-[var(--accent)]" : "text-[var(--muted)] hover:text-[var(--on-surface)]"
            }`}
            onClick={() => setLocale("zh-CN")}
            aria-label={t("topbar.locale.zh")}
          >
            中
          </button>
          <button
            type="button"
            className={`rounded-[4px] px-2 py-0.5 text-[10px] font-semibold transition-all duration-150 ${
              locale === "en-US" ? "bg-[var(--accent)]/10 text-[var(--accent)]" : "text-[var(--muted)] hover:text-[var(--on-surface)]"
            }`}
            onClick={() => setLocale("en-US")}
            aria-label={t("topbar.locale.en")}
          >
            EN
          </button>
        </div>
        <div className="flex items-center gap-0.5 border-r border-[var(--outline-variant)] pr-2">
          {[Play, Settings, Bell].map((Icon, index) => (
            <button
              key={index}
              type="button"
              className="flex size-7 items-center justify-center rounded-[4px] text-[var(--muted)] transition-colors hover:bg-[var(--surface-container)] hover:text-[var(--on-surface)]"
              aria-label={Icon.displayName ?? "toolbar action"}
            >
              <Icon className="size-3.5" strokeWidth={1.7} />
            </button>
          ))}
        </div>
        <Button variant="primary" size="sm">
          {t("common.export")}
        </Button>
      </div>
    </header>
  );
}
