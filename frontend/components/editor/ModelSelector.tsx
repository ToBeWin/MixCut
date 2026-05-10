'use client'

import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, Cpu, AlertCircle, XCircle } from 'lucide-react'
import { getModelRoutes, modelHealth, type ModelHealth, type ModelRoute } from '@/lib/api'
import { useI18n } from '@/lib/i18n'

interface ModelSelectorProps {
  className?: string
}

function HealthDot({ status }: { status: boolean | undefined }) {
  if (status === undefined) return <span className="size-2 rounded-full bg-[var(--muted)]" />
  return (
    <span className={`size-2 rounded-full ${status ? 'bg-green-400' : 'bg-red-400'}`} />
  )
}

export function ModelSelector({ className }: ModelSelectorProps) {
  const { t } = useI18n()
  const { data: routes } = useQuery({
    queryKey: ['model-routes'],
    queryFn: getModelRoutes,
    staleTime: 30_000,
  })

  const { data: health } = useQuery({
    queryKey: ['model-health'],
    queryFn: modelHealth,
    staleTime: 15_000,
  })

  const healthMap = new Map<string, boolean>()
  if (health) {
    for (const h of health) {
      healthMap.set(h.name, h.online)
    }
  }

  return (
    <div className={`space-y-2 ${className ?? ''}`}>
      <div className="flex items-center gap-2 text-[12px] font-semibold text-[var(--on-surface)]">
        <Cpu className="size-4 text-[var(--accent)]" />
        {t('modelSelector.title')}
      </div>
      {routes?.routes.map((route) => {
        const isOnline = healthMap.get(route.provider)
        return (
          <div key={route.task} className="rounded-[4px] border border-[var(--outline-variant)] bg-[var(--surface-lowest)] px-2.5 py-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] text-[var(--muted)]">{t(`settings.route.${route.task}`)}</span>
              <div className="flex items-center gap-1.5">
                <HealthDot status={isOnline} />
                <span className="rounded-[3px] bg-[var(--surface-low)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--on-surface)]">
                  {route.provider}
                </span>
              </div>
            </div>
            <div className="mt-1 flex items-center justify-between text-[9px] text-[var(--muted)]">
              <span>{route.model || t('common.default')}</span>
              {route.fallback_providers.length > 0 && (
                <span>fallback: {route.fallback_providers[0]}</span>
              )}
            </div>
          </div>
        )
      })}
      {routes?.routes.length === 0 && (
        <p className="py-4 text-center text-[11px] text-[var(--muted)]">No model routes configured</p>
      )}
    </div>
  )
}
