import * as React from 'react';
import { Checkbox as BaseCheckbox } from '@base-ui/react/checkbox';

export interface CheckboxProps
  extends Omit<
    React.ComponentPropsWithoutRef<typeof BaseCheckbox.Root>,
    'className'
  > {
  /** The text beside the box. */
  label?: React.ReactNode;
  /** A smaller, dimmer second line under the text. */
  description?: React.ReactNode;
  /** Wrapper class (the `<label>` around box and text), not the box's. */
  className?: string;
}

export const Checkbox = React.forwardRef<HTMLButtonElement, CheckboxProps>(
  ({ label, description, className, id, children, ...props }, ref) => {
    return (
      <label data-ui="checkbox-label" className={className}>
        <BaseCheckbox.Root ref={ref} id={id} data-ui="checkbox" {...props}>
          <BaseCheckbox.Indicator data-ui="checkbox-indicator">
            ✓
          </BaseCheckbox.Indicator>
        </BaseCheckbox.Root>
        {(label || children || description) && (
          <div data-ui="checkbox-text-wrapper">
            {(label || children) && (
              <span data-ui="checkbox-text">{label || children}</span>
            )}
            {description && (
              <span data-ui="checkbox-description">{description}</span>
            )}
          </div>
        )}
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';

export interface CheckboxGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string;
  description?: string;
  error?: string;
}

export function CheckboxGroup({
  label,
  description,
  error,
  children,
  ...props
}: CheckboxGroupProps) {
  return (
    <div data-ui="checkbox-group" role="group" {...props}>
      {label && <span data-ui="checkbox-group-label">{label}</span>}
      <div data-ui="checkbox-group-items">{children}</div>
      {description && !error && (
        <span data-ui="checkbox-group-description">{description}</span>
      )}
      {error && <span data-ui="checkbox-group-error" role="alert">{error}</span>}
    </div>
  );
}
