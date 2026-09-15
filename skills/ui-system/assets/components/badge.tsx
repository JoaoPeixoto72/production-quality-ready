import * as React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'solid' | 'flat' | 'bordered';
  color?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  /**
   * `sm | md | lg`, como no `Button`, no `Chip` e no `Progress` — e como no
   * HeroUI. Tinha `small | medium`, que era o único sítio do catálogo a
   * escrever os tamanhos por extenso.
   */
  size?: 'sm' | 'md' | 'lg';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'flat', color = 'default', size = 'md', ...props }, ref) => {
    return (
      <span
        ref={ref}
        data-ui="badge"
        data-variant={variant}
        data-color={color}
        data-size={size}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';
