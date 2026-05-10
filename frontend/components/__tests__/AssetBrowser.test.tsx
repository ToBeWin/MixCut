import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AssetBrowser } from '@/components/editor/AssetBrowser'

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

describe('AssetBrowser', () => {
  it('renders the sidebar container', () => {
    render(<AssetBrowser projectId="test-project" />, { wrapper })
    expect(screen.getByText(/assets/i)).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(<AssetBrowser projectId="test-project" />, { wrapper })
    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument()
  })

  it('renders upload button', () => {
    render(<AssetBrowser projectId="test-project" />, { wrapper })
    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument()
  })

  it('shows empty state when no assets', () => {
    render(<AssetBrowser projectId="test-project" />, { wrapper })
    expect(screen.getByText(/no assets/i)).toBeInTheDocument()
  })
})
