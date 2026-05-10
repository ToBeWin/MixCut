import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nProvider } from '@/lib/i18n'
import { ToastProvider } from '@/components/ui/Toast'
import { UploadPage } from '@/components/setup/UploadPage'

// Mock the API
jest.mock('@/lib/api', () => ({
  listAssets: jest.fn().mockResolvedValue({ assets: [] }),
  uploadAsset: jest.fn().mockResolvedValue({ id: '1', filename: 'test.mp4' }),
  createJob: jest.fn().mockResolvedValue({ id: 'j1', status: 'queued' }),
}))

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/project/test/upload',
  useParams: () => ({ id: 'test-project' }),
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

describe('UploadPage', () => {
  it('renders the upload title', () => {
    render(<UploadPage />, { wrapper })
    expect(screen.getByText(/Media Ingest/i)).toBeInTheDocument()
  })

  it('renders drop zone', () => {
    render(<UploadPage />, { wrapper })
    expect(screen.getByText(/Drop media here/i)).toBeInTheDocument()
  })
})
