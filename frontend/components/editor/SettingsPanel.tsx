'use client'

import { useState } from 'react'
import { Download, Settings, WandSparkles, ExternalLink } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { ModelSelector } from '@/components/editor/ModelSelector'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { exportVideo } from '@/lib/api'

interface ExportPanelProps {
  projectId: string
  jobId: string | null
}

export function ExportPanel({ projectId, jobId }: ExportPanelProps) {
  const [format, setFormat] = useState('mp4')
  const [quality, setQuality] = useState('standard')
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)

  const exportMutation = useMutation({
    mutationFn: async () => {
      if (!jobId) throw new Error('No active job')
      const res = await exportVideo(projectId, jobId, format, quality)
      return res as { download_url: string; status: string }
    },
    onSuccess: (data) => {
      if (data?.download_url) {
        setDownloadUrl(data.download_url)
      }
    },
  })

  return (
    <div className="space-y-3">
      <div className="rounded-[5px] border border-[var(--border)] bg-[var(--surface-low)] p-3">
        <h3 className="text-[12px] font-semibold tracking-tight text-[var(--on-surface)]">Export Settings</h3>
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-[var(--muted)]">Format</span>
            <select
              className="rounded-[4px] border border-[var(--outline-variant)]/50 bg-[var(--surface-lowest)] px-2 py-1 text-[11px] text-[var(--on-surface)] outline-none transition-all duration-150 focus:border-[var(--accent)] focus:shadow-[0_0_0_2px_rgba(107,92,255,0.12)]"
              value={format}
              onChange={(e) => setFormat(e.target.value)}
            >
              <option value="mp4">MP4 (H.264)</option>
              <option value="webm">WebM (VP9)</option>
              <option value="mov">MOV (ProRes)</option>
            </select>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-[var(--muted)]">Quality</span>
            <select
              className="rounded-[4px] border border-[var(--outline-variant)]/50 bg-[var(--surface-lowest)] px-2 py-1 text-[11px] text-[var(--on-surface)] outline-none transition-all duration-150 focus:border-[var(--accent)] focus:shadow-[0_0_0_2px_rgba(107,92,255,0.12)]"
              value={quality}
              onChange={(e) => setQuality(e.target.value)}
            >
              <option value="draft">Draft (fast)</option>
              <option value="standard">Standard</option>
              <option value="high">High (4K ready)</option>
            </select>
          </div>
          {format === 'mp4' && (
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[var(--muted)]">Platform preset</span>
              <select className="rounded-[4px] border border-[var(--outline-variant)]/50 bg-[var(--surface-lowest)] px-2 py-1 text-[11px] text-[var(--on-surface)] outline-none transition-all duration-150 focus:border-[var(--accent)] focus:shadow-[0_0_0_2px_rgba(107,92,255,0.12)]">
                <option value="douyin">Douyin (9:16)</option>
                <option value="xiaohongshu">Xiaohongshu (9:16)</option>
                <option value="taobao">Taobao (1:1)</option>
                <option value="bilibili">Bilibili (16:9)</option>
                <option value="custom">Custom</option>
              </select>
            </div>
          )}
        </div>
      </div>
      {downloadUrl ? (
        <a
          href={downloadUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex w-full items-center justify-center gap-2 rounded-[5px] bg-[var(--accent)] px-4 py-2 text-[12px] font-semibold text-white shadow-[0_0_0_1px_rgba(107,92,255,0.3),0_2px_8px_rgba(107,92,255,0.2)] transition-all duration-150 hover:bg-[var(--accent-hover)] active:scale-[0.98]"
        >
          <ExternalLink className="size-3.5" />
          Download Video
        </a>
      ) : (
        <Button
          className="w-full"
          variant="primary"
          size="sm"
          icon={<Download className="size-3.5" />}
          onClick={() => exportMutation.mutate()}
          disabled={!jobId || exportMutation.isPending}
        >
          {exportMutation.isPending ? 'Rendering...' : 'Render Final'}
        </Button>
      )}
      {exportMutation.isPending && <Progress value={50} variant="accent" />}
      {exportMutation.isError && (
        <p className="flex items-center gap-1.5 text-[11px] text-[var(--error)]">
          <span className="size-1 rounded-full bg-[var(--error)]" />
          Export failed. Please try again.
        </p>
      )}
    </div>
  )
}

type SettingsTab = 'models' | 'export'

interface SettingsPanelProps {
  projectId: string
  jobId: string | null
}

export function SettingsPanel({ projectId, jobId }: SettingsPanelProps) {
  const [tab, setTab] = useState<SettingsTab>('models')

  return (
    <aside className="flex w-72 shrink-0 flex-col border-l border-[var(--border)] bg-[var(--surface)]">
      <header className="flex h-10 items-center gap-0.5 border-b border-[var(--border)] px-2">
        <button
          className={`flex-1 rounded-[4px] px-2.5 py-1.5 text-[11px] font-medium transition-all duration-150 ${tab === 'models' ? 'bg-[var(--accent)]/10 text-[var(--accent)] shadow-[0_0_0_1px_rgba(107,92,255,0.12)]' : 'text-[var(--muted)] hover:text-[var(--on-surface)]'}`}
          onClick={() => setTab('models')}
        >
          <Settings className="mr-1 inline size-3" />
          Models
        </button>
        <button
          className={`flex-1 rounded-[4px] px-2.5 py-1.5 text-[11px] font-medium transition-all duration-150 ${tab === 'export' ? 'bg-[var(--accent)]/10 text-[var(--accent)] shadow-[0_0_0_1px_rgba(107,92,255,0.12)]' : 'text-[var(--muted)] hover:text-[var(--on-surface)]'}`}
          onClick={() => setTab('export')}
        >
          <Download className="mr-1 inline size-3" />
          Export
        </button>
      </header>
      <div className="flex-1 overflow-auto p-3">
        {tab === 'models' && <ModelSelector />}
        {tab === 'export' && <ExportPanel projectId={projectId} jobId={jobId} />}
      </div>
      <footer className="flex items-center border-t border-[var(--border)] px-3 py-2 text-[10px] text-[var(--muted)]">
        <WandSparkles className="mr-1.5 size-3 text-[var(--accent)]" />
        {jobId ? <span className="mono">Job {jobId.slice(0, 8)}...</span> : 'No active job'}
      </footer>
    </aside>
  )
}