import * as React from 'react';

export interface ColorFieldProps
  extends Omit<
    React.InputHTMLAttributes<HTMLInputElement>,
    'className' | 'type' | 'onChange' | 'value'
  > {
  /** `#rrggbb`, the only format the native control takes. */
  value?: string;
  onValueChange?: (value: string) => void;
  label?: React.ReactNode;
  description?: React.ReactNode;
  error?: React.ReactNode;
  /** Wrapper class, as in `Input` and `Select`. */
  className?: string;
}

/**
 * A colour picker: the native `<input type="color">` on purpose (no picker beats the
 * system's). The wrapper adds label, note, error and a `color-field` slot to style the
 * swatch, which is raw white on a dark theme otherwise.
 */
export const ColorField = React.forwardRef<HTMLInputElement, ColorFieldProps>(
  (
    { label, description, error, className, value, onValueChange, id, ...props },
    ref,
  ) => {
    const generated = React.useId();
    const inputId = id || generated;
    const descriptionId = `${inputId}-desc`;
    const errorId = `${inputId}-err`;

    const control = (
      <input
        ref={ref}
        id={inputId}
        type="color"
        data-ui="color-field"
        value={value}
        onChange={(e) => onValueChange?.(e.target.value)}
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
  },
);

ColorField.displayName = 'ColorField';
