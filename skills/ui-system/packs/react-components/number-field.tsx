import * as React from 'react';
import { NumberField as BaseNumberField } from '@base-ui/react/number-field';

export interface NumberFieldProps {
  value?: number | null;
  defaultValue?: number;
  /**
   * O valor já **limitado ao intervalo**: o Base UI corrige o que sai fora de
   * `min`/`max` antes de chegar aqui. `null` é o campo vazio, e não zero — quem
   * chama decide o que fazer com ele.
   */
  onValueChange?: (value: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  /**
   * Como o número se escreve. **Nem todo o número é uma quantidade**: um lado
   * de uma proporção, um ano ou um número de porta não levam separador de
   * milhares, e `{ useGrouping: false }` é o que o tira. Sem isto, um `1000`
   * aparece como `1,000` — que numa interface portuguesa se lê como um valor a
   * seguir a uma vírgula decimal.
   */
  format?: Intl.NumberFormatOptions;
  /** A etiqueta por cima do campo. Um nó, como no `Input` e no `Select`. */
  label?: React.ReactNode;
  description?: React.ReactNode;
  error?: React.ReactNode;
  disabled?: boolean;
  readOnly?: boolean;
  placeholder?: string;
  /**
   * Os botões de somar e subtrair, um de cada lado do campo. **Ficam
   * desligados por omissão**: um campo estreito com dois botões agarrados fica
   * com mais botão do que número, e o teclado (as setas) e a roda do rato
   * fazem o mesmo sem ocupar espaço nenhum.
   */
  withButtons?: boolean;
  /** Classe do **invólucro**, como no `Input` e no `Select`. */
  className?: string;
}

/**
 * Um campo de número a sério, e não um `<input type="number">`.
 *
 * O que ele traz que o nativo não tem: o valor fica **preso ao intervalo** sem
 * ninguém escrever a conta, as setas do teclado e a roda do rato andam de passo
 * em passo, e o que se escreve à mão é lido na língua de quem escreve. O
 * nativo, além disso, desenha um par de setas minúsculas que muda de aspecto em
 * cada sistema.
 */
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

  // Sem etiqueta nem nota, sai o campo nu — a mesma degradação do `Input`, e
  // pela mesma razão: há sítios onde ele vive dentro de uma linha de outra
  // coisa, e um invólucro a mais parte essa linha.
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
