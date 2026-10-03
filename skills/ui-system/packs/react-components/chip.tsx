import * as React from 'react';

export interface ChipProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'onClick'> {
  variant?: 'solid' | 'flat' | 'bordered' | 'dot';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  /** A boolean makes the chip a toggle (`<button aria-pressed>`); without it, a plain `<span>` label. */
  pressed?: boolean;
  onClick?: React.MouseEventHandler<HTMLElement>;
  /** Shows a `×` that calls this. Not with `pressed`: a button inside a button is invalid HTML. */
  onClose?: () => void;
  /** The `×`'s accessible name. No default: a system component does not know the app's language. */
  closeLabel?: string;
  /** Drawn inside the `×`. Default `✕`. */
  closeIcon?: React.ReactNode;
  avatar?: React.ReactNode;
}

export const Chip = React.forwardRef<HTMLElement, ChipProps>(
  (
    {
      variant = 'flat',
      color = 'default',
      size = 'md',
      pressed,
      onClose,
      closeLabel,
      closeIcon,
      avatar,
      children,
      ...props
    },
    ref
  ) => {
    const toggle = pressed !== undefined;
    const Tag = (toggle ? 'button' : 'span') as 'span';

    return (
      <Tag
        ref={ref as React.Ref<HTMLSpanElement>}
        data-ui="chip"
        data-variant={variant}
        data-color={color}
        data-size={size}
        {...(toggle ? { type: 'button' as const, 'aria-pressed': pressed } : {})}
        {...props}
      >
        {variant === 'dot' && <span data-ui="chip-dot" aria-hidden="true" />}
        {avatar && <span data-ui="chip-avatar">{avatar}</span>}
        <span data-ui="chip-content">{children}</span>
        {onClose && !toggle && (
          <button
            type="button"
            data-ui="chip-close-btn"
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            aria-label={closeLabel}
          >
            {closeIcon ?? '✕'}
          </button>
        )}
      </Tag>
    );
  }
);

Chip.displayName = 'Chip';
