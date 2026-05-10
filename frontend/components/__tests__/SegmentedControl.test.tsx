import { render, screen, fireEvent } from '@testing-library/react'
import { SegmentedControl } from '@/components/ui/SegmentedControl'

const OPTIONS = ['all', 'active', 'done'] as const

describe('SegmentedControl', () => {
  it('renders all options', () => {
    render(<SegmentedControl value="all" options={OPTIONS} onChange={jest.fn()} />)
    expect(screen.getByText('all')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
    expect(screen.getByText('done')).toBeInTheDocument()
  })

  it('highlights the selected option', () => {
    render(<SegmentedControl value="active" options={OPTIONS} onChange={jest.fn()} />)
    const active = screen.getByText('active')
    expect(active.className).toContain('accent')
  })

  it('calls onChange when option is clicked', () => {
    const onChange = jest.fn()
    render(<SegmentedControl value="all" options={OPTIONS} onChange={onChange} />)
    fireEvent.click(screen.getByText('done'))
    expect(onChange).toHaveBeenCalledWith('done')
  })

  it('does not call onChange when selected option is clicked', () => {
    const onChange = jest.fn()
    render(<SegmentedControl value="all" options={OPTIONS} onChange={onChange} />)
    fireEvent.click(screen.getByText('all'))
    expect(onChange).toHaveBeenCalledWith('all')
  })
})
