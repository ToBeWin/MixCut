'use client'

import { useCallback, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Mic, Send, Sparkles, Subtitles, Volume2, RotateCcw } from 'lucide-react'
import { submitCorrection, correctJob, listCorrections, type UserGoal } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { useToast } from '@/components/ui/Toast'
import { useI18n } from '@/lib/i18n'
import { useSpeechToText } from '@/hooks/useSpeechToText'

interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  text: string
  agent?: string
  model?: string
  timestamp: Date
  details?: {
    action?: string
    segments_changed?: number
    before_duration?: number
    after_duration?: number
  }
}

interface ChatPanelProps {
  projectId: string
  jobId: string | null
  goal?: UserGoal | null
}

export function ChatPanel({ projectId, jobId, goal }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const { locale, t } = useI18n()
  const { addToast } = useToast()

  const quickActions = useMemo(() => ([
    { label: t('chat.quick.replan.label'), icon: RotateCcw, prompt: t('chat.quick.replan.prompt') },
    { label: t('chat.quick.subtitle.label'), icon: Subtitles, prompt: t('chat.quick.subtitle.prompt') },
    { label: t('chat.quick.voiceover.label'), icon: Volume2, prompt: t('chat.quick.voiceover.prompt') },
    { label: t('chat.quick.refine.label'), icon: Sparkles, prompt: t('chat.quick.refine.prompt') },
  ]), [t])

  const { isSupported, isListening, startListening, stopListening } = useSpeechToText(locale, (transcript) => {
    setInput(transcript)
  })

  const { data: corrections } = useQuery({
    queryKey: ['corrections', projectId],
    queryFn: () => listCorrections(projectId),
    enabled: !!projectId,
  })

  const correctionMutation = useMutation({
    mutationFn: (text: string) => {
      if (!jobId) return Promise.reject(new Error('No active job'))
      // Use the new correctJob endpoint for actual graph correction
      return correctJob(jobId, text)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['corrections', projectId] })
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
    },
  })

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim()) return
      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        text: text.trim(),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMsg])
      setInput('')
      setIsTyping(true)

      correctionMutation.mutate(text.trim(), {
        onSuccess: (data: any) => {
          const agentMsg: ChatMessage = {
            id: `a-${Date.now()}`,
            role: 'agent',
            text: locale === 'zh-CN'
              ? '修正已应用，正在重新处理视频...'
              : 'Correction applied, re-processing video...',
            agent: 'correct_agent',
            model: locale === 'zh-CN' ? '当前路由模型' : 'Current Routed Model',
            timestamp: new Date(),
            details: {
              action: locale === 'zh-CN' ? '修正中' : 'correcting',
            },
          }
          setMessages((prev) => [...prev, agentMsg])
          setIsTyping(false)
          addToast('Correction submitted', 'success')
        },
        onError: () => {
          const errorMsg: ChatMessage = {
            id: `a-${Date.now()}`,
            role: 'agent',
            text: t('chat.agent.error'),
            agent: 'system',
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, errorMsg])
          setIsTyping(false)
          addToast('Failed to submit correction', 'error')
        },
      })
    },
    [jobId, correctionMutation, locale, t]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        sendMessage(input)
      }
    },
    [input, sendMessage]
  )

  return (
    <div className="flex h-full w-full flex-col">
      <header className="flex h-10 items-center justify-between border-b border-[var(--border)] px-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="size-4 text-[var(--accent)]" />
          <span className="text-[12px] font-semibold tracking-tight text-[var(--on-surface)]">{t('chat.title')}</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-[var(--muted)]">
          {corrections && corrections.length > 0 && <span className="mono tabular-nums">{corrections.length}</span>}
          {goal && <span className="mono">{goal.platform} · {goal.style}</span>}
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="flex size-10 items-center justify-center rounded-full bg-[var(--accent)]/10">
              <Sparkles className="size-5 text-[var(--accent)]" />
            </div>
            <p className="mt-3 text-[13px] font-semibold text-[var(--on-surface)]">{t('chat.emptyTitle')}</p>
            <p className="mt-1 text-[12px] text-[var(--muted)]">
              {t('chat.emptyDescription')}
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-[10px] px-3 py-2 ${
                msg.role === 'user'
                  ? 'bg-[var(--accent)] text-white shadow-[0_0_0_1px_rgba(107,92,255,0.3),0_2px_8px_rgba(107,92,255,0.2)]'
                  : 'border border-[var(--border)] bg-[var(--surface-low)] text-[var(--on-surface)] shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]'
              }`}
            >
              {msg.role === 'agent' && msg.agent && (
                <div className="mb-1 flex items-center gap-1.5 text-[10px] text-[var(--muted)]">
                  <span className="rounded-[3px] bg-[rgba(0,240,255,0.12)] px-1 py-0.5 text-[var(--cyan)]">{msg.agent}</span>
                  {msg.model && <span>{msg.model}</span>}
                </div>
              )}
              <p className="text-[13px] leading-relaxed">{msg.text}</p>
              {msg.details && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {msg.details.segments_changed != null && (
                    <span className="rounded-full bg-[rgba(82,196,26,0.12)] px-2 py-0.5 text-[10px] text-green-400">
                      {msg.details.segments_changed} segment{msg.details.segments_changed !== 1 ? 's' : ''} modified
                    </span>
                  )}
                  {msg.details.before_duration != null && msg.details.after_duration != null && (
                    <span className="rounded-full bg-[rgba(254,183,0,0.12)] px-2 py-0.5 text-[10px] text-[var(--amber-soft)]">
                      {msg.details.before_duration.toFixed(1)}s → {msg.details.after_duration.toFixed(1)}s
                    </span>
                  )}
                  {msg.details.action && (
                    <span className="rounded-full bg-[rgba(107,92,255,0.12)] px-2 py-0.5 text-[10px] text-[var(--accent)]">
                      {msg.details.action}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="rounded-[10px] border border-[var(--border)] bg-[var(--surface-low)] px-4 py-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]">
              <div className="flex items-center gap-1">
                <span className="size-1.5 animate-bounce rounded-full bg-[var(--accent)] [animation-delay:0ms]" />
                <span className="size-1.5 animate-bounce rounded-full bg-[var(--accent)] [animation-delay:150ms]" />
                <span className="size-1.5 animate-bounce rounded-full bg-[var(--accent)] [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-[var(--border)] p-2.5">
        <div className="mb-2 flex flex-wrap gap-1">
          {quickActions.map((action) => (
            <button
              key={action.label}
              className="flex items-center gap-1 rounded-[4px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] px-2 py-1 text-[10px] font-medium text-[var(--muted)] transition-all duration-150 hover:border-[var(--accent)]/40 hover:text-[var(--on-surface)] active:scale-[0.97]"
              onClick={() => sendMessage(action.prompt)}
              disabled={!jobId}
              aria-label={action.label}
            >
              <action.icon className="size-3" />
              {action.label}
            </button>
          ))}
        </div>
        <div className="mb-2 flex items-center justify-between text-[10px] text-[var(--muted)]">
          <span>{isListening ? t('chat.voice.listening') : t('chat.voice.idle')}</span>
          {!isSupported && <span>{t('chat.voice.unsupported')}</span>}
        </div>
        <div className="flex gap-2">
          <textarea
            className="flex-1 resize-none rounded-[5px] border border-[var(--outline-variant)] bg-[var(--surface-lowest)] px-3 py-2 text-[13px] outline-none placeholder:text-[var(--muted-dim)] transition-all duration-150 focus:border-[var(--accent)] focus:shadow-[inset_0_1px_2px_rgba(0,0,0,0.2),0_0_0_2px_rgba(107,92,255,0.15)]"
            placeholder={t('chat.input.placeholder')}
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!jobId}
          />
          <div className="flex flex-col gap-1 self-end">
            <Button
              variant="ghost"
              size="sm"
              icon={<Mic className={`size-3.5 ${isListening ? 'text-[var(--accent)]' : ''}`} />}
              onClick={() => (isListening ? stopListening() : startListening())}
              disabled={!isSupported || !jobId}
            />
            <Button
              variant="primary"
              size="sm"
              icon={<Send className="size-3.5" />}
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || !jobId || isTyping}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
