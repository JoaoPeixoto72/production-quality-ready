import * as React from 'react';
import { RadioGroup as BaseRadioGroup } from '@base-ui/react/radio-group';
import { Radio as BaseRadio } from '@base-ui/react/radio';

export interface RadioGroupProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  label?: React.ReactNode;
  description?: React.ReactNode;
  /** The group's accessible name when no visible `label`. */
  'aria-label'?: string;
  disabled?: boolean;
  /** Wrapper class, as in `Input` and `Select`. */
  className?: string;
  children: React.ReactNode;
}

export function RadioGroup({
  value,
  defaultValue,
  onValueChange,
  label,
  description,
  disabled,
  className,
  children,
  ...props
}: RadioGroupProps) {
  return (
    <BaseRadioGroup
      value={value}
      defaultValue={defaultValue}
      // Base UI sends `unknown`; callers get a string, as in `Select`.
      onValueChange={(v) => onValueChange?.(String(v))}
      disabled={disabled}
      data-ui="radio-group"
      className={className}
      aria-label={props['aria-label']}
    >
      {label && <span data-ui="radio-group-label">{label}</span>}
      <div data-ui="radio-group-items">{children}</div>
      {description && (
        <span data-ui="radio-group-description">{description}</span>
      )}
    </BaseRadioGroup>
  );
}

export interface RadioProps
  extends Omit<
    React.ComponentPropsWithoutRef<typeof BaseRadio.Root>,
    'className'
  > {
  label?: React.ReactNode;
  /** The sentence under the name. */
  description?: React.ReactNode;
  /** Wrapper class (the `<label>` around dot and text). */
  className?: string;
}

export const Radio = React.forwardRef<HTMLButtonElement, RadioProps>(
  ({ label, description, className, id, children, ...props }, ref) => {
    return (
      <label data-ui="radio-label" className={className}>
        <BaseRadio.Root ref={ref} id={id} data-ui="radio" {...props}>
          <BaseRadio.Indicator data-ui="radio-indicator" />
        </BaseRadio.Root>
        {(label || children || description) && (
          <div data-ui="radio-text-wrapper">
            {(label || children) && (
              <span data-ui="radio-text">{label || children}</span>
            )}
            {description && (
              <span data-ui="radio-description">{description}</span>
            )}
          </div>
        )}
      </label>
    );
  }
);

Radio.displayName = 'Radio';
