import * as React from 'react';
import { Button as BaseButton } from '@base-ui/react/button';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', isLoading = false, disabled, children, ...props }, ref) => {
    return (
      <BaseButton
        ref={ref}
        data-ui="button"
        data-variant={variant}
        data-size={size}
        disabled={disabled || isLoading}
        aria-busy={isLoading ? 'true' : undefined}
        {...props}
      >
        {isLoading && (
          <span data-ui="button-spinner" aria-hidden="true">
            ⏳
          </span>
        )}
        {children}
      </BaseButton>
    );
  }
);

Button.displayName = 'Button';
