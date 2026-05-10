'use client'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
    super(`API error ${status}`)
    this.status = status
    this.body = body
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => null)
    throw new ApiError(res.status, body)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// --- Types ---

export interface Project {
  id: string
  name: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface Asset {
  id: string
  project_id: string
  filename: string
  storage_path: string
  content_type: string
  status: 'uploaded' | 'analyzing' | 'ready' | 'failed'
  duration_seconds: number | null
  width: number | null
  height: number | null
  fps: number | null
  codec: string | null
  audio_present: boolean
  audio_codec: string | null
  poster_path: string | null
  proxy_path: string | null
}

export interface Job {
  id: string
  project_id: string
  goal: UserGoal
  status: 'queued' | 'running' | 'pending_review' | 'succeeded' | 'failed' | 'canceled'
  progress: number
  current_step: string | null
  output_path: string | null
  edit_script: {
    project_id: string
    target_duration: number
    aspect_ratio: string
    segments: EditSegment[]
    bgm_path: string | null
    voiceover_script: string | null
    planning_rationale: string | null
  } | null
  error: string | null
}

export interface UserGoal {
  prompt: string
  platform: string
  aspect_ratio: string
  style: string
  target_duration: number
  selling_points: string | null
  product_name: string | null
  voiceover_requested: boolean
  subtitle_requested: boolean
  bgm_requested: boolean
}

export interface EditSegment {
  asset_id: string
  in_point: number
  out_point: number
  timeline_start: number
  speed: number
  transition_in: string
  volume: number
  text_overlay: string | null
}

export interface ModelProviderInfo {
  name: string
  supports_vision: boolean
  context_window: number
  max_output_tokens: number
  models: string[]
}

export interface ModelHealth {
  name: string
  online: boolean
  detail: string | null
}

export interface ModelRoute {
  task: string
  display_name: string
  modality: 'multimodal' | 'text'
  provider: string
  model: string | null
  fallback_providers: string[]
  available_providers: string[]
}

export interface CorrectionIntent {
  id: string
  project_id: string
  job_id: string
  raw_text: string
  affected_nodes: string[]
  patch: Record<string, unknown>
  confidence: number
}

// --- Projects ---

export async function listProjects(): Promise<{ projects: Project[] }> {
  return request('/projects')
}

export async function createProject(data: { name: string; description?: string }): Promise<Project> {
  return request('/projects', { method: 'POST', body: JSON.stringify(data) })
}

export async function getProject(id: string): Promise<Project> {
  return request(`/projects/${id}`)
}

export async function updateProject(id: string, data: { name: string; description?: string }): Promise<Project> {
  return request(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteProject(id: string): Promise<void> {
  return request(`/projects/${id}`, { method: 'DELETE' })
}

// --- Assets ---

export async function listAssets(projectId: string): Promise<{ project_id: string; assets: Asset[] }> {
  return request(`/assets/project/${projectId}`)
}

export async function uploadAsset(projectId: string, file: File): Promise<Asset> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/assets/project/${projectId}/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}

export async function deleteAsset(assetId: string): Promise<void> {
  return request(`/assets/${assetId}`, { method: 'DELETE' })
}

// --- Jobs ---

export async function listJobs(projectId: string): Promise<{ jobs: Job[] }> {
  return request(`/jobs/project/${projectId}`)
}

export async function createJob(projectId: string, goal: UserGoal): Promise<Job> {
  return request('/jobs', { method: 'POST', body: JSON.stringify({ project_id: projectId, goal }) })
}

export async function getJob(jobId: string): Promise<Job> {
  return request(`/jobs/${jobId}`)
}

export async function resumeJob(jobId: string): Promise<Job> {
  return request(`/jobs/${jobId}/resume`, { method: 'POST' })
}

export async function correctJob(jobId: string, correctionText: string): Promise<Job> {
  const params = new URLSearchParams({ correction_text: correctionText })
  return request(`/jobs/${jobId}/correct?${params}`, { method: 'POST' })
}

export async function cancelJob(jobId: string): Promise<Job> {
  return request(`/jobs/${jobId}/cancel`, { method: 'POST' })
}

// --- Corrections ---

export async function submitCorrection(projectId: string, jobId: string, message: string) {
  return request('/chat/corrections', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId, job_id: jobId, message }),
  })
}

export async function listCorrections(projectId: string, jobId?: string): Promise<CorrectionIntent[]> {
  const params = jobId ? `?job_id=${jobId}` : ''
  return request(`/chat/corrections${params}`)
}

// --- Models ---

export async function listModels(): Promise<ModelProviderInfo[]> {
  return request('/models')
}

export async function modelHealth(): Promise<ModelHealth[]> {
  return request('/models/health')
}

export async function getModelRoutes(): Promise<{ routes: ModelRoute[] }> {
  return request('/models/routes')
}

export async function updateModelRoute(
  task: string,
  payload: { provider: string; model?: string | null; fallback_providers?: string[] }
): Promise<ModelRoute> {
  return request(`/models/routes/${task}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

// --- Export ---

export async function exportVideo(projectId: string, jobId: string, format: string = 'mp4', quality: string = 'standard') {
  return request('/export', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId, job_id: jobId, format, quality }),
  })
}

export function getJobOutputUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/output`
}

export function getAssetPosterUrl(assetId: string): string {
  return `${API_BASE}/assets/${assetId}/poster`
}

export function getAssetFrameUrl(assetId: string, time: number): string {
  return `${API_BASE}/assets/${assetId}/frame?time=${time}`
}

export { ApiError }
