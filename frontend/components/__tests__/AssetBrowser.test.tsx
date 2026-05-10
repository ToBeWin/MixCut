import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nProvider } from '@/lib/i18n'
import { ToastProvider } from '@/components/ui/Toast'
import { AssetBrowser } from '@/components/editor/AssetBrowser'

// Mock the API
jest.mock('@/lib/api', () => ({
  listAssets: jest.fn().mockResolvedValue({ assets: [] }),
  uploadAsset: jest.fn().mockResolvedValue({}),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return (
    <I18nProvider>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>{children}</ToastProvider>
      </QueryClientProvider>
    </I18nProvider>
  )
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
    expect(screen.getByText(/import/i)).toBeInTheDocument()
  })

  it('shows empty state when no assets', async () => {
    render(<AssetBrowser projectId="test-project" />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText(/No assets yet/i)).toBeInTheDocument()
    })
  })
})
