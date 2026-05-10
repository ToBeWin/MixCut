import { render, screen } from '@testing-library/react'
import { Progress } from '@/components/ui/Progress'

describe('Progress', () => {
  it('renders a progressbar', () => {
    render(<Progress value={50} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('sets correct aria attributes', () => {
    render(<Progress value={75} />)
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '75')
    expect(bar).toHaveAttribute('aria-valuemin', '0')
    expect(bar).toHaveAttribute('aria-valuemax', '100')
  })

  it('clamps value to 0-100', () => {
    render(<Progress value={150} />)
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '100')
  })

  it('clamps negative value to 0', () => {
    render(<Progress value={-10} />)
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '0')
  })

  it('renders label when provided', () => {
    render(<Progress value={50} label="Upload progress" />)
    expect(screen.getByText('Upload progress')).toBeInTheDocument()
  })

  it('renders percentage when label is provided', () => {
    render(<Progress value={60} label="Loading" />)
    expect(screen.getByText('60%')).toBeInTheDocument()
  })

  it('applies accent variant', () => {
    const { container } = render(<Progress value={50} variant="accent" />)
    const bar = container.querySelector('[style*="width"]')
    expect(bar?.className).toContain('accent')
  })

  it('applies success variant', () => {
    const { container } = render(<Progress value={100} variant="success" />)
    const bar = container.querySelector('[style*="width"]')
    expect(bar?.className).toContain('ok')
  })
})
