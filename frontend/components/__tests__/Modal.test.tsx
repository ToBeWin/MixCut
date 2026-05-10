import { render, screen, fireEvent } from '@testing-library/react'
import { Modal } from '@/components/ui/Modal'

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(<Modal open={false} onClose={() => {}}>Content</Modal>)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders dialog when open', () => {
    render(<Modal open={true} onClose={() => {}}>Content</Modal>)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders title', () => {
    render(<Modal open={true} onClose={() => {}} title="Test Title">Content</Modal>)
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })

  it('has aria-modal and aria-label', () => {
    render(<Modal open={true} onClose={() => {}} title="My Modal">Content</Modal>)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-label', 'My Modal')
  })

  it('calls onClose when pressing Escape', () => {
    const onClose = jest.fn()
    render(<Modal open={true} onClose={onClose}>Content</Modal>)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when clicking backdrop', () => {
    const onClose = jest.fn()
    render(<Modal open={true} onClose={onClose}>Content</Modal>)
    // The backdrop is the outer div with the click handler
    const backdrop = screen.getByRole('dialog').firstChild as HTMLElement
    fireEvent.click(backdrop)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('renders close button with aria-label', () => {
    render(<Modal open={true} onClose={() => {}} title="Test">Content</Modal>)
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument()
  })

  it('renders footer when provided', () => {
    render(
      <Modal open={true} onClose={() => {}} footer={<button>Save</button>}>
        Content
      </Modal>,
    )
    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument()
  })
})
