import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nProvider } from '@/lib/i18n'
import { DashboardPage } from '@/components/dashboard/DashboardPage'

// Mock the API
jest.mock('@/lib/api', () => ({
  listProjects: jest.fn().mockResolvedValue({ projects: [] }),
  createProject: jest.fn().mockResolvedValue({ id: '1', name: 'Test' }),
}))

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/',
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

describe('DashboardPage', () => {
  it('renders the dashboard title', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/Recent Projects/i)).toBeInTheDocument()
  })

  it('renders new project button', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByRole('button', { name: /new project/i })).toBeInTheDocument()
  })

  it('renders filter controls', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/^All$/i)).toBeInTheDocument()
    expect(screen.getByText(/^Active$/i)).toBeInTheDocument()
    expect(screen.getByText(/^Done$/i)).toBeInTheDocument()
  })

  it('renders sort control', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/^Recent$/i)).toBeInTheDocument()
  })

  it('shows empty state when no projects', async () => {
    render(<DashboardPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText(/No projects yet/i)).toBeInTheDocument()
    })
  })
})
