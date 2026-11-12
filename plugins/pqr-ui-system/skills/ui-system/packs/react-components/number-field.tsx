import * as React from 'react';
import { NumberField as BaseNumberField } from '@base-ui/react/number-field';

export interface NumberFieldProps {
  value?: number | null;
  defaultValue?: number;
  /** Already clamped to `min`/`max` by Base UI. `null` is the empty field, not zero. */
  onValueChange?: (value: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  /** Number format. A ratio side, a year or a port takes `{ useGrouping: false }` (no `1,000`). */
  format?: Intl.NumberFormatOptions;
  label?: React.ReactNode;
  description?: React.ReactNode;
  error?: React.ReactNode;
  disabled?: boolean;
  readOnly?: boolean;
  placeholder?: string;
  /** − and + buttons. Off by default: arrows and the wheel step without taking space. */
  withButtons?: boolean;
  /** Wrapper class, as in `Input` and `Select`. */
  className?: string;
}

/** A real number field, not `<input type="number">`: clamped, stepped by arrows and wheel, parsed in the user's locale. */
export function NumberField({
  value,
  defaultValue,
  onValueChange,
  min,
  max,
  step,
  format,
  label,
  description,
  error,
  disabled,
  readOnly,
  placeholder,
  withButtons = false,
  className,
}: NumberFieldProps) {
  const id = React.useId();
  const inputId = `${id}-input`;
  const descriptionId = `${id}-desc`;
  const errorId = `${id}-err`;

  const control = (
    <BaseNumberField.Root
      id={id}
      value={value}
      defaultValue={defaultValue}
      onValueChange={(v) => onValueChange?.(v)}
      min={min}
      max={max}
      step={step}
      format={format}
      disabled={disabled}
      readOnly={readOnly}
      data-ui="number-field"
    >
      <BaseNumberField.Group data-ui="number-field-group">
        {withButtons && (
          <BaseNumberField.Decrement data-ui="number-field-decrement">
            −
          </BaseNumberField.Decrement>
        )}
        <BaseNumberField.Input
          id={inputId}
          data-ui="number-field-input"
          placeholder={placeholder}
          aria-invalid={error ? true : undefined}
          aria-describedby={
            [description ? descriptionId : null, error ? errorId : null]
              .filter(Boolean)
              .join(' ') || undefined
          }
        />
        {withButtons && (
          <BaseNumberField.Increment data-ui="number-field-increment">
            +
          </BaseNumberField.Increment>
        )}
      </BaseNumberField.Group>
    </BaseNumberField.Root>
  );

  // Bare field without label or note, as in `Input`: it may live inside another row.
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

NumberField.displayName = 'NumberField';
