'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Columns2,
  Crop,
  Maximize2,
  Minimize,
  Pause,
  PictureInPicture2,
  Play,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'

type AspectRatio = '9:16' | '1:1' | '16:9'

const ASPECT_RATIOS: { value: AspectRatio; label: string; width: number; height: number }[] = [
  { value: '9:16', label: '9:16', width: 9, height: 16 },
  { value: '1:1', label: '1:1', width: 1, height: 1 },
  { value: '16:9', label: '16:9', width: 16, height: 9 },
]

const PLAYBACK_SPEEDS = [0.25, 0.5, 1, 1.5, 2] as const

const FRAME_STEP = 1 / 30 // ~30fps

interface VideoPlayerProps {
  src?: string | null
  previousSrc?: string | null
  poster?: string | null
  aspectRatio?: AspectRatio
  onTimeUpdate?: (currentTime: number, duration: number) => void
  onDurationChange?: (duration: number) => void
  onVideoRef?: (el: HTMLVideoElement | null) => void
  className?: string
}

export function VideoPlayer({
  src,
  previousSrc,
  poster,
  aspectRatio: initialAspectRatio = '9:16',
  onTimeUpdate,
  onDurationChange,
  onVideoRef,
  className,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    onVideoRef?.(videoRef.current)
    return () => onVideoRef?.(null)
  }, [onVideoRef])

  const containerRef = useRef<HTMLDivElement>(null)
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [ratio, setRatio] = useState<AspectRatio>(initialAspectRatio)
  const [speed, setSpeed] = useState(1)
  const [fullscreen, setFullscreen] = useState(false)
  const [pip, setPip] = useState(false)
  const [hovering, setHovering] = useState(false)
  const [hoverPosition, setHoverPosition] = useState(0)
  const [showPrevious, setShowPrevious] = useState(false)
  const progressRef = useRef<HTMLDivElement>(null)

  // Play/pause sync
  useEffect(() => {
    if (!videoRef.current) return
    if (playing) {
      videoRef.current.play().catch(() => setPlaying(false))
    } else {
      videoRef.current.pause()
    }
  }, [playing])

  // Speed sync
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = speed
    }
  }, [speed])

  // Fullscreen change listener
  useEffect(() => {
    const handler = () => setFullscreen(!!document.fullscreenElement)
    containerRef.current?.addEventListener('fullscreenchange', handler)
    return () => containerRef.current?.removeEventListener('fullscreenchange', handler)
  }, [])

  const togglePlay = useCallback(() => setPlaying((p) => !p), [])

  const stepFrame = useCallback(
    (direction: 1 | -1) => {
      const v = videoRef.current
      if (!v) return
      setPlaying(false)
      v.currentTime = Math.max(0, Math.min(duration, v.currentTime + direction * FRAME_STEP))
    },
    [duration],
  )

  const skip = useCallback(
    (seconds: number) => {
      const v = videoRef.current
      if (!v) return
      v.currentTime = Math.max(0, Math.min(duration, v.currentTime + seconds))
    },
    [duration],
  )

  const handleTimeUpdate = useCallback(() => {
    const v = videoRef.current
    if (!v) return
    setCurrentTime(v.currentTime)
    onTimeUpdate?.(v.currentTime, v.duration || 0)
  }, [onTimeUpdate])

  const handleDurationChange = useCallback(() => {
    const v = videoRef.current
    if (!v) return
    setDuration(v.duration)
    onDurationChange?.(v.duration)
  }, [onDurationChange])

  const handleProgressClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const bar = progressRef.current
      if (!bar || !duration) return
      const rect = bar.getBoundingClientRect()
      const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
      if (videoRef.current) {
        videoRef.current.currentTime = percent * duration
      }
    },
    [duration],
  )

  const handleProgressHover = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!duration) return
      const bar = progressRef.current
      if (!bar) return
      const rect = bar.getBoundingClientRect()
      setHoverPosition(Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)))
    },
    [duration],
  )

  const handleFullscreen = useCallback(() => {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      containerRef.current?.requestFullscreen()
    }
  }, [])

  const togglePip = useCallback(async () => {
    const v = videoRef.current
    if (!v) return
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture()
      } else {
        await v.requestPictureInPicture()
      }
    } catch {}
  }, [])

  // PiP event listeners
  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    const onEnter = () => setPip(true)
    const onLeave = () => setPip(false)
    v.addEventListener('enterpictureinpicture', onEnter)
    v.addEventListener('leavepictureinpicture', onLeave)
    return () => {
      v.removeEventListener('enterpictureinpicture', onEnter)
      v.removeEventListener('leavepictureinpicture', onLeave)
    }
  }, [src])

  const cycleRatio = useCallback(() => {
    setRatio((r) => {
      const idx = ASPECT_RATIOS.findIndex((ar) => ar.value === r)
      return ASPECT_RATIOS[(idx + 1) % ASPECT_RATIOS.length].value
    })
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't capture if typing in an input
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

      switch (e.key) {
        case ' ':
          e.preventDefault()
          togglePlay()
          break
        case 'ArrowLeft':
          e.preventDefault()
          if (e.shiftKey) {
            skip(-5)
          } else {
            stepFrame(-1)
          }
          break
        case 'ArrowRight':
          e.preventDefault()
          if (e.shiftKey) {
            skip(5)
          } else {
            stepFrame(1)
          }
          break
        case 'j':
        case 'J':
          e.preventDefault()
          skip(-10)
          break
        case 'l':
        case 'L':
          e.preventDefault()
          skip(10)
          break
        case 'k':
        case 'K':
          e.preventDefault()
          togglePlay()
          break
        case 'm':
        case 'M':
          e.preventDefault()
          setMuted((m) => !m)
          break
        case 'f':
        case 'F':
          e.preventDefault()
          handleFullscreen()
          break
        case 'p':
        case 'P':
          e.preventDefault()
          togglePip()
          break
        case ',':
          e.preventDefault()
          stepFrame(-1)
          break
        case '.':
          e.preventDefault()
          stepFrame(1)
          break
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [togglePlay, stepFrame, skip, handleFullscreen, togglePip])

  const currentRatio = ASPECT_RATIOS.find((ar) => ar.value === ratio) || ASPECT_RATIOS[0]
  const displayTime = hovering ? hoverPosition * duration : currentTime
  const progressPercent = duration > 0 ? (displayTime / duration) * 100 : 0

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      className={`flex flex-col outline-none ${className ?? ''}`}
    >
      {/* Video area */}
      <div className="flex flex-1 items-center justify-center bg-black">
        <div
          className="relative overflow-hidden rounded-[8px] border border-[var(--outline-variant)]/50 bg-gradient-to-br from-[var(--surface-lowest)] via-[var(--surface-low)] to-[var(--surface-lowest)] shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]"
          style={{
            aspectRatio: `${currentRatio.width}/${currentRatio.height}`,
            maxHeight: '680px',
          }}
        >
          {src ? (
            <video
              ref={videoRef}
              src={showPrevious && previousSrc ? previousSrc : src}
              poster={poster || undefined}
              onTimeUpdate={handleTimeUpdate}
              onDurationChange={handleDurationChange}
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={() => setPlaying(false)}
              className="h-full w-full object-contain"
              playsInline
              preload="metadata"
            />
          ) : (
            <div className="absolute inset-0 studio-grid-bg opacity-40" />
          )}
          {!src && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <Play className="size-8 text-[var(--muted)]/40" />
              <p className="text-[11px] text-[var(--muted)]">Upload clips and start a job to preview</p>
            </div>
          )}
          {src && !playing && (
            <button
              className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[2px] transition-all duration-200 hover:bg-black/50 group"
              onClick={togglePlay}
              aria-label="Play video"
            >
              <div className="flex size-16 items-center justify-center rounded-full bg-[var(--accent)] shadow-[0_0_0_1px_rgba(107,92,255,0.4),0_0_32px_rgba(107,92,255,0.5),0_8px_24px_rgba(0,0,0,0.4)] transition-transform duration-200 group-hover:scale-105">
                <Play className="size-7 translate-x-0.5 fill-white text-white" />
              </div>
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-10 border-t border-[var(--border)] bg-[var(--surface)]">
        <div
          ref={progressRef}
          className="group/progress relative mx-3 mt-2.5 h-1 cursor-pointer rounded-full bg-[var(--outline-variant)]/60 transition-all duration-150 hover:h-1.5"
          onClick={handleProgressClick}
          onMouseEnter={() => setHovering(true)}
          onMouseLeave={() => setHovering(false)}
          onMouseMove={handleProgressHover}
          role="slider"
          aria-label="Video progress"
          aria-valuemin={0}
          aria-valuemax={Math.round(duration)}
          aria-valuenow={Math.round(currentTime)}
          tabIndex={0}
        >
          <div
            className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-[var(--accent)] to-[var(--accent-hover)] transition-[width] duration-100"
            style={{ width: `${progressPercent}%` }}
          />
          <div
            className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--surface)] border-2 border-[var(--accent)] shadow-[0_0_6px_rgba(107,92,255,0.5)] opacity-0 transition-opacity duration-150 group-hover/progress:opacity-100"
            style={{ left: `${progressPercent}%` }}
          />
          {/* Hover time tooltip */}
          {hovering && duration > 0 && (
            <div
              className="absolute -top-8 -translate-x-1/2 rounded-[4px] bg-[var(--surface-high)] px-2 py-1 text-[10px] font-medium text-[var(--on-surface)] shadow-[0_4px_12px_rgba(0,0,0,0.3)] border border-[var(--outline-variant)]/30"
              style={{ left: `${hoverPosition * 100}%` }}
            >
              {formatTime(hoverPosition * duration)}
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <footer className="flex h-10 items-center justify-between border-t border-[var(--border)] bg-[var(--surface)] px-3">
        <div className="flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => skip(-10)}
            icon={<SkipBack className="size-3.5" />}
            title="Back 10s (J)"
            aria-label="Skip back 10 seconds"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={togglePlay}
            icon={playing ? <Pause className="size-3.5" /> : <Play className="size-3.5" />}
            title={playing ? 'Pause (Space)' : 'Play (Space)'}
            aria-label={playing ? 'Pause' : 'Play'}
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => skip(10)}
            icon={<SkipForward className="size-3.5" />}
            title="Forward 10s (L)"
            aria-label="Skip forward 10 seconds"
          />
          <div className="mx-1.5 h-3 w-px bg-[var(--outline-variant)]" />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMuted((m) => !m)}
            icon={muted ? <VolumeX className="size-3.5" /> : <Volume2 className="size-3.5" />}
            title="Mute (M)"
            aria-label={muted ? 'Unmute' : 'Mute'}
          />
          <span className="mono ml-2 tabular-nums text-[11px] text-[var(--muted)] select-none">
            {formatTime(currentTime)}
            <span className="mx-0.5 text-[var(--outline-variant)]">/</span>
            {formatTime(duration)}
          </span>
        </div>
        <div className="flex items-center gap-0.5">
          <button
            className="mono rounded-[4px] px-1.5 py-0.5 text-[10px] font-medium text-[var(--muted)] transition-colors hover:bg-[var(--surface-container)] hover:text-[var(--on-surface)]"
            onClick={() =>
              setSpeed(
                (s) => PLAYBACK_SPEEDS[(PLAYBACK_SPEEDS.indexOf(s as (typeof PLAYBACK_SPEEDS)[number]) + 1) % PLAYBACK_SPEEDS.length] as typeof s,
              )
            }
            title="Playback speed"
            aria-label={`Playback speed: ${speed}x`}
          >
            {speed}x
          </button>
          <Button variant="ghost" size="sm" onClick={cycleRatio} icon={<Crop className="size-3.5" />} title={`Aspect: ${ratio}`} aria-label={`Aspect ratio: ${ratio}`}>
            {ratio}
          </Button>
          {src && document.pictureInPictureEnabled && (
            <Button
              variant="ghost"
              size="sm"
              onClick={togglePip}
              icon={<PictureInPicture2 className="size-3.5" />}
              title="Picture in Picture (P)"
              aria-label={pip ? 'Exit picture in picture' : 'Picture in picture'}
            />
          )}
          {previousSrc && (
            <Button
              variant={showPrevious ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setShowPrevious((p) => !p)}
              icon={<Columns2 className="size-3.5" />}
              title="Compare with previous version"
              aria-label={showPrevious ? 'Show current version' : 'Show previous version'}
            >
              {showPrevious ? 'Before' : 'After'}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleFullscreen}
            icon={fullscreen ? <Minimize className="size-3.5" /> : <Maximize2 className="size-3.5" />}
            title="Fullscreen (F)"
            aria-label={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          />
        </div>
      </footer>
    </div>
  )
}
