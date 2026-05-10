import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from '@/components/dashboard/DashboardPage'

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/',
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

describe('DashboardPage', () => {
  it('renders the dashboard title', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/projects/i)).toBeInTheDocument()
  })

  it('renders new project button', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByRole('button', { name: /new project/i })).toBeInTheDocument()
  })

  it('renders filter controls', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/all/i)).toBeInTheDocument()
    expect(screen.getByText(/active/i)).toBeInTheDocument()
  })

  it('renders sort control', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/recent/i)).toBeInTheDocument()
  })

  it('shows empty state when no projects', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/no projects/i)).toBeInTheDocument()
  })
})
