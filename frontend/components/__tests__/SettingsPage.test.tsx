import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nProvider } from '@/lib/i18n'
import { SettingsPage } from '@/components/settings/SettingsPage'

// Mock the API
jest.mock('@/lib/api', () => ({
  listModels: jest.fn().mockResolvedValue([
    { name: 'mock', type: 'mock', online: true, models: ['mock-model'] },
  ]),
  modelHealth: jest.fn().mockResolvedValue([
    { name: 'mock', online: true, detail: 'ok' },
  ]),
  getModelRoutes: jest.fn().mockResolvedValue({
    routes: [
      { task: 'edit_planning', provider: 'mock', model: null, fallback_providers: [] },
    ],
  }),
  updateModelRoute: jest.fn().mockResolvedValue({}),
}))

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/settings',
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return (
    <I18nProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </I18nProvider>
  )
}

describe('SettingsPage', () => {
  it('renders the settings title', () => {
    render(<SettingsPage />, { wrapper })
    expect(screen.getByText(/Model Routing/i)).toBeInTheDocument()
  })

  it('renders model fleet section', () => {
    render(<SettingsPage />, { wrapper })
    expect(screen.getByText(/Active Model Fleet/i)).toBeInTheDocument()
  })

  it('renders task routing section', () => {
    render(<SettingsPage />, { wrapper })
    expect(screen.getByText(/Task Routing/i)).toBeInTheDocument()
  })
})
