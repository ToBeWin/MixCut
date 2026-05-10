import { render, screen } from '@testing-library/react'
import { Skeleton, ProjectCardSkeleton, AssetCardSkeleton, DashboardSkeleton, AssetGridSkeleton } from '@/components/ui/Skeleton'

describe('Skeleton', () => {
  it('renders a div with pulse animation', () => {
    const { container } = render(<Skeleton />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('animate-pulse')
  })

  it('applies width and height classes', () => {
    const { container } = render(<Skeleton width="w-32" height="h-4" />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('w-32')
    expect(el.className).toContain('h-4')
  })

  it('applies circle class', () => {
    const { container } = render(<Skeleton circle />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('rounded-full')
  })

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="custom" />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('custom')
  })
})

describe('ProjectCardSkeleton', () => {
  it('renders a card-like structure', () => {
    const { container } = render(<ProjectCardSkeleton />)
    expect(container.querySelector('.aspect-video')).toBeInTheDocument()
  })
})

describe('AssetCardSkeleton', () => {
  it('renders a card-like structure', () => {
    const { container } = render(<AssetCardSkeleton />)
    expect(container.querySelector('.aspect-video')).toBeInTheDocument()
  })
})

describe('DashboardSkeleton', () => {
  it('renders default 6 cards', () => {
    const { container } = render(<DashboardSkeleton />)
    const cards = container.querySelectorAll('.aspect-video')
    expect(cards.length).toBe(6)
  })

  it('renders custom count', () => {
    const { container } = render(<DashboardSkeleton count={3} />)
    const cards = container.querySelectorAll('.aspect-video')
    expect(cards.length).toBe(3)
  })
})

describe('AssetGridSkeleton', () => {
  it('renders default 6 cards', () => {
    const { container } = render(<AssetGridSkeleton />)
    const cards = container.querySelectorAll('.aspect-video')
    expect(cards.length).toBe(6)
  })
})
