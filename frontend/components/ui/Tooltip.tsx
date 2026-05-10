"use client";

import { clsx } from "clsx";
import { useCallback, useRef, useState, type ReactNode } from "react";

type TooltipPosition = "top" | "bottom" | "left" | "right";

type TooltipProps = {
  content: string;
  position?: TooltipPosition;
  children: ReactNode;
  delayMs?: number;
};

const positionClass: Record<TooltipPosition, string> = {
  top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
  bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
  left: "right-full top-1/2 -translate-y-1/2 mr-2",
  right: "left-full top-1/2 -translate-y-1/2 ml-2",
};

const arrowClass: Record<TooltipPosition, string> = {
  top: "bottom-[-4px] left-1/2 -translate-x-1/2 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-[var(--surface-high)]",
  bottom: "top-[-4px] left-1/2 -translate-x-1/2 border-l-[4px] border-r-[4px] border-b-[4px] border-l-transparent border-r-transparent border-b-[var(--surface-high)]",
  left: "right-[-4px] top-1/2 -translate-y-1/2 border-t-[4px] border-b-[4px] border-l-[4px] border-t-transparent border-b-transparent border-l-[var(--surface-high)]",
  right: "left-[-4px] top-1/2 -translate-y-1/2 border-t-[4px] border-b-[4px] border-r-[4px] border-t-transparent border-b-transparent border-r-[var(--surface-high)]",
};

export function Tooltip({ content, position = "top", children, delayMs = 150 }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = useCallback(() => {
    timeoutRef.current = setTimeout(() => setVisible(true), delayMs);
  }, [delayMs]);

  const hide = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setVisible(false);
  }, []);

  return (
    <div className="relative inline-flex" onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      {children}
      {visible && (
        <div
          className={clsx(
            "pointer-events-none absolute z-50 whitespace-nowrap rounded-[4px] bg-[var(--surface-high)] px-2 py-1 text-[10px] font-medium text-[var(--on-surface)] shadow-[0_4px_12px_rgba(0,0,0,0.3)] animate-[fadeIn_100ms_ease-out]",
            positionClass[position],
          )}
          role="tooltip"
        >
          {content}
          <span className={clsx("absolute h-0 w-0 border-solid", arrowClass[position])} />
        </div>
      )}
    </div>
  );
}