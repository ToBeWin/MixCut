'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'

// --- Queries ---

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: api.listProjects,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => api.getProject(id),
    enabled: !!id,
  })
}

export function useAssets(projectId: string) {
  return useQuery({
    queryKey: ['assets', projectId],
    queryFn: () => api.listAssets(projectId),
    enabled: !!projectId,
  })
}

export function useJobs(projectId: string) {
  return useQuery({
    queryKey: ['jobs', projectId],
    queryFn: () => api.listJobs(projectId),
    enabled: !!projectId,
  })
}

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'running' || status === 'queued') return 2000
      return false
    },
  })
}

export function useModelRoutes() {
  return useQuery({
    queryKey: ['model-routes'],
    queryFn: api.getModelRoutes,
  })
}

export function useModelHealth() {
  return useQuery({
    queryKey: ['model-health'],
    queryFn: api.modelHealth,
    refetchInterval: 30000,
  })
}

export function useCorrections(projectId: string, jobId?: string) {
  return useQuery({
    queryKey: ['corrections', projectId, jobId],
    queryFn: () => api.listCorrections(projectId, jobId),
    enabled: !!projectId,
  })
}

// --- Mutations ---

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) => api.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUploadAsset(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => api.uploadAsset(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets', projectId] })
    },
  })
}

export function useDeleteAsset(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (assetId: string) => api.deleteAsset(assetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets', projectId] })
    },
  })
}

export function useCreateJob(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (goal: api.UserGoal) => api.createJob(projectId, goal),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs', projectId] })
    },
  })
}

export function useResumeJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (jobId: string) => api.resumeJob(jobId),
    onSuccess: (_data, jobId) => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
    },
  })
}

export function useCorrectJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ jobId, text }: { jobId: string; text: string }) => api.correctJob(jobId, text),
    onSuccess: (_data, { jobId }) => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['corrections'] })
    },
  })
}

export function useCancelJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (jobId: string) => api.cancelJob(jobId),
    onSuccess: (_data, jobId) => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
    },
  })
}

export function useExportVideo() {
  return useMutation({
    mutationFn: ({ projectId, jobId, format, quality }: { projectId: string; jobId: string; format?: string; quality?: string }) =>
      api.exportVideo(projectId, jobId, format, quality),
  })
}

export function useUpdateModelRoute() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ task, payload }: { task: string; payload: { provider: string; model?: string | null; fallback_providers?: string[] } }) =>
      api.updateModelRoute(task, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-routes'] })
    },
  })
}
