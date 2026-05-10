import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/ui/Badge'

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge>Active</Badge>)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('applies default gray tone', () => {
    render(<Badge>Test</Badge>)
    const badge = screen.getByText('Test')
    expect(badge.className).toContain('--muted')
  })

  it('applies cyan tone', () => {
    render(<Badge tone="cyan">Cyan</Badge>)
    const badge = screen.getByText('Cyan')
    expect(badge.className).toContain('--cyan')
  })

  it('applies green tone', () => {
    render(<Badge tone="green">Success</Badge>)
    const badge = screen.getByText('Success')
    expect(badge.className).toContain('--ok')
  })

  it('applies red tone', () => {
    render(<Badge tone="red">Error</Badge>)
    const badge = screen.getByText('Error')
    expect(badge.className).toContain('--error')
  })

  it('accepts custom className', () => {
    render(<Badge className="extra-class">Test</Badge>)
    const badge = screen.getByText('Test')
    expect(badge.className).toContain('extra-class')
  })
})
