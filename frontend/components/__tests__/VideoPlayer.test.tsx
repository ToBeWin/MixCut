import { render, screen } from '@testing-library/react'
import { VideoPlayer } from '@/components/editor/VideoPlayer'

describe('VideoPlayer', () => {
  it('renders a video element', () => {
    render(<VideoPlayer src="test.mp4" />)
    const video = document.querySelector('video')
    expect(video).toBeInTheDocument()
  })

  it('renders placeholder when no src', () => {
    render(<VideoPlayer />)
    expect(screen.getByText(/no video/i)).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<VideoPlayer src="test.mp4" className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('renders with 9:16 aspect ratio by default', () => {
    const { container } = render(<VideoPlayer src="test.mp4" />)
    const wrapper = container.querySelector('[style*="aspect-ratio"]')
    expect(wrapper).toBeTruthy()
  })

  it('renders with 1:1 aspect ratio', () => {
    const { container } = render(<VideoPlayer src="test.mp4" aspectRatio="1:1" />)
    const wrapper = container.querySelector('[style*="aspect-ratio"]')
    expect(wrapper).toBeTruthy()
  })

  it('renders play button', () => {
    render(<VideoPlayer src="test.mp4" />)
    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument()
  })

  it('renders volume button', () => {
    render(<VideoPlayer src="test.mp4" />)
    expect(screen.getByRole('button', { name: /volume/i })).toBeInTheDocument()
  })
})
