import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/components/ui/Toast'

// Mock i18n hook
jest.mock('@/lib/i18n', () => ({
  useI18n: () => ({
    locale: 'en-US',
    t: (key: string) => {
      const map: Record<string, string> = {
        'chat.title': 'Chat',
        'chat.emptyTitle': 'Start a conversation',
        'chat.emptyDescription': 'Send a message to correct or refine the video.',
        'chat.input.placeholder': 'Describe your changes...',
        'chat.send': 'Send',
        'chat.voice.idle': 'Voice idle',
        'chat.voice.unsupported': 'Not supported',
        'chat.agent.error': 'Error occurred',
        'chat.quick.replan.label': 'Replan',
        'chat.quick.replan.prompt': 'Replan the edit',
        'chat.quick.subtitle.label': 'Subtitles',
        'chat.quick.subtitle.prompt': 'Add subtitles',
        'chat.quick.voiceover.label': 'Voiceover',
        'chat.quick.voiceover.prompt': 'Add voiceover',
        'chat.quick.refine.label': 'Refine',
        'chat.quick.refine.prompt': 'Refine the edit',
      }
      return map[key] || key
    },
  }),
}))

// Mock speech-to-text hook
jest.mock('@/hooks/useSpeechToText', () => ({
  useSpeechToText: () => ({
    isSupported: false,
    isListening: false,
    startListening: jest.fn(),
    stopListening: jest.fn(),
  }),
}))

import { ChatPanel } from '@/components/editor/ChatPanel'

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>,
  )
}

describe('ChatPanel', () => {
  it('renders title', () => {
    renderWithQuery(<ChatPanel projectId="p1" jobId={null} />)
    expect(screen.getByText('Chat')).toBeInTheDocument()
  })

  it('shows empty state when no messages', () => {
    renderWithQuery(<ChatPanel projectId="p1" jobId={null} />)
    expect(screen.getByText('Start a conversation')).toBeInTheDocument()
  })

  it('renders quick action buttons', () => {
    renderWithQuery(<ChatPanel projectId="p1" jobId="j1" />)
    expect(screen.getByText('Replan')).toBeInTheDocument()
    expect(screen.getByText('Subtitles')).toBeInTheDocument()
    expect(screen.getByText('Voiceover')).toBeInTheDocument()
    expect(screen.getByText('Refine')).toBeInTheDocument()
  })

  it('disables send when no job', () => {
    renderWithQuery(<ChatPanel projectId="p1" jobId={null} />)
    const sendButton = screen.getByRole('button', { name: 'Send' })
    expect(sendButton).toBeDisabled()
  })

  it('renders input textarea', () => {
    renderWithQuery(<ChatPanel projectId="p1" jobId="j1" />)
    expect(screen.getByPlaceholderText('Describe your changes...')).toBeInTheDocument()
  })

  it('shows platform and style info when goal provided', () => {
    renderWithQuery(
      <ChatPanel
        projectId="p1"
        jobId="j1"
        goal={{ prompt: '', platform: 'douyin', style: 'lively', target_duration: 30, aspect_ratio: '9:16', selling_points: null, product_name: null, voiceover_requested: false, subtitle_requested: true, bgm_requested: false }}
      />,
    )
    expect(screen.getByText(/douyin/)).toBeInTheDocument()
  })
})
