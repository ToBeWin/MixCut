import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastProvider, useToast } from '@/components/ui/Toast'

function TestComponent() {
  const { addToast } = useToast()
  return (
    <div>
      <button onClick={() => addToast('Success message', 'success')}>Success</button>
      <button onClick={() => addToast('Error message', 'error')}>Error</button>
      <button onClick={() => addToast('Info message', 'info')}>Info</button>
    </div>
  )
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <TestComponent />
    </ToastProvider>
  )
}

describe('Toast', () => {
  it('renders success toast', async () => {
    const user = userEvent.setup()
    renderWithProvider()
    await user.click(screen.getByText('Success'))
    expect(screen.getByText('Success message')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders error toast', async () => {
    const user = userEvent.setup()
    renderWithProvider()
    await user.click(screen.getByText('Error'))
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('renders info toast', async () => {
    const user = userEvent.setup()
    renderWithProvider()
    await user.click(screen.getByText('Info'))
    expect(screen.getByText('Info message')).toBeInTheDocument()
  })

  it('dismisses toast on click', async () => {
    const user = userEvent.setup()
    renderWithProvider()
    await user.click(screen.getByText('Success'))
    expect(screen.getByText('Success message')).toBeInTheDocument()
    await user.click(screen.getByLabelText('Dismiss'))
    expect(screen.queryByText('Success message')).not.toBeInTheDocument()
  })

  it('throws when useToast is used outside provider', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<TestComponent />)).toThrow('useToast must be used within a ToastProvider')
    spy.mockRestore()
  })
})
