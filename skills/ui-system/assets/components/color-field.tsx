import * as React from 'react';

export interface ColorFieldProps
  extends Omit<
    React.InputHTMLAttributes<HTMLInputElement>,
    'className' | 'type' | 'onChange' | 'value'
  > {
  /** A cor, em `#rrggbb`. É o único formato que o controlo nativo aceita. */
  value?: string;
  onValueChange?: (value: string) => void;
  label?: React.ReactNode;
  description?: React.ReactNode;
  error?: React.ReactNode;
  /** Classe do **invólucro**, como no `Input` e no `Select`. */
  className?: string;
}

/**
 * Escolher uma cor.
 *
 * **É o `<input type="color">` nativo por dentro, e é de propósito.** Ao
 * contrário dos outros controlos deste catálogo, aqui não há nada do Base UI a
 * substituir: escolher uma cor sem o controlo do sistema obrigava a escrever um
 * seletor inteiro — roda, saturação, canal alfa, campo hexadecimal — e nenhum
 * deles é melhor do que aquele que quem usa já conhece do resto do sistema.
 *
 * O que este invólucro dá é o resto: a etiqueta, a nota, o erro e um slot
 * (`data-ui="color-field"`) por onde se lhe pode mexer no aspecto — porque o
 * quadrado que o browser desenha sozinho não tem cor de fundo nenhuma e, sobre
 * um tema escuro, aparece como um rectângulo branco cru.
 */
export const ColorField = React.forwardRef<HTMLInputElement, ColorFieldProps>(
  (
    { label, description, error, className, value, onValueChange, id, ...props },
    ref,
  ) => {
    const gerado = React.useId();
    const inputId = id || gerado;
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
