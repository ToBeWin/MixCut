import { render, screen, fireEvent } from '@testing-library/react'
import { Timeline } from '@/components/editor/Timeline'
import type { EditSegment } from '@/lib/api'

const mockSegments: EditSegment[] = [
  { asset_id: 'asset1', in_point: 0, out_point: 5, timeline_start: 0, speed: 1, transition_in: 'cut', volume: 1, text_overlay: null },
  { asset_id: 'asset1', in_point: 5, out_point: 10, timeline_start: 5, speed: 1, transition_in: 'cut', volume: 1, text_overlay: null },
  { asset_id: 'asset2', in_point: 0, out_point: 3, timeline_start: 10, speed: 1.5, transition_in: 'fade', volume: 1, text_overlay: null },
]

describe('Timeline', () => {
  it('renders segment count and duration', () => {
    render(<Timeline segments={mockSegments} duration={13} />)
    expect(screen.getByText(/3 segments/)).toBeInTheDocument()
    expect(screen.getByText(/13s/)).toBeInTheDocument()
  })

  it('renders empty state with 0 segments', () => {
    render(<Timeline segments={[]} duration={30} />)
    expect(screen.getByText(/0 segments/)).toBeInTheDocument()
  })

  it('renders segment labels', () => {
    render(<Timeline segments={mockSegments} duration={13} />)
    expect(screen.getAllByText('asset1').length).toBeGreaterThanOrEqual(1)
  })

  it('has listbox role on track area', () => {
    render(<Timeline segments={mockSegments} duration={13} />)
    expect(screen.getByRole('listbox')).toBeInTheDocument()
  })

  it('segments have option role and aria-label', () => {
    render(<Timeline segments={mockSegments} duration={13} />)
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(3)
    expect(options[0]).toHaveAttribute('aria-label', expect.stringContaining('Segment 1'))
  })

  it('selects segment on click', () => {
    const onSelect = jest.fn()
    render(<Timeline segments={mockSegments} duration={13} onSegmentSelect={onSelect} />)
    const options = screen.getAllByRole('option')
    fireEvent.click(options[0])
    expect(onSelect).toHaveBeenCalledWith(mockSegments[0])
    expect(options[0]).toHaveAttribute('aria-selected', 'true')
  })

  it('deselects segment on second click', () => {
    const onSelect = jest.fn()
    render(<Timeline segments={mockSegments} duration={13} onSegmentSelect={onSelect} />)
    const options = screen.getAllByRole('option')
    fireEvent.click(options[0])
    fireEvent.click(options[0])
    expect(onSelect).toHaveBeenCalledWith(null)
  })

  it('navigates segments with arrow keys', () => {
    const onSelect = jest.fn()
    render(<Timeline segments={mockSegments} duration={13} onSegmentSelect={onSelect} />)
    const listbox = screen.getByRole('listbox')
    fireEvent.keyDown(listbox, { key: 'ArrowRight' })
    expect(onSelect).toHaveBeenCalledWith(mockSegments[0])
    fireEvent.keyDown(listbox, { key: 'ArrowRight' })
    expect(onSelect).toHaveBeenCalledWith(mockSegments[1])
  })

  it('seeks on Enter key', () => {
    const onSeek = jest.fn()
    const onSelect = jest.fn()
    render(<Timeline segments={mockSegments} duration={13} onSegmentSelect={onSelect} onSeek={onSeek} />)
    const listbox = screen.getByRole('listbox')
    fireEvent.keyDown(listbox, { key: 'ArrowRight' })
    fireEvent.keyDown(listbox, { key: 'Enter' })
    expect(onSeek).toHaveBeenCalledWith(0)
  })

  it('deselects on Escape key', () => {
    const onSelect = jest.fn()
    render(<Timeline segments={mockSegments} duration={13} onSegmentSelect={onSelect} />)
    const listbox = screen.getByRole('listbox')
    fireEvent.keyDown(listbox, { key: 'ArrowRight' })
    fireEvent.keyDown(listbox, { key: 'Escape' })
    expect(onSelect).toHaveBeenCalledWith(null)
  })

  it('shows details panel for selected segment', () => {
    render(<Timeline segments={mockSegments} duration={13} />)
    const options = screen.getAllByRole('option')
    fireEvent.click(options[2])
    expect(screen.getByText('Segment 3')).toBeInTheDocument()
    // Speed badge appears in both segment chip and details panel
    expect(screen.getAllByText('1.5x').length).toBeGreaterThanOrEqual(1)
  })
})
