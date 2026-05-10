'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

export interface CostSummary {
  total_tokens: number
  total_calls: number
  by_node: Record<string, { input_tokens: number; output_tokens: number; calls: number; duration_ms: number }>
  by_provider: Record<string, { input_tokens: number; output_tokens: number; calls: number; duration_ms: number }>
}

export interface ProgressEvent {
  job_id: string
  event: string
  progress: number
  message: string | null
  node?: string
  cost?: CostSummary
}

export function useJobProgress(jobId: string | null) {
  const [events, setEvents] = useState<ProgressEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentNode, setCurrentNode] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!jobId) return
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
    const url = `${apiBase}/jobs/${jobId}/events`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)

    es.onmessage = (e) => {
      try {
        const data: ProgressEvent = JSON.parse(e.data)
        setEvents((prev) => [...prev.slice(-99), data])
        if (data.progress !== undefined) setProgress(data.progress)
        if (data.node) setCurrentNode(data.node)
      } catch { /* ignore parse errors */ }
    }

    return () => {
      es.close()
      eventSourceRef.current = null
      setConnected(false)
    }
  }, [jobId])

  const clear = useCallback(() => {
    setEvents([])
    setProgress(0)
    setCurrentNode(null)
  }, [])

  return { events, connected, progress, currentNode, clear }
}