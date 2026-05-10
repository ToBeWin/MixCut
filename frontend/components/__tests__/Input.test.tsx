import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from '@/components/ui/Input'

describe('Input', () => {
  it('renders an input element', () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('renders label when provided', () => {
    render(<Input label="Email" />)
    expect(screen.getByText('Email')).toBeInTheDocument()
  })

  it('renders error message when provided', () => {
    render(<Input error="Required field" />)
    expect(screen.getByText('Required field')).toBeInTheDocument()
  })

  it('applies error styling when error is present', () => {
    render(<Input error="Error" />)
    const input = screen.getByRole('textbox')
    expect(input.className).toContain('error')
  })

  it('is disabled when disabled prop is set', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('calls onChange handler', () => {
    const onChange = jest.fn()
    render(<Input onChange={onChange} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } })
    expect(onChange).toHaveBeenCalledTimes(1)
  })

  it('applies ghost variant', () => {
    render(<Input variant="ghost" />)
    const input = screen.getByRole('textbox')
    expect(input.className).toContain('transparent')
  })

  it('accepts custom className', () => {
    render(<Input className="custom-class" />)
    expect(document.querySelector('.custom-class')).toBeInTheDocument()
  })
})
