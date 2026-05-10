'use client'

import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Activity, CheckCircle2, Route, Server } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import {
  getModelRoutes,
  listModels,
  modelHealth,
  updateModelRoute,
  type ModelProviderInfo,
  type ModelHealth,
  type ModelRoute,
} from '@/lib/api'
import { useI18n } from '@/lib/i18n'

export function SettingsPage() {
  const { t } = useI18n()
  const queryClient = useQueryClient()
  const [saveState, setSaveState] = useState<string | null>(null)

  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['models'],
    queryFn: listModels,
  })

  const { data: health } = useQuery({
    queryKey: ['model-health'],
    queryFn: modelHealth,
    refetchInterval: 30000,
  })

  const { data: routes } = useQuery({
    queryKey: ['model-routes'],
    queryFn: getModelRoutes,
  })

  const routeMutation = useMutation({
    mutationFn: ({ task, provider, model, fallback_providers }: { task: string; provider: string; model?: string | null; fallback_providers?: string[] }) =>
      updateModelRoute(task, { provider, model, fallback_providers }),
    onSuccess: () => {
      setSaveState(t('settings.saved'))
      queryClient.invalidateQueries({ queryKey: ['model-routes'] })
    },
  })

  const healthMap = new Map(health?.map((h: ModelHealth) => [h.name, h.online]))
  const providerMap = new Map((models ?? []).map((provider: ModelProviderInfo) => [provider.name, provider]))
  const onlineCount = useMemo(() => health?.filter((item: ModelHealth) => item.online).length ?? 0, [health])

  return (
    <AppShell>
      <div className="h-full overflow-auto bg-[var(--surface-lowest)] p-6">
        <header className="mb-6 flex items-end justify-between border-b border-[var(--border)] pb-4">
          <div>
            <p className="label-caps mb-2 text-[var(--muted-dim)]">{t('settings.badge')}</p>
            <h1 className="flex items-center gap-2.5 text-[20px] font-semibold tracking-tight text-[var(--on-surface)]">
              <Route className="size-5 text-[var(--accent)]" /> {t('settings.title')}
            </h1>
          </div>
          <Button variant="primary" size="sm">{saveState || t('settings.save')}</Button>
        </header>

        <section className="mb-4 rounded-[6px] border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-[13px] font-semibold tracking-tight text-[var(--on-surface)]"><Server className="size-4 text-[var(--muted)]" /> {t('settings.fleet')}</h2>
            {health && <Badge tone="green">{t('settings.onlineCount', { online: onlineCount, total: health.length })}</Badge>}
          </div>
          {modelsLoading ? (
            <div className="grid grid-cols-4 gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="shimmer h-28 rounded-[4px]" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-3">
              {models?.map((model: ModelProviderInfo) => {
                const online = healthMap.get(model.name) ?? false
                return (
                  <div key={model.name} className="rounded-[5px] border border-[var(--border)] bg-[var(--surface-lowest)] p-3 transition-all duration-150 hover:border-[var(--outline-variant)]">
                    <div className="mb-3 flex items-center justify-between">
                      <h3 className="text-[13px] font-semibold text-[var(--on-surface)]">{model.name}</h3>
                      <Badge tone={online ? 'green' : 'red'}>{online ? t('settings.online') : t('settings.offline')}</Badge>
                    </div>
                    <div className="space-y-1 text-[11px] text-[var(--muted)]">
                      <p>{t('settings.vision')}: {model.supports_vision ? '✓' : '✗'}</p>
                      <p>{t('settings.context')}: {(model.context_window / 1000).toFixed(0)}K tokens</p>
                      <p className="mono text-[10px]">{model.models.join(', ')}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        <section className="rounded-[6px] border border-[var(--border)] bg-[var(--surface)] p-4">
          <h2 className="mb-4 flex items-center gap-2 text-[13px] font-semibold tracking-tight text-[var(--on-surface)]"><Activity className="size-4 text-[var(--muted)]" /> {t('settings.routes')}</h2>
          <div className="space-y-2">
            {routes?.routes.map((route: ModelRoute) => {
              const provider = providerMap.get(route.provider)
              const availableModels = provider?.models ?? []
              return (
                <div key={route.task} className="rounded-[5px] border border-[var(--border)] bg-[var(--surface-lowest)] p-3">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 text-[12px] font-semibold text-[var(--on-surface)]">
                        <span>{t(`settings.route.${route.task}`)}</span>
                        <Badge tone={route.modality === 'multimodal' ? 'cyan' : 'gray'}>
                          {t(`settings.modality.${route.modality}`)}
                        </Badge>
                      </div>
                      <p className="mt-0.5 text-[10px] text-[var(--muted)]">
                        {t('settings.fallbacks')}: {route.fallback_providers.join(' → ') || t('settings.noFallbacks')}
                      </p>
                    </div>
                    <CheckCircle2 className="size-3.5 text-[var(--accent)]" />
                  </div>
                  <div className="grid grid-cols-[1fr_1fr_auto] gap-2">
                    <label className="space-y-1">
                      <span className="text-[10px] font-medium text-[var(--muted)]">{t('settings.primaryProvider')}</span>
                      <select
                        className="w-full rounded-[5px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] px-2 py-1.5 text-[11px] text-[var(--on-surface)] outline-none transition-all duration-150 focus:border-[var(--accent)] focus:shadow-[0_0_0_2px_rgba(107,92,255,0.12)]"
                        value={route.provider}
                        onChange={(event) => {
                          const nextProvider = event.target.value
                          const nextModels = providerMap.get(nextProvider)?.models ?? []
                          routeMutation.mutate({
                            task: route.task,
                            provider: nextProvider,
                            model: nextModels[0] ?? null,
                            fallback_providers: route.fallback_providers,
                          })
                        }}
                      >
                        {route.available_providers.map((providerName) => (
                          <option key={providerName} value={providerName}>
                            {providerName}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="space-y-1">
                      <span className="text-[10px] font-medium text-[var(--muted)]">{t('settings.primaryModel')}</span>
                      <select
                        className="w-full rounded-[5px] border border-[var(--outline-variant)]/50 bg-[var(--surface-low)] px-2 py-1.5 text-[11px] text-[var(--on-surface)] outline-none transition-all duration-150 focus:border-[var(--accent)] focus:shadow-[0_0_0_2px_rgba(107,92,255,0.12)]"
                        value={route.model ?? ''}
                        onChange={(event) => {
                          routeMutation.mutate({
                            task: route.task,
                            provider: route.provider,
                            model: event.target.value || null,
                            fallback_providers: route.fallback_providers,
                          })
                        }}
                      >
                        <option value="">{t('common.default')}</option>
                        {availableModels.map((modelName) => (
                          <option key={modelName} value={modelName}>
                            {modelName}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="flex items-end">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="w-full"
                        onClick={() => {
                          routeMutation.mutate({
                            task: route.task,
                            provider: route.provider,
                            model: route.model,
                            fallback_providers: route.fallback_providers,
                          })
                        }}
                      >
                        {t('common.save')}
                      </Button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>
    </AppShell>
  )
}
