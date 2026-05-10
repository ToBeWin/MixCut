'use client'

import { useState, useCallback, useRef } from 'react'
import { useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, FileImage, FileVideo, ListVideo, UploadCloud } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { useI18n } from '@/lib/i18n'
import { listAssets, uploadAsset, type Asset } from '@/lib/api'

interface UploadItem {
  file: File
  status: 'pending' | 'uploading' | 'done' | 'error'
  progress: number
  result?: Asset
  error?: string
}

export function UploadPage() {
  const params = useParams()
  const projectId = (params?.id as string) || ''
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { t } = useI18n()

  const { data } = useQuery({
    queryKey: ['assets', projectId],
    queryFn: () => listAssets(projectId),
    enabled: !!projectId,
  })

  const [uploads, setUploads] = useState<UploadItem[]>([])
  const [goalForm, setGoalForm] = useState({
    platform: 'douyin',
    aspect_ratio: '9:16',
    style: 'professional',
    target_duration: 30,
    prompt: '',
    subtitle_requested: true,
    voiceover_requested: false,
    bgm_requested: false,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ projectId, file }: { projectId: string; file: File }) => uploadAsset(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets', projectId] })
    },
  })

  const handleFiles = useCallback((files: FileList) => {
    const newItems: UploadItem[] = Array.from(files).map((file) => ({
      file,
      status: 'uploading' as const,
      progress: 0,
    }))
    setUploads((prev) => [...prev, ...newItems])
    newItems.forEach((item) => {
      uploadMutation.mutate(
        { projectId, file: item.file },
        {
          onSuccess: (result) => {
            setUploads((prev) =>
              prev.map((u) => (u.file === item.file ? { ...u, status: 'done' as const, progress: 100, result } : u))
            )
          },
          onError: (error) => {
            setUploads((prev) =>
              prev.map((u) => (u.file === item.file ? { ...u, status: 'error' as const, error: String(error) } : u))
            )
          },
        }
      )
    })
  }, [projectId, uploadMutation])

  const assets = data?.assets ?? []
  const iconForFile = (contentType?: string) => contentType?.startsWith('image/') ? FileImage : FileVideo

  return (
    <AppShell>
      <div className="flex h-full gap-[1px] bg-[var(--outline-variant)]">
        <section className="flex min-w-0 flex-[3] flex-col overflow-auto bg-[var(--surface)] p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-[24px] font-semibold">{t('upload.title')}</h1>
              <p className="text-[12px] text-[var(--muted)]">{t('upload.subtitle')}</p>
            </div>
            <Badge tone="cyan">{t('upload.workspace')}</Badge>
          </div>

          <input ref={fileInputRef} type="file" multiple accept="video/*,image/*" className="hidden" onChange={(e) => e.target.files && handleFiles(e.target.files)} />

          <div
            className="mb-6 flex h-52 cursor-pointer flex-col items-center justify-center rounded-[8px] border border-dashed border-[var(--outline-variant)] bg-[var(--surface-lowest)] text-center transition-colors hover:border-[var(--cyan)]"
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud className="mb-3 size-12 text-[var(--cyan)]" strokeWidth={1.5} />
            <p className="text-[16px] font-semibold">{t('upload.dropTitle')}</p>
            <p className="mt-1 text-[12px] text-[var(--muted)]">{t('upload.dropDescription')}</p>
          </div>

          <div className="space-y-2">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-[16px] font-semibold"><ListVideo className="size-4" /> {t('upload.queue')}</h2>
              <Badge tone="gray">{uploads.length + assets.length} Items</Badge>
            </div>
            {uploads.map((u) => (
              <div key={u.file.name} className="rounded-[4px] border border-[var(--border)] bg-[var(--surface-low)] p-3">
                <div className="flex items-center justify-between gap-4">
                  <span className="flex min-w-0 items-center gap-3">
                    <span className="flex size-10 shrink-0 items-center justify-center rounded bg-[var(--surface-lowest)] text-[var(--cyan)]">
                      {(() => {
                        const AssetIcon = iconForFile(u.file.type)
                        return <AssetIcon className="size-5" />
                      })()}
                    </span>
                    <span className="truncate text-[13px]">{u.file.name}</span>
                  </span>
                  <span className="text-[12px] text-[var(--cyan)]">
                    {u.status === 'uploading' ? t('upload.item.uploading') : u.status === 'done' ? t('upload.item.ready') : u.status === 'error' ? t('upload.item.error') : t('upload.item.queued')}
                  </span>
                </div>
                <Progress value={u.progress} variant={u.status === 'error' ? 'default' : 'accent'} className="mt-2" />
              </div>
            ))}
            {assets.map((asset: Asset) => (
              <div key={asset.id} className="flex items-center justify-between rounded-[4px] border border-[var(--border)] bg-[var(--surface-low)] p-3">
                <span className="flex min-w-0 items-center gap-3">
                  <span className="flex size-10 shrink-0 items-center justify-center rounded bg-[var(--surface-lowest)] text-[var(--cyan)]">
                    {(() => {
                      const AssetIcon = iconForFile(asset.content_type)
                      return <AssetIcon className="size-5" />
                    })()}
                  </span>
                  <span className="truncate text-[13px]">{asset.filename}</span>
                </span>
                <span className="flex items-center gap-2 text-[12px]">
                  <CheckCircle2 className="size-4 text-[var(--success)]" />
                  {asset.duration_seconds ? `${asset.duration_seconds.toFixed(1)}s` : asset.content_type.startsWith('image/') ? t('upload.item.imageReady') : t('upload.item.ready')}
                </span>
              </div>
            ))}
          </div>
        </section>

        <aside className="w-[360px] bg-[var(--surface)] p-6">
          <h2 className="text-[16px] font-semibold">Project Setup</h2>
          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">Platform</span>
              <select value={goalForm.platform} onChange={(e) => setGoalForm({ ...goalForm, platform: e.target.value })} className="mt-1 w-full rounded-[6px] border border-[var(--border)] bg-[var(--surface-low)] px-3 py-2 text-[13px] text-[var(--on-surface)]">
                <option value="douyin">Douyin</option>
                <option value="xiaohongshu">Xiaohongshu</option>
                <option value="taobao">Taobao</option>
                <option value="bilibili">Bilibili</option>
                <option value="custom">Custom</option>
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">Duration (seconds)</span>
              <input type="number" value={goalForm.target_duration} onChange={(e) => setGoalForm({ ...goalForm, target_duration: parseInt(e.target.value) || 30 })} className="mt-1 w-full rounded-[6px] border border-[var(--border)] bg-[var(--surface-low)] px-3 py-2 text-[13px] text-[var(--on-surface)]" min={5} max={600} />
            </label>
            <label className="flex items-center gap-2 text-[13px]">
              <input type="checkbox" checked={goalForm.subtitle_requested} onChange={(e) => setGoalForm({ ...goalForm, subtitle_requested: e.target.checked })} className="accent-[var(--cyan)]" />
              Subtitles
            </label>
            <label className="flex items-center gap-2 text-[13px]">
              <input type="checkbox" checked={goalForm.voiceover_requested} onChange={(e) => setGoalForm({ ...goalForm, voiceover_requested: e.target.checked })} className="accent-[var(--cyan)]" />
              Voiceover (TTS)
            </label>
            <textarea placeholder="Describe what you want..." value={goalForm.prompt} onChange={(e) => setGoalForm({ ...goalForm, prompt: e.target.value })} rows={3} className="w-full rounded-[6px] border border-[var(--border)] bg-[var(--surface-low)] px-3 py-2 text-[13px] text-[var(--on-surface)]" />
            <Button variant="primary" className="w-full">Start AI Planning</Button>
          </div>
        </aside>
      </div>
    </AppShell>
  )
}
