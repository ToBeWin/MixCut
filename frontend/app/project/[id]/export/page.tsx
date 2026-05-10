'use client'

import { useParams, useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { ExportPanel } from '@/components/editor/SettingsPanel'
import { Button } from '@/components/ui/Button'
import { ArrowLeft, Download } from 'lucide-react'
import { getProject, getJob, listJobs } from '@/lib/api'
import Link from 'next/link'

export default function ExportPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const projectId = (params?.id as string) || ''
  const jobIdFromUrl = searchParams?.get('job') || null

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
    enabled: !!projectId,
  })

  const { data: jobsData } = useQuery({
    queryKey: ['jobs', projectId],
    queryFn: () => listJobs(projectId),
    enabled: !!projectId && !jobIdFromUrl,
  })

  const completedJobs = jobsData?.jobs?.filter(
    (j) => j.status === 'succeeded' || j.status === 'pending_review'
  ) ?? []

  const activeJobId = jobIdFromUrl || (completedJobs.length > 0 ? completedJobs[0].id : null)

  return (
    <AppShell>
      <div className="flex h-full items-center justify-center">
        <div className="w-full max-w-lg space-y-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-8">
          <div className="flex items-center gap-3">
            <Link href={`/project/${projectId}`} className="text-[var(--muted)] hover:text-[var(--on-surface)]">
              <ArrowLeft className="size-5" />
            </Link>
            <div>
              <h1 className="text-[20px] font-semibold text-[var(--on-surface)]">Export</h1>
              <p className="text-[13px] text-[var(--muted)]">{project?.name || 'Project'}</p>
            </div>
          </div>
          {!activeJobId && (
            <div className="rounded-[6px] border border-[var(--border)] bg-[var(--surface-low)] p-4 text-center">
              <Download className="mx-auto size-8 text-[var(--muted)]" />
              <p className="mt-2 text-[13px] text-[var(--muted)]">
                No completed jobs found. Run an edit job first.
              </p>
              <Link href={`/project/${projectId}`}>
                <Button variant="primary" className="mt-3">Go to Editor</Button>
              </Link>
            </div>
          )}
          {activeJobId && <ExportPanel projectId={projectId} jobId={activeJobId} />}
        </div>
      </div>
    </AppShell>
  )
}
