import { clsx } from "clsx";

interface SkeletonProps {
  className?: string;
  /** Width class, e.g. "w-32" */
  width?: string;
  /** Height class, e.g. "h-4" */
  height?: string;
  /** Make it circular */
  circle?: boolean;
}

export function Skeleton({ className, width, height, circle }: SkeletonProps) {
  return (
    <div
      className={clsx(
        "animate-pulse bg-[var(--surface-container)]",
        circle ? "rounded-full" : "rounded-[4px]",
        width,
        height,
        className,
      )}
    />
  );
}

/** Full project card placeholder for dashboard grid */
export function ProjectCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-[6px] border border-[var(--border)] bg-[var(--surface)]">
      <div className="relative aspect-video overflow-hidden bg-[var(--surface-lowest)]">
        <Skeleton className="absolute inset-0" />
      </div>
      <div className="p-2.5">
        <Skeleton className="mb-2 h-4 w-3/4" />
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-20" />
        </div>
      </div>
    </div>
  );
}

/** Asset card placeholder for asset browser grid */
export function AssetCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-[4px] border border-[var(--border)] bg-[var(--surface-low)]">
      <div className="relative aspect-video overflow-hidden bg-[var(--surface-lowest)]">
        <Skeleton className="absolute inset-0" />
      </div>
      <div className="p-1.5">
        <Skeleton className="mb-1 h-3 w-full" />
        <Skeleton className="h-2 w-1/2" />
      </div>
    </div>
  );
}

/** Dashboard grid skeleton */
export function DashboardSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <ProjectCardSkeleton key={i} />
      ))}
    </div>
  );
}

/** Asset browser grid skeleton */
export function AssetGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-1.5">
      {Array.from({ length: count }).map((_, i) => (
        <AssetCardSkeleton key={i} />
      ))}
    </div>
  );
}
