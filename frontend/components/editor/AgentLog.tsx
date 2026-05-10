'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Cpu, Timer, Zap } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import type { CostSummary, ProgressEvent } from '@/lib/sse'

const NODE_COLORS: Record<string, string> = {
  understand: 'border-[rgba(0,240,255,0.5)] bg-[rgba(0,240,255,0.08)] text-[var(--cyan)]',
  plan: 'border-[rgba(107,92,255,0.5)] bg-[rgba(107,92,255,0.08)] text-[var(--accent)]',
  execute: 'border-[rgba(254,183,0,0.5)] bg-[rgba(254,183,0,0.08)] text-[var(--amber-soft,#f0b400)]',
  subtitle: 'border-[rgba(82,196,26,0.5)] bg-[rgba(82,196,26,0.08)] text-green-400',
  tts: 'border-[rgba(251,146,60,0.5)] bg-[rgba(251,146,60,0.08)] text-orange-400',
  correct: 'border-[rgba(236,72,153,0.5)] bg-[rgba(236,72,153,0.08)] text-pink-400',
  human_review: 'border-[rgba(168,162,158,0.5)] bg-[rgba(168,162,158,0.08)] text-[var(--muted)]',
  supervisor: 'border-[rgba(107,92,255,0.5)] bg-[rgba(107,92,255,0.08)] text-[var(--accent)]',
}

const NODE_LABELS: Record<string, string> = {
  understand: 'Understand',
  plan: 'Plan',
  execute: 'Execute',
  subtitle: 'Subtitle',
  tts: 'TTS',
  correct: 'Correct',
  human_review: 'Review',
  supervisor: 'Supervisor',
}

interface AgentLogProps {
  events: ProgressEvent[]
  connected: boolean
  currentNode: string | null
  progress: number
}

export function AgentLog({ events, connected, currentNode, progress }: AgentLogProps) {
  const expanded = useAppStore((s) => s.agentLogExpanded)
  const toggleAgentLog = useAppStore((s) => s.toggleAgentLog)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (!expanded) {
    return (
      <button
        onClick={toggleAgentLog}
        className="flex h-8 w-full items-center justify-between border-t border-[var(--border)] bg-[var(--surface)] px-3 text-[11px] transition-colors hover:bg-[var(--surface-low)]"
      >
        <div className="flex items-center gap-2">
          {connected && currentNode && (
            <>
              <span className="size-1.5 animate-pulse rounded-full bg-[var(--accent)]" />
              <span className="font-medium text-[var(--on-surface)]">{NODE_LABELS[currentNode] || currentNode}</span>
            </>
          )}
          {!connected && (
            <span className="text-[var(--muted)]">Agent Log</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-[var(--muted)]">
          <span className="mono tabular-nums">{Math.round(progress * 100)}%</span>
          <ChevronUp className="size-3" />
        </div>
      </button>
    )
  }

  return (
    <div className="flex max-h-[280px] flex-col border-t border-[var(--border)] bg-[var(--surface)]">
      <button
        onClick={toggleAgentLog}
        className="flex h-8 items-center justify-between border-b border-[var(--border)] px-3 text-[11px] transition-colors hover:bg-[var(--surface-low)]"
      >
        <div className="flex items-center gap-2">
          {connected && <span className="size-1.5 animate-pulse rounded-full bg-[var(--accent)]" />}
          <span className="font-semibold text-[var(--on-surface)]">Agent Log</span>
          <span className="mono text-[var(--muted)]">{events.length} events</span>
        </div>
        <ChevronDown className="size-3 text-[var(--muted)]" />
      </button>
      <div className="flex-1 overflow-auto">
        {events.length === 0 && (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <Cpu className="size-5 text-[var(--muted)]" />
            <p className="mt-2 text-[12px] text-[var(--muted)]">Waiting for agent events...</p>
          </div>
        )}
        {[...events].reverse().map((event, i) => {
          const node = event.node || 'supervisor'
          const colorClass = NODE_COLORS[node] || NODE_COLORS.supervisor
          const isExpanded = expandedRows.has(`${i}-${event.node}`)
          const isRunning = connected && currentNode === node && event.event === 'node_start'

          return (
            <div key={`${i}-${event.node}`} className="border-b border-[var(--border)]/50 last:border-b-0">
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-[var(--surface-low)]"
                onClick={() => toggleRow(`${i}-${event.node}`)}
              >
                <span className={`flex size-5 shrink-0 items-center justify-center rounded-[3px] border text-[9px] font-bold ${colorClass}`}>
                  {(NODE_LABELS[node] || node).charAt(0)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[12px] font-semibold text-[var(--on-surface)]">
                      {NODE_LABELS[node] || node}
                    </span>
                    {isRunning && (
                      <span className="inline-block size-1.5 animate-pulse rounded-full bg-[var(--cyan)]" />
                    )}
                    {event.event === 'node_error' && (
                      <span className="rounded-[2px] bg-red-500/15 px-1 text-[9px] text-red-400">error</span>
                    )}
                  </div>
                  {event.message && (
                    <p className="truncate text-[11px] text-[var(--muted)]">{event.message}</p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {event.progress > 0 && event.progress < 1 && (
                    <span className="mono text-[10px] text-[var(--muted)]">{Math.round(event.progress * 100)}%</span>
                  )}
                  {isExpanded ? (
                    <ChevronDown className="size-3 text-[var(--muted)]" />
                  ) : (
                    <ChevronRight className="size-3 text-[var(--muted)]" />
                  )}
                </div>
              </button>
              {isExpanded && (
                <div className="border-t border-[var(--border)]/30 bg-[var(--surface-lowest)] px-3 py-2">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
                    <div>
                      <span className="text-[var(--muted)]">Event:</span>{' '}
                      <span className="text-[var(--on-surface)]">{event.event}</span>
                    </div>
                    <div>
                      <span className="text-[var(--muted)]">Node:</span>{' '}
                      <span className="text-[var(--on-surface)]">{node}</span>
                    </div>
                    {event.message && (
                      <div className="col-span-2 mt-1">
                        <span className="text-[var(--muted)]">Detail:</span>{' '}
                        <span className="text-[var(--on-surface)]">{event.message}</span>
                      </div>
                    )}
                    {event.cost && (
                      <CostBreakdown cost={event.cost} />
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ChevronUp({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="m18 15-6-6-6 6" />
    </svg>
  )
}

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.round(ms)}ms`
}

function CostBreakdown({ cost }: { cost: CostSummary }) {
  const nodeEntries = Object.entries(cost.by_node)
  if (nodeEntries.length === 0 && cost.total_calls === 0) return null

  return (
    <div className="col-span-2 mt-1.5 rounded-[4px] border border-[var(--border)]/30 bg-[var(--surface)] p-2">
      <div className="mb-1.5 flex items-center gap-2">
        <span className="text-[10px] font-semibold text-[var(--accent)]">Cost Summary</span>
        <span className="text-[9px] text-[var(--muted)]">
          {formatTokens(cost.total_tokens)} tokens <span className="text-[var(--outline-variant)]">·</span> {cost.total_calls} calls
        </span>
      </div>
      {nodeEntries.length > 0 && (
        <div className="space-y-0.5">
          {nodeEntries.map(([node, stats]) => (
            <div key={node} className="flex items-center justify-between text-[9px]">
              <span className="text-[var(--on-surface)]">{NODE_LABELS[node] || node}</span>
              <span className="mono tabular-nums text-[var(--muted)]">
                {formatTokens(stats.input_tokens + stats.output_tokens)} tok <span className="text-[var(--outline-variant)]">·</span> {formatMs(stats.duration_ms)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}