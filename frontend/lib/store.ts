import { create } from 'zustand'

interface AppState {
  activeProjectId: string | null
  activeJobId: string | null
  sidebarCollapsed: boolean
  agentLogExpanded: boolean
  modelOverrides: Record<string, string>

  setActiveProject: (id: string | null) => void
  setActiveJob: (id: string | null) => void
  toggleSidebar: () => void
  toggleAgentLog: () => void
  setModelOverride: (task: string, provider: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  activeProjectId: null,
  activeJobId: null,
  sidebarCollapsed: false,
  agentLogExpanded: false,
  modelOverrides: {},

  setActiveProject: (id) => set({ activeProjectId: id }),
  setActiveJob: (id) => set({ activeJobId: id }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  toggleAgentLog: () => set((s) => ({ agentLogExpanded: !s.agentLogExpanded })),
  setModelOverride: (task, provider) =>
    set((s) => ({ modelOverrides: { ...s.modelOverrides, [task]: provider } })),
}))