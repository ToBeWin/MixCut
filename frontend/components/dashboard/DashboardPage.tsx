'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowDownAZ, ArrowDownUp, Clock, Filter, Plus, MoreVertical } from 'lucide-react'
import { useProjects } from '@/hooks/queries'
import { AppShell } from '@/components/layout/AppShell'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { NewProjectModal } from '@/components/dashboard/NewProjectModal'
import { useI18n } from '@/lib/i18n'
import { type Project } from '@/lib/api'

type SortKey = 'updated' | 'name'
type FilterStatus = 'all' | 'active' | 'completed'

const STATUS_COLORS: Record<string, string> = {
  active: 'text-[var(--cyan)] bg-[rgba(0,240,255,0.12)]',
  completed: 'text-green-400 bg-[rgba(82,196,26,0.12)]',
  draft: 'text-[var(--muted)] bg-[var(--surface-high)]',
  archived: 'text-[var(--text-tertiary)] bg-[var(--surface-low)]',
}

export function DashboardPage() {
  const [showNewProject, setShowNewProject] = useState(false)
  const [sortBy, setSortBy] = useState<SortKey>('updated')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')
  const { locale, t } = useI18n()
  const { data, isLoading } = useProjects()

  const projects = (data?.projects ?? [])
    .filter((p) => {
      if (filterStatus === 'all') return true
      if (filterStatus === 'active') return p.status === 'active'
      return p.status === 'completed'
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })

  return (
    <AppShell>
      <div className="flex h-full flex-col bg-[var(--surface-lowest)]">
        <header className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-6 py-4">
          <div>
            <h1 className="text-[20px] font-semibold tracking-tight text-[var(--on-surface)]">{t('dashboard.title')}</h1>
            <p className="mt-0.5 text-[12px] text-[var(--muted)]">{t('dashboard.subtitle')}</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Filter */}
            <div className="flex items-center gap-0.5 rounded-[5px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] p-0.5">
              {(['all', 'active', 'completed'] as FilterStatus[]).map((s) => (
                <button
                  key={s}
                  className={`rounded-[4px] px-2.5 py-1 text-[11px] font-medium transition-all duration-150 ${
                    filterStatus === s
                      ? 'bg-[var(--accent)]/10 text-[var(--accent)] shadow-[0_0_0_1px_rgba(107,92,255,0.15)]'
                      : 'text-[var(--muted)] hover:text-[var(--on-surface)]'
                  }`}
                  onClick={() => setFilterStatus(s)}
                >
                  {s === 'all' ? 'All' : s === 'active' ? 'Active' : 'Done'}
                </button>
              ))}
            </div>
            {/* Sort */}
            <button
              className="flex items-center gap-1.5 rounded-[5px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] px-2.5 py-1.5 text-[11px] font-medium text-[var(--muted)] transition-all duration-150 hover:text-[var(--on-surface)] active:scale-[0.97]"
              onClick={() => setSortBy((s) => (s === 'updated' ? 'name' : 'updated'))}
            >
              <ArrowDownUp className="size-3" />
              {sortBy === 'updated' ? 'Recent' : 'Name'}
            </button>
            <Button variant="primary" size="sm" icon={<Plus className="size-3.5" />} onClick={() => setShowNewProject(true)}>
              {t('dashboard.newProject')}
            </Button>
          </div>
        </header>
        <section className="flex-1 overflow-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="shimmer h-8 w-32 rounded-[4px]" />
            </div>
          ) : projects.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="flex size-16 items-center justify-center rounded-[8px] border border-[var(--border)] bg-[var(--surface)]">
                <Plus className="size-7 text-[var(--muted)]/50" />
              </div>
              <p className="mt-4 text-[15px] font-semibold text-[var(--on-surface)]">{t('dashboard.emptyTitle')}</p>
              <p className="mt-1 text-[12px] text-[var(--muted)]">{t('dashboard.emptyDescription')}</p>
              <Button className="mt-4" variant="primary" icon={<Plus className="size-4" />} onClick={() => setShowNewProject(true)}>
                {t('dashboard.newProject')}
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-3">
              {projects.map((project: Project) => (
                <Link
                  key={project.id}
                  href={`/project/${project.id}`}
                  className="group overflow-hidden rounded-[6px] border border-[var(--border)] bg-[var(--surface)] transition-all duration-150 hover:border-[var(--accent)]/40 hover:shadow-[0_0_0_1px_rgba(107,92,255,0.1),0_4px_12px_rgba(0,0,0,0.2)]"
                >
                  <div className="relative aspect-video overflow-hidden bg-[var(--surface-lowest)]">
                    <div className="flex h-full items-center justify-center">
                      <span className="mono text-[10px] text-[var(--muted)]/50">{project.status}</span>
                    </div>
                    <div className="absolute right-2 top-2">
                      <Badge tone={project.status === 'completed' ? 'green' : project.status === 'active' ? 'cyan' : 'gray'}>{project.status}</Badge>
                    </div>
                  </div>
                  <div className="p-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <h2 className="truncate text-[13px] font-semibold text-[var(--on-surface)]">{project.name}</h2>
                      <MoreVertical className="size-3.5 shrink-0 text-[var(--muted)] opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-[var(--muted)]">
                      <span className="flex items-center gap-1.5">
                        <span className={`size-1.5 rounded-full ${project.status === 'active' ? 'bg-[var(--cyan)]' : project.status === 'completed' ? 'bg-green-400' : 'bg-[var(--muted)]/50'}`} />
                        {project.status}
                      </span>
                      <span>{new Date(project.updated_at).toLocaleDateString(locale)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
      <NewProjectModal open={showNewProject} onClose={() => setShowNewProject(false)} />
    </AppShell>
  )
}
