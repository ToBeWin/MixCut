'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { AlertTriangle, CheckCircle2, RotateCcw, Sparkles, Settings, XCircle } from 'lucide-react'
import { useProject, useJob, useCreateJob, useCancelJob } from '@/hooks/queries'
import { AppShell } from '@/components/layout/AppShell'
import { AssetBrowser } from '@/components/editor/AssetBrowser'
import { VideoPlayer } from '@/components/editor/VideoPlayer'
import { Timeline } from '@/components/editor/Timeline'
import { ChatPanel } from '@/components/editor/ChatPanel'
import { AgentLog } from '@/components/editor/AgentLog'
import { SettingsPanel } from '@/components/editor/SettingsPanel'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { useJobProgress } from '@/lib/sse'
import { getJobOutputUrl, type Asset, type EditSegment, type UserGoal } from '@/lib/api'

const DEFAULT_GOAL: UserGoal = {
  prompt: '',
  platform: 'douyin',
  aspect_ratio: '9:16',
  style: 'lively',
  target_duration: 30,
  selling_points: null,
  product_name: null,
  voiceover_requested: false,
  subtitle_requested: true,
  bgm_requested: false,
}

export function EditorPage() {
  const params = useParams()
  const projectId = (params?.id as string) || ''
  const { addToast } = useToast()
  const [jobId, setJobId] = useState<string | null>(null)
  const [segments, setSegments] = useState<EditSegment[]>([])
  const [duration, setDuration] = useState(30)
  const [currentTime, setCurrentTime] = useState(0)
  const [videoSrc, setVideoSrc] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [showGoalForm, setShowGoalForm] = useState(false)
  const [goalDraft, setGoalDraft] = useState<UserGoal>(DEFAULT_GOAL)
  const [selectedSegment, setSelectedSegment] = useState<EditSegment | null>(null)

  const { data: project } = useProject(projectId)
  const { data: job } = useJob(jobId)

  const { events, connected, progress, currentNode } = useJobProgress(jobId)

  // Connect video source when job completes
  useEffect(() => {
    if (!job) return
    if ((job.status === 'succeeded' || job.status === 'pending_review') && job.id) {
      setVideoSrc(getJobOutputUrl(job.id))
    }
  }, [job?.id, job?.status])

  // Extract segments from edit_script
  useEffect(() => {
    if (!job?.edit_script?.segments) return
    setSegments(job.edit_script.segments)
    if (job.edit_script.target_duration) {
      setDuration(job.edit_script.target_duration)
    }
  }, [job?.edit_script])

  // Toast on job status changes
  useEffect(() => {
    if (!job) return
    if (job.status === 'succeeded') {
      addToast('Job completed successfully', 'success')
    } else if (job.status === 'failed') {
      addToast(`Job failed: ${job.error || 'Unknown error'}`, 'error')
    } else if (job.status === 'pending_review') {
      addToast('Job is ready for review', 'info')
    }
  }, [job?.status]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleTimeUpdate = useCallback((time: number, dur: number) => {
    setCurrentTime(time)
    if (dur > 0) setDuration(dur)
  }, [])

  const handleSelectAsset = useCallback((_asset: Asset) => {}, [])

  const handleSegmentSelect = useCallback((segment: EditSegment | null) => {
    setSelectedSegment(segment)
  }, [])

  const handleReorder = useCallback((newSegments: EditSegment[]) => {
    setSegments(newSegments)
    const total = newSegments.reduce((sum, seg) => sum + (seg.out_point - seg.in_point) / seg.speed, 0)
    setDuration(Math.ceil(total))
  }, [])

  const [videoElement, setVideoElement] = useState<HTMLVideoElement | null>(null)

  const handleVideoRef = useCallback((el: HTMLVideoElement | null) => {
    setVideoElement(el)
  }, [])

  const handleSeek = useCallback(
    (time: number) => {
      if (videoElement) {
        videoElement.currentTime = time
      }
    },
    [videoElement],
  )

  const startJobMutation = useCreateJob(projectId)
  const cancelMutation = useCancelJob()

  const handleStartEdit = useCallback(() => {
    setShowGoalForm(true)
  }, [])

  const handleSubmitGoal = useCallback(() => {
    if (!goalDraft.prompt.trim()) return
    startJobMutation.mutate(goalDraft, {
      onSuccess: (job) => {
        setJobId(job.id)
        setShowGoalForm(false)
        addToast('Job created, processing started', 'success')
      },
      onError: (error: any) => {
        const detail = error?.body ? (() => {
          try { return JSON.parse(error.body).detail } catch { return null }
        })() : null
        addToast(detail || `Failed to create job (${error.status || 'network'})`, 'error')
      },
    })
  }, [goalDraft, startJobMutation, addToast])

  const isRunning = job?.status === 'running' || job?.status === 'queued'
  const isPendingReview = job?.status === 'pending_review'
  const isFailed = job?.status === 'failed'

  return (
    <AppShell>
      <div className="grid h-full grid-cols-[240px_1fr_320px] bg-[var(--outline-variant)]">
        <AssetBrowser projectId={projectId} onSelectAsset={handleSelectAsset} />
        <section className="flex min-w-0 flex-col">
          <div className="flex min-h-0 flex-1 flex-col bg-[var(--surface)]">
            <header className="flex h-10 items-center justify-between border-b border-[var(--border)] px-3">
              <div className="flex items-center gap-3 text-[var(--text-xs)] text-[var(--text-secondary)]">
                <span className="mono truncate text-[var(--accent)]">{project?.name || 'Loading...'}</span>
                {jobId && (
                  <span className={`rounded-[var(--radius-sm)] px-1.5 py-0.5 text-[10px] ${
                    isRunning ? 'bg-[rgba(0,240,255,0.12)] text-[var(--cyan)]' :
                    isPendingReview ? 'bg-[rgba(254,183,0,0.12)] text-[var(--amber-soft)]' :
                    isFailed ? 'bg-[rgba(255,77,79,0.12)] text-red-400' :
                    job?.status === 'succeeded' ? 'bg-[rgba(82,196,26,0.12)] text-green-400' :
                    'bg-[rgba(107,92,255,0.12)] text-[var(--accent)]'
                  }`}>
                    {job?.status || 'queued'}
                  </span>
                )}
                {job?.current_step && jobId && (
                  <span className="text-[var(--text-tertiary)]">{job.current_step}</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {isRunning && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      if (jobId) {
                        cancelMutation.mutate(jobId, {
                          onSuccess: () => addToast('Job canceled', 'info'),
                          onError: () => addToast('Failed to cancel job', 'error'),
                        })
                      }
                    }}
                    disabled={cancelMutation.isPending}
                    className="text-[11px] text-red-400 hover:text-red-300"
                  >
                    Cancel
                  </Button>
                )}
                <Button
                  variant="ghost"
                  icon={<Settings className="size-4" />}
                  onClick={() => setShowSettings((s) => !s)}
                />
                <Button
                  variant="primary"
                  icon={<Sparkles className="size-4" />}
                  onClick={handleStartEdit}
                  disabled={startJobMutation.isPending || isRunning}
                  className="text-[13px]"
                >
                  {startJobMutation.isPending ? 'Starting...' : 'Start Edit'}
                </Button>
              </div>
            </header>

            {/* Pending Review Banner */}
            {isPendingReview && (
              <div className="flex items-center gap-3 border-b border-[var(--amber-soft)]/20 bg-[rgba(254,183,0,0.06)] px-4 py-2">
                <CheckCircle2 className="size-4 shrink-0 text-[var(--amber-soft)]" />
                <span className="flex-1 text-[12px] text-[var(--amber-soft)]">
                  Draft ready for review. Use the chat to request changes or approve to export.
                </span>
              </div>
            )}

            {/* Failed Banner */}
            {isFailed && (
              <div className="flex items-center gap-3 border-b border-red-500/20 bg-[rgba(255,77,79,0.06)] px-4 py-2">
                <XCircle className="size-4 shrink-0 text-red-400" />
                <span className="flex-1 text-[12px] text-red-400">
                  {job?.error || 'Job failed. You can start a new edit or retry.'}
                </span>
                <Button
                  variant="ghost"
                  icon={<RotateCcw className="size-3" />}
                  onClick={handleStartEdit}
                  className="shrink-0 text-[11px] text-red-400 hover:text-red-300"
                >
                  Retry
                </Button>
              </div>
            )}

            {/* Node Errors Banner */}
            {job?.status === 'succeeded' && events.some(e => e.event === 'node_error') && (
              <div className="flex items-center gap-3 border-b border-[var(--amber-soft)]/20 bg-[rgba(254,183,0,0.04)] px-4 py-1.5">
                <AlertTriangle className="size-3.5 shrink-0 text-[var(--amber-soft)]" />
                <span className="text-[11px] text-[var(--amber-soft)]">
                  Some steps had errors but the job completed with available data.
                </span>
              </div>
            )}

            <div className="flex flex-1 items-center justify-center bg-[var(--bg-primary)] p-4">
              <VideoPlayer
                src={videoSrc}
                aspectRatio="9:16"
                onTimeUpdate={handleTimeUpdate}
                onVideoRef={handleVideoRef}
                className="h-full w-full"
              />
            </div>
            <AgentLog
              events={events}
              connected={connected}
              currentNode={currentNode}
              progress={progress}
            />
          </div>
          <Timeline
            segments={segments}
            duration={duration}
            currentTime={currentTime}
            onSegmentSelect={handleSegmentSelect}
            onSeek={handleSeek}
            onReorder={handleReorder}
          />
        </section>
        <ChatPanel projectId={projectId} jobId={jobId} goal={job?.goal ?? null} />
        {showSettings && (
          <SettingsPanel projectId={projectId} jobId={jobId} />
        )}
      </div>

      {/* Goal Form Modal */}
      <Modal open={showGoalForm} onClose={() => setShowGoalForm(false)} title="New Edit Job">
        <div className="w-full space-y-5">
          {/* Platform Presets */}
          <div>
            <label className="mb-2 block text-[12px] font-medium text-[var(--muted)]">Platform</label>
            <div className="grid grid-cols-4 gap-2">
              {[
                { id: 'douyin', label: 'Douyin', ratio: '9:16', dur: '60s', icon: '🎵' },
                { id: 'xiaohongshu', label: 'XHS', ratio: '3:4', dur: '15min', icon: '📕' },
                { id: 'taobao', label: 'Taobao', ratio: '1:1', dur: '60s', icon: '🛒' },
                { id: 'bilibili', label: 'Bilibili', ratio: '16:9', dur: '∞', icon: '📺' },
              ].map((p) => (
                <button
                  key={p.id}
                  className={`flex flex-col items-center gap-1 rounded-lg border px-2 py-2.5 text-[11px] transition-all ${
                    goalDraft.platform === p.id
                      ? 'border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]'
                      : 'border-[var(--outline-variant)] bg-[var(--surface-lowest)] text-[var(--text-secondary)] hover:border-[var(--accent)]/40'
                  }`}
                  onClick={() => {
                    const ratioMap: Record<string, string> = { douyin: '9:16', xiaohongshu: '3:4', taobao: '1:1', bilibili: '16:9' }
                    setGoalDraft((g) => ({ ...g, platform: p.id, aspect_ratio: ratioMap[p.id] || '9:16' }))
                  }}
                >
                  <span className="text-base">{p.icon}</span>
                  <span className="font-semibold">{p.label}</span>
                  <span className="text-[10px] text-[var(--text-tertiary)]">{p.ratio} · {p.dur}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Edit Instructions */}
          <div>
            <label className="mb-1 block text-[12px] font-medium text-[var(--muted)]">Edit Instructions</label>
            <textarea
              className="w-full resize-none rounded-[6px] border border-[var(--outline-variant)] bg-[var(--surface-lowest)] px-3 py-2 text-[13px] outline-none placeholder:text-[var(--muted)] focus:border-[var(--accent)]"
              rows={3}
              placeholder="Describe how you want the video edited..."
              value={goalDraft.prompt}
              onChange={(e) => setGoalDraft((g) => ({ ...g, prompt: e.target.value }))}
              autoFocus
            />
          </div>

          {/* Duration Slider */}
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="text-[12px] font-medium text-[var(--muted)]">Target Duration</label>
              <span className="mono text-[12px] text-[var(--cyan)]">{goalDraft.target_duration}s</span>
            </div>
            <input
              type="range"
              min={5}
              max={120}
              step={5}
              value={goalDraft.target_duration}
              onChange={(e) => setGoalDraft((g) => ({ ...g, target_duration: Number(e.target.value) }))}
              className="w-full accent-[var(--accent)]"
            />
            <div className="flex justify-between text-[10px] text-[var(--text-tertiary)]">
              <span>5s</span>
              <span>30s</span>
              <span>60s</span>
              <span>120s</span>
            </div>
          </div>

          {/* Style + Aspect */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-[12px] font-medium text-[var(--muted)]">Style</label>
              <select
                className="w-full rounded-[4px] border border-[var(--outline-variant)] bg-[var(--surface-lowest)] px-2 py-1.5 text-[12px] outline-none focus:border-[var(--accent)]"
                value={goalDraft.style}
                onChange={(e) => setGoalDraft((g) => ({ ...g, style: e.target.value }))}
              >
                <option value="lively">Lively</option>
                <option value="professional">Professional</option>
                <option value="cinematic">Cinematic</option>
                <option value="minimal">Minimal</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-[12px] font-medium text-[var(--muted)]">Aspect Ratio</label>
              <div className="flex gap-1.5">
                {['9:16', '1:1', '16:9'].map((r) => (
                  <button
                    key={r}
                    className={`flex-1 rounded border px-2 py-1.5 text-[11px] font-medium transition-all ${
                      goalDraft.aspect_ratio === r
                        ? 'border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]'
                        : 'border-[var(--outline-variant)] bg-[var(--surface-lowest)] text-[var(--text-secondary)] hover:border-[var(--accent)]/40'
                    }`}
                    onClick={() => setGoalDraft((g) => ({ ...g, aspect_ratio: r }))}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Toggles */}
          <div className="flex flex-wrap gap-3">
            {[
              { key: 'subtitle_requested', label: 'Subtitles' },
              { key: 'voiceover_requested', label: 'Voiceover' },
              { key: 'bgm_requested', label: 'BGM' },
            ].map((t) => (
              <label
                key={t.key}
                className={`flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] transition-all ${
                  (goalDraft as any)[t.key]
                    ? 'border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]'
                    : 'border-[var(--outline-variant)] text-[var(--text-secondary)] hover:border-[var(--accent)]/40'
                }`}
              >
                <input
                  type="checkbox"
                  checked={(goalDraft as any)[t.key]}
                  onChange={(e) => setGoalDraft((g) => ({ ...g, [t.key]: e.target.checked }))}
                  className="hidden"
                />
                {(goalDraft as any)[t.key] ? '✓' : '○'} {t.label}
              </label>
            ))}
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-2 border-t border-[var(--border)] pt-3">
            <Button variant="ghost" onClick={() => setShowGoalForm(false)}>Cancel</Button>
            <Button
              variant="primary"
              icon={<Sparkles className="size-4" />}
              onClick={handleSubmitGoal}
              disabled={!goalDraft.prompt.trim() || startJobMutation.isPending}
            >
              {startJobMutation.isPending ? 'Starting...' : 'Start Edit'}
            </Button>
          </div>
        </div>
      </Modal>
    </AppShell>
  )
}
