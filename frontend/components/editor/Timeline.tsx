'use client'

import { useState, useCallback } from 'react'
import { GripVertical } from 'lucide-react'
import { type EditSegment, getAssetFrameUrl } from '@/lib/api'

const trackRows = ['V2', 'V1', 'A1'] as const

function colorForIndex(i: number): string {
  const colors = [
    'border-[rgba(0,240,255,0.55)] bg-gradient-to-r from-[rgba(0,240,255,0.22)] to-[rgba(0,240,255,0.08)] text-[var(--cyan)]',
    'border-[rgba(254,183,0,0.5)] bg-gradient-to-r from-[rgba(254,183,0,0.22)] to-[rgba(254,183,0,0.08)] text-[var(--amber-soft)]',
    'border-[rgba(82,196,26,0.5)] bg-gradient-to-r from-[rgba(82,196,26,0.22)] to-[rgba(82,196,26,0.08)] text-green-400',
    'border-[rgba(107,92,255,0.5)] bg-gradient-to-r from-[rgba(107,92,255,0.22)] to-[rgba(107,92,255,0.08)] text-[var(--accent)]',
    'border-[rgba(255,77,79,0.5)] bg-gradient-to-r from-[rgba(255,77,79,0.22)] to-[rgba(255,77,79,0.08)] text-red-400',
  ]
  return colors[i % colors.length]
}

interface TimelineProps {
  segments?: EditSegment[]
  duration?: number
  currentTime?: number
  onSegmentSelect?: (segment: EditSegment | null) => void
  onSeek?: (time: number) => void
  onReorder?: (segments: EditSegment[]) => void
}

