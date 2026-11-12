import * as React from 'react';

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  label?: string;
}

export const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
  ({ size = 'md', color = 'primary', label, ...props }, ref) => {
    return (
      <div
        ref={ref}
        data-ui="spinner"
        data-size={size}
        data-color={color}
        role="status"
        aria-label={label || 'A carregar...'}
        {...props}
      >
        <span data-ui="spinner-circle" aria-hidden="true" />
        {label && <span data-ui="spinner-label">{label}</span>}
      </div>
    );
  }
);

Spinner.displayName = 'Spinner';
