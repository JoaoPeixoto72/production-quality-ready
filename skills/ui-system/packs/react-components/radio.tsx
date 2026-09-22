import * as React from 'react';
import { RadioGroup as BaseRadioGroup } from '@base-ui/react/radio-group';
import { Radio as BaseRadio } from '@base-ui/react/radio';

export interface RadioGroupProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  /** A etiqueta do grupo. Um nó, como no `Select`. */
  label?: React.ReactNode;
  description?: React.ReactNode;
  /**
   * O nome do grupo para quem lê por som, quando não há `label` à vista. Um
   * grupo de escolhas sem nome é uma lista de palavras soltas a meio de uma
   * página.
   */
  'aria-label'?: string;
  disabled?: boolean;
  /** Classe do **invólucro**, como no `Input` e no `Select`. */
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
      // O Base UI entrega `unknown` (o valor pode ser qualquer coisa) e um
      // segundo argumento com o evento. Cá fora a assinatura fica simples, como
      // no `Select`.
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
  /** O nome da opção. Um nó, como no resto do catálogo. */
  label?: React.ReactNode;
  /** A frase por baixo do nome. */
  description?: React.ReactNode;
  /** Classe do **invólucro** (o `<label>` que embrulha o ponto e o texto). */
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
