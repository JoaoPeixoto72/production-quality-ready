import * as React from 'react';

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'className'> {
  label?: React.ReactNode;
  /** A short sentence below, for what the label cannot hold. */
  description?: React.ReactNode;
  error?: React.ReactNode;
  /** Wrapper class, not the input's — as in `Select`. */
  className?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, description, error, className, id, ...props }, ref) => {
    // Always called: `id || useId()` would change the hook order when `id` appears mid-life.
    const generated = React.useId();
    const inputId = id || generated;
    const descriptionId = `${inputId}-desc`;
    const errorId = `${inputId}-err`;

    const control = (
      <input
        ref={ref}
        id={inputId}
        data-ui="input"
        // `undefined`, not `false`: no attribute at all without an error.
        aria-invalid={error ? true : undefined}
        aria-describedby={
          [description ? descriptionId : null, error ? errorId : null]
            .filter(Boolean)
            .join(' ') || undefined
        }
        {...props}
      />
    );

    // Bare input without label or note: it may live inside a row with a button.
    if (!label && !description && !error) {
      return className ? (
        <div data-ui="field" className={className}>
          {control}
        </div>
      ) : (
        control
      );
    }

    return (
      <div data-ui="field" className={className}>
        {label && (
          <label htmlFor={inputId} data-ui="field-label">
            {label}
          </label>
        )}
        {control}
        {description && !error && (
          <p id={descriptionId} data-ui="field-description">
            {description}
          </p>
        )}
        {error && (
          <p id={errorId} data-ui="field-error" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
