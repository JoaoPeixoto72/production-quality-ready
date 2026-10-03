import * as React from 'react';
import { Tooltip as BaseTooltip } from '@base-ui/react/tooltip';

/** Base UI's `Tooltip.Arrow` is an empty `<div>`: this shape gives `core.css`'s `color` something to fill. */
function Arrow() {
  return (
    <svg width="10" height="5" viewBox="0 0 10 5" aria-hidden="true">
      <path d="M0 5 L5 0 L10 5 Z" fill="currentColor" />
    </svg>
  );
}

export interface TooltipProps {
  content: React.ReactNode;
  /**
   * One element; the tooltip attaches inside it (Base UI `render`), so no extra
   * `<button>` wraps it. A disabled child gets no mouse events: wrap it in a box
   * with its own layout (not `display: contents`) to give it a tooltip.
   */
  children: React.ReactElement;
  /** Side of the trigger; flips when it does not fit. */
  placement?: 'top' | 'bottom' | 'left' | 'right';
  align?: 'start' | 'center' | 'end';
  /** Distance to the trigger; larger with an arrow (HeroUI's two values). */
  offset?: number;
  /** @default false */
  showArrow?: boolean;
  /** Hover time before opening, ms. */
  delay?: number;
  /** Time it stays after the pointer leaves, ms. */
  closeDelay?: number;
  /** Never opens, by pointer or focus. */
  isDisabled?: boolean;
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
}

/**
 * The browser `title` replacement: themed, and shown on keyboard focus too. A
 * `role="tooltip"` tied by `aria-describedby` — a description, not a name, so an
 * icon-only button still needs its `aria-label`.
 */
export function Tooltip({
  content,
  children,
  placement = 'top',
  align = 'center',
  offset,
  showArrow = false,
  delay = 700,
  closeDelay = 0,
  isDisabled = false,
  open,
  defaultOpen,
  onOpenChange,
  className,
}: TooltipProps) {
  return (
    <BaseTooltip.Root
      open={open}
      defaultOpen={defaultOpen}
      onOpenChange={onOpenChange}
      disabled={isDisabled}
    >
      {/* No `data-ui`: the trigger is the child, and its own slot must survive. */}
      <BaseTooltip.Trigger
        delay={delay}
        closeDelay={closeDelay}
        render={children}
      />
      <BaseTooltip.Portal>
        <BaseTooltip.Positioner
          side={placement}
          align={align}
          sideOffset={offset ?? (showArrow ? 7 : 3)}
          data-ui="tooltip-positioner"
        >
          <BaseTooltip.Popup data-ui="tooltip-popup" className={className}>
            {showArrow && (
              <BaseTooltip.Arrow data-ui="tooltip-arrow">
                <Arrow />
              </BaseTooltip.Arrow>
            )}
            {content}
          </BaseTooltip.Popup>
        </BaseTooltip.Positioner>
      </BaseTooltip.Portal>
    </BaseTooltip.Root>
  );
}
