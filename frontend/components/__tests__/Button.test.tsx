import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/ui/Button'

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  it('applies primary variant class', () => {
    render(<Button variant="primary">Primary</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('accent')
  })

  it('applies ghost variant class', () => {
    render(<Button variant="ghost">Ghost</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('transparent')
  })

  it('renders icon alongside children', () => {
    render(<Button icon={<span data-testid="icon">I</span>}>With Icon</Button>)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByText('With Icon')).toBeInTheDocument()
  })

  it('is disabled when disabled prop is set', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('calls onClick handler', () => {
    const onClick = jest.fn()
    render(<Button onClick={onClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('defaults to type="button"', () => {
    render(<Button>Test</Button>)
    expect(screen.getByRole('button')).toHaveAttribute('type', 'button')
  })

  it('accepts custom className', () => {
    render(<Button className="custom-class">Test</Button>)
    expect(screen.getByRole('button').className).toContain('custom-class')
  })
})
