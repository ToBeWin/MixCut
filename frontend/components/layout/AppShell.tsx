import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen overflow-hidden bg-[var(--background)] text-[var(--on-surface)]">
      <TopBar />
      <Sidebar />
      <main className="h-screen overflow-hidden bg-[var(--outline-variant)] pl-20 pt-12">
        {children}
      </main>
    </div>
  );
}
