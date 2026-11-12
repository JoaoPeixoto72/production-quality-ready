import * as React from 'react';

export interface TextareaProps
  extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {
  label?: React.ReactNode;
  /** A short sentence below, for what the label cannot hold. */
  description?: React.ReactNode;
  error?: React.ReactNode;
  /** Wrapper class, not the field's (see `Input`). */
  className?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, description, error, className, id, ...props }, ref) => {
    // Always called; see `input.tsx`.
    const generated = React.useId();
    const textareaId = id || generated;
    const descriptionId = `${textareaId}-desc`;
    const errorId = `${textareaId}-err`;

    const control = (
      <textarea
        ref={ref}
        id={textareaId}
        data-ui="textarea"
        aria-invalid={error ? true : undefined}
        aria-describedby={
          [description ? descriptionId : null, error ? errorId : null]
            .filter(Boolean)
            .join(' ') || undefined
        }
        {...props}
      />
    );

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
          <label htmlFor={textareaId} data-ui="field-label">
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

Textarea.displayName = 'Textarea';
