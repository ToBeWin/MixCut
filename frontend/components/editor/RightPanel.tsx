'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, MessageSquare, WandSparkles } from 'lucide-react'
import { useJobProgress } from '@/lib/sse'
import { submitCorrection, exportVideo } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Progress } from '@/components/ui/Progress'

const tabs = ['Trace', 'Corrections', 'Export'] as const

interface RightPanelProps {
  projectId: string
  jobId: string | null
}

export function RightPanel({ projectId, jobId }: RightPanelProps) {
  const [tab, setTab] = useState<(typeof tabs)[number]>('Trace')
  const [correctionText, setCorrectionText] = useState('')
  const queryClient = useQueryClient()

  const { events, connected, progress, currentNode } = useJobProgress(jobId)

  const correctionMutation = useMutation({
    mutationFn: () => {
      if (!jobId) return Promise.reject()
      return submitCorrection(projectId, jobId, correctionText)
    },
    onSuccess: () => {
      setCorrectionText('')
      queryClient.invalidateQueries({ queryKey: ['corrections', projectId] })
    },
  })

  const exportMutation = useMutation({
    mutationFn: () => {
      if (!jobId) return Promise.reject()
      return exportVideo(projectId, jobId)
    },
  })

  return (
    <aside className="flex w-80 shrink-0 flex-col bg-[var(--surface)]">
      <header className="border-b border-[var(--border)] p-3">
        <SegmentedControl value={tab} options={tabs} onChange={setTab} />
      </header>
      <div className="flex-1 overflow-auto p-3">
        {tab === 'Trace' && (
          <div className="space-y-3">
            {connected && (
              <div className="flex items-center gap-2 text-[11px] text-[var(--cyan)]">
                <span className="size-2 rounded-full bg-[var(--cyan)] animate-pulse" />
                Connected
              </div>
            )}
            {progress > 0 && (
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface-low)] p-3">
                <div className="flex items-center justify-between text-[12px]">
                  <span className="font-semibold">{currentNode || 'Processing'}</span>
                  <span className="mono text-[var(--muted)]">{Math.round(progress * 100)}%</span>
                </div>
                <Progress value={progress * 100} variant="accent" className="mt-2" />
              </div>
            )}
            {events.map((event, i) => (
              <div key={i} className="rounded-[4px] border border-[var(--border)] bg-[var(--surface-low)] p-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-[13px] font-semibold">{event.node || event.event}</h3>
                  <span className="mono text-[11px] text-[var(--muted)]">
                    {event.progress ? `${Math.round(event.progress * 100)}%` : ''}
                  </span>
                </div>
                {event.message && <p className="mt-1 text-[12px] text-[var(--muted)]">{event.message}</p>}
              </div>
            ))}
            {!connected && events.length === 0 && (
              <p className="py-8 text-center text-[12px] text-[var(--muted)]">Waiting for job to start...</p>
            )}
          </div>
        )}
        {tab === 'Corrections' && (
          <div className="space-y-3">
            <div className="rounded-[4px] border border-[rgba(0,240,255,0.35)] bg-[rgba(0,240,255,0.08)] p-3">
              <p className="text-[12px] text-[var(--muted)]">Ask for a targeted edit correction.</p>
              <textarea
                className="mt-3 h-28 w-full resize-none rounded-[4px] border border-[var(--outline-variant)] bg-[var(--surface-lowest)] p-2 text-[12px] outline-none focus:border-[var(--cyan)]"
                placeholder="e.g. Make the opening faster and add subtitles"
                value={correctionText}
                onChange={(e) => setCorrectionText(e.target.value)}
              />
              <Button
                className="mt-3 w-full"
                variant="primary"
                icon={<MessageSquare className="size-4" />}
                onClick={() => correctionMutation.mutate()}
                disabled={!correctionText.trim() || !jobId}
              >
                Submit Correction
              </Button>
            </div>
          </div>
        )}
        {tab === 'Export' && (
          <div className="space-y-3">
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface-low)] p-3">
              <p className="text-[12px] font-semibold">Export Settings</p>
              <div className="mt-3 space-y-2 text-[12px]">
                <div className="flex justify-between"><span className="text-[var(--muted)]">Format</span><span>MP4 H.264</span></div>
                <div className="flex justify-between"><span className="text-[var(--muted)]">Quality</span><span>Standard</span></div>
              </div>
            </div>
            <Button
              className="w-full"
              variant="primary"
              icon={<Download className="size-4" />}
              onClick={() => exportMutation.mutate()}
              disabled={!jobId}
            >
              {exportMutation.isPending ? 'Rendering...' : 'Render Final'}
            </Button>
          </div>
        )}
      </div>
      <footer className="border-t border-[var(--border)] p-3 text-[12px] text-[var(--muted)]">
        <WandSparkles className="mr-2 inline size-4 text-[var(--cyan)]" />
        {jobId ? `Job ${jobId.slice(0, 8)}...` : 'No active job'}
      </footer>
    </aside>
  )
}