import * as React from 'react';
import { Checkbox as BaseCheckbox } from '@base-ui/react/checkbox';

export interface CheckboxProps
  extends Omit<
    React.ComponentPropsWithoutRef<typeof BaseCheckbox.Root>,
    'className'
  > {
  /** O texto ao lado da caixa. Um nó, como no `Input` e no `Select`. */
  label?: React.ReactNode;
  /** Uma segunda linha, mais pequena e apagada, por baixo do texto. */
  description?: React.ReactNode;
  /**
   * Classe do **invólucro** (o `<label>` que embrulha a caixa e o texto), e não
   * da caixa — a mesma regra do `Input` e do `Select`. Sem isto, uma classe de
   * grelha aterrava no `<button>` da caixa e a linha desfazia-se.
   */
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