export function Timeline({
  segments = [],
  duration = 30,
  currentTime = 0,
  onSegmentSelect,
  onSeek,
  onReorder,
}: TimelineProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  const playheadPercent = duration > 0 ? (currentTime / duration) * 100 : 0

  const handleSegmentClick = useCallback(
    (index: number) => {
      const newIndex = selectedIndex === index ? null : index
      setSelectedIndex(newIndex)
      onSegmentSelect?.(newIndex !== null ? segments[newIndex] : null)
    },
    [selectedIndex, segments, onSegmentSelect],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!segments.length) return
      if (e.key === 'ArrowRight') {
        e.preventDefault()
        const next = selectedIndex === null ? 0 : Math.min(selectedIndex + 1, segments.length - 1)
        setSelectedIndex(next)
        onSegmentSelect?.(segments[next])
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault()
        const prev = selectedIndex === null ? segments.length - 1 : Math.max(selectedIndex - 1, 0)
        setSelectedIndex(prev)
        onSegmentSelect?.(segments[prev])
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        if (selectedIndex !== null) {
          onSeek?.(segments[selectedIndex].timeline_start)
        }
      } else if (e.key === 'Escape') {
        setSelectedIndex(null)
        onSegmentSelect?.(null)
      }
    },
    [selectedIndex, segments, onSegmentSelect, onSeek],
  )

  const handleTrackClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!onSeek) return
      const rect = e.currentTarget.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percent = x / rect.width
      onSeek(percent * duration)
    },
    [duration, onSeek],
  )

  // Drag handlers
  const handleDragStart = useCallback((index: number) => {
    setDragIndex(index)
  }, [])

  const handleDragOver = useCallback(
    (e: React.DragEvent, index: number) => {
      e.preventDefault()
      if (dragIndex !== null && dragIndex !== index) {
        setDragOverIndex(index)
      }
    },
    [dragIndex],
  )

  const handleDrop = useCallback(
    (targetIndex: number) => {
      if (dragIndex === null || dragIndex === targetIndex) {
        setDragIndex(null)
        setDragOverIndex(null)
        return
      }
      const newSegments = [...segments]
      const [moved] = newSegments.splice(dragIndex, 1)
      newSegments.splice(targetIndex, 0, moved)

      // Recalculate timeline_start based on order
      let cursor = 0
      for (const seg of newSegments) {
        seg.timeline_start = cursor
        cursor += (seg.out_point - seg.in_point) / seg.speed
      }

      onReorder?.(newSegments)
      setDragIndex(null)
      setDragOverIndex(null)
    },
    [dragIndex, segments, onReorder],
  )

  const handleDragEnd = useCallback(() => {
    setDragIndex(null)
    setDragOverIndex(null)
  }, [])

  const selected = selectedIndex !== null ? segments[selectedIndex] : null

  return (
    <section className="shrink-0 border-t border-[var(--border)] bg-[var(--surface-lowest)]">
      {/* Header */}
      <div className="flex h-9 items-center justify-between border-b border-[var(--border)] px-3">
        <h2 className="text-[12px] font-semibold tracking-tight text-[var(--on-surface)]">Timeline</h2>
        <span className="mono tabular-nums text-[11px] text-[var(--muted)]">
          {segments.length} segment{segments.length !== 1 ? 's' : ''} <span className="text-[var(--outline-variant)]">·</span> {duration}s
        </span>
      </div>

      {/* Tracks */}
      <div className="grid grid-cols-[52px_1fr]">
        <div>
          {trackRows.map((track) => (
            <div
              key={track}
              className="flex h-14 items-center justify-center border-b border-r border-[var(--border)] text-[10px] font-bold text-[var(--muted)]/70 select-none"
            >
              {track}
            </div>
          ))}
        </div>
        <div
          className="relative cursor-pointer studio-grid-bg"
          onClick={handleTrackClick}
          onKeyDown={handleKeyDown}
          role="listbox"
          aria-label="Timeline segments"
          aria-activedescendant={selectedIndex !== null ? `segment-${selectedIndex}` : undefined}
          tabIndex={0}
        >
          {/* Playhead */}
          <div
            className="absolute bottom-0 top-0 z-10 w-px bg-[var(--cyan)] shadow-[0_0_8px_rgba(0,240,255,0.6)]"
            style={{ left: `${playheadPercent}%` }}
          />

          {trackRows.map((track, row) => (
            <div key={track} className="relative h-14 border-b border-[var(--border)]">
              {track === 'V1' &&
                segments.map((seg, i) => {
                  const left = duration > 0 ? (seg.timeline_start / duration) * 100 : 0
                  const width =
                    duration > 0
                      ? ((seg.out_point - seg.in_point) / seg.speed / duration) * 100
                      : 10
                  const isSelected = selectedIndex === i
                  const isDragging = dragIndex === i
                  const isDragOver = dragOverIndex === i

                  return (
                    <div
                      key={i}
                      id={`segment-${i}`}
                      role="option"
                      aria-selected={isSelected}
                      aria-label={`Segment ${i + 1}: ${seg.asset_id.slice(0, 8)}, ${seg.in_point.toFixed(1)}s to ${seg.out_point.toFixed(1)}s`}
                      draggable
                      onDragStart={() => handleDragStart(i)}
                      onDragOver={(e) => handleDragOver(e, i)}
                      onDrop={() => handleDrop(i)}
                      onDragEnd={handleDragEnd}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleSegmentClick(i)
                      }}
                      className={`absolute top-2 flex h-10 cursor-grab items-center gap-1 overflow-hidden rounded-[4px] border text-[11px] font-semibold transition-all active:cursor-grabbing ${colorForIndex(i)} ${
                        isSelected
                          ? 'ring-2 ring-[var(--cyan)] ring-offset-1 ring-offset-[var(--surface-lowest)] brightness-110'
                          : 'hover:brightness-125'
                      } ${isDragging ? 'opacity-40' : ''} ${
                        isDragOver ? 'ring-2 ring-[var(--amber)] ring-offset-1 ring-offset-[var(--surface-lowest)]' : ''
                      }`}
                      style={{ left: `${left}%`, width: `${Math.max(width, 3)}%` }}
                    >
                      {/* Thumbnail */}
                      {width > 4 && (
                        <img
                          src={getAssetFrameUrl(seg.asset_id, seg.in_point)}
                          alt=""
                          className="h-full w-12 shrink-0 rounded-l-[3px] object-cover opacity-70"
                          loading="lazy"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                        />
                      )}
                      <div className="flex min-w-0 flex-1 items-center gap-1 px-1">
                        <GripVertical className="size-3 shrink-0 opacity-50" />
                        <span className="truncate">{seg.asset_id.slice(0, 8)}</span>
                        {seg.speed !== 1 && (
                          <span className="ml-auto shrink-0 text-[9px] opacity-70">{seg.speed}x</span>
                        )}
                      </div>
                    </div>
                  )
                })}

              {/* Playhead dot on V1 */}
              {row === 0 && (
                <div
                  className="absolute top-0 z-20 size-2 -translate-x-1/2 rounded-full bg-[var(--cyan)] shadow-[0_0_6px_rgba(0,240,255,0.5)]"
                  style={{ left: `${playheadPercent}%` }}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Segment details panel */}
      {selected && (
        <div className="flex items-center gap-3 border-t border-[var(--border)] bg-[var(--surface)] px-3 py-2">
          <span className="text-[11px] font-semibold text-[var(--cyan)]">
            Segment {(selectedIndex ?? 0) + 1}
          </span>
          <span className="text-[11px] text-[var(--muted)]">
            {selected.asset_id.slice(0, 12)}
          </span>
          <span className="mono tabular-nums text-[11px] text-[var(--muted)]">
            {selected.in_point.toFixed(1)}s → {selected.out_point.toFixed(1)}s
          </span>
          <span className="mono tabular-nums text-[11px] text-[var(--muted)]">
            {((selected.out_point - selected.in_point) / selected.speed).toFixed(1)}s
          </span>
          {selected.speed !== 1 && (
            <span className="rounded-[3px] bg-[rgba(254,183,0,0.1)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--amber-soft)]">
              {selected.speed}x
            </span>
          )}
          {selected.transition_in && selected.transition_in !== 'cut' && (
            <span className="rounded-[3px] bg-[rgba(82,196,26,0.1)] px-1.5 py-0.5 text-[10px] font-medium text-green-400">
              {selected.transition_in}
            </span>
          )}
          {selected.text_overlay && (
            <span className="rounded-[3px] bg-[rgba(107,92,255,0.1)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--accent)]">
              overlay
            </span>
          )}
        </div>
      )}
    </section>
  )
}
