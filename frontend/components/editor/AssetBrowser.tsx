'use client'

import { useCallback, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, FileImage, FileVideo, Search, Upload } from 'lucide-react'
import { listAssets, uploadAsset, type Asset } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { useToast } from '@/components/ui/Toast'
import { useI18n } from '@/lib/i18n'

interface AssetBrowserProps {
  projectId: string
  onSelectAsset?: (asset: Asset) => void
}

function qualityColor(score: number | null): string {
  if (score === null) return 'text-[var(--muted)]'
  if (score >= 85) return 'text-green-400'
  if (score >= 70) return 'text-[var(--amber-soft)]'
  return 'text-red-400'
}

export function AssetBrowser({ projectId, onSelectAsset }: AssetBrowserProps) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { t } = useI18n()
  const { addToast } = useToast()
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['assets', projectId],
    queryFn: () => listAssets(projectId),
    enabled: !!projectId,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadAsset(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets', projectId] })
      addToast('Asset uploaded', 'success')
    },
    onError: () => addToast('Upload failed', 'error'),
  })

  const handleFiles = useCallback((files: FileList) => {
    Array.from(files).forEach((file) => {
      uploadMutation.mutate(file)
    })
  }, [uploadMutation])

  const assets = (data?.assets ?? []).filter((a) =>
    search ? a.filename.toLowerCase().includes(search.toLowerCase()) : true,
  )

  const iconForAsset = (asset: Asset) => {
    return asset.content_type.startsWith('image/') ? FileImage : FileVideo
  }

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface)]">
      <header className="border-b border-[var(--border)] p-3">
        <h2 className="truncate text-[14px] font-semibold">{t('assets.title')}</h2>
        <input ref={fileInputRef} type="file" multiple accept="video/*,image/*" className="hidden" onChange={(e) => e.target.files && handleFiles(e.target.files)} />
        {/* Search */}
        <div className="relative mt-2">
          <Search className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-[var(--muted-dim)]" />
          <input
            className="h-7 w-full rounded-[4px] border border-[var(--outline-variant)] bg-[var(--surface-lowest)] pl-7 pr-2 text-[11px] outline-none placeholder:text-[var(--muted-dim)] focus:border-[var(--accent)]"
            placeholder="Search assets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button className="mt-2 w-full" icon={<Upload className="size-4" />} onClick={() => fileInputRef.current?.click()}>
          {t('assets.import')}
        </Button>
      </header>
      <div className="flex-1 overflow-auto p-2">
        {isLoading && <p className="py-4 text-center text-[12px] text-[var(--muted)]">Loading...</p>}
        {uploadMutation.isPending && (
          <div className="mb-2 rounded-[4px] border border-[var(--cyan)]/30 bg-[var(--surface-low)] p-2">
            <p className="truncate text-[11px]">{uploadMutation.variables?.name}</p>
            <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-[var(--outline-variant)]">
              <div className="h-full w-1/2 animate-pulse rounded-full bg-[var(--cyan)]" />
            </div>
          </div>
        )}
        {/* 2-column grid */}
        <div className="grid grid-cols-2 gap-1.5">
          {assets.map((asset: Asset) => {
            const AssetIcon = iconForAsset(asset)
            return (
              <button
                key={asset.id}
                className="group relative overflow-hidden rounded-[4px] border border-[var(--border)] bg-[var(--surface-low)] text-left transition-colors hover:border-[var(--cyan)]/50"
                onClick={() => onSelectAsset?.(asset)}
              >
                {/* Thumbnail area */}
                <div className="relative aspect-video overflow-hidden bg-[var(--surface-lowest)]">
                  <div className="flex h-full items-center justify-center">
                    <AssetIcon className="size-4 text-[var(--muted)]" />
                  </div>
                  {/* Duration badge */}
                  {asset.duration_seconds && (
                    <span className="mono absolute bottom-1 right-1 rounded bg-black/75 px-1 py-0.5 text-[8px] text-white">
                      {asset.duration_seconds.toFixed(1)}s
                    </span>
                  )}
                  {/* Status badge */}
                  {asset.status === 'ready' && (
                    <span className="absolute left-1 top-1 flex items-center gap-0.5 rounded border border-green-400/30 bg-green-400/15 px-0.5 py-0.5 text-[7px] text-green-300">
                      <Check className="size-2" />
                    </span>
                  )}
                  {asset.status === 'failed' && (
                    <span className="absolute left-1 top-1 rounded bg-red-500/20 px-1 py-0.5 text-[7px] text-red-400">
                      err
                    </span>
                  )}
                </div>
                {/* Info */}
                <div className="p-1.5">
                  <p className="truncate text-[10px] text-[var(--on-surface)]">{asset.filename}</p>
                  <div className="mt-0.5 flex items-center justify-between text-[8px] text-[var(--muted)]">
                    <span>{asset.width && asset.height ? `${asset.width}x${asset.height}` : ''}</span>
                    {asset.codec && <span className="uppercase">{asset.codec}</span>}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
        {!isLoading && assets.length === 0 && (
          <p className="py-8 text-center text-[12px] text-[var(--muted)]">
            {search ? 'No matching assets' : t('assets.empty')}
          </p>
        )}
      </div>
    </aside>
  )
}
