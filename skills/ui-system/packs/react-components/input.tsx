import * as React from 'react';

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'className'> {
  /**
   * A etiqueta por cima do campo. Um nó e não uma string, como no `Select`:
   * há etiquetas que levam um valor a negrito ao lado do nome.
   */
  label?: React.ReactNode;
  /** Uma frase curta por baixo, para o que não cabe na etiqueta. */
  description?: React.ReactNode;
  error?: React.ReactNode;
  /**
   * Classe do **invólucro**, e não do campo — a mesma regra do `Select`, para
   * que uma app com grelha própria a possa pôr onde ela conta.
   */
  className?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, description, error, className, id, ...props }, ref) => {
    // **Sempre chamado**, e só depois é que se escolhe. Um `id || useId()`
    // salta o hook quando o `id` vem de fora, e no dia em que um componente
    // passa a dar `id` a meio da vida — de indefinido para definido — a ordem
    // dos hooks muda e o React estoira com "rendered fewer hooks than
    // expected". Custa nada e tira o pé da armadilha.
    const gerado = React.useId();
    const inputId = id || gerado;
    const descriptionId = `${inputId}-desc`;
    const errorId = `${inputId}-err`;

    const control = (
      <input
        ref={ref}
        id={inputId}
        data-ui="input"
        // `undefined` e não `false`: sem erro, o atributo não chega a existir.
        // Um `aria-invalid="false"` em cada campo da app é ruído que os
        // leitores de ecrã têm de atravessar para chegar ao que interessa.
        aria-invalid={error ? true : undefined}
        aria-describedby={
          [description ? descriptionId : null, error ? errorId : null]
            .filter(Boolean)
            .join(' ') || undefined
        }
        {...props}
      />
    );

    // **Sem etiqueta nem nota, sai o campo nu.** Há sítios onde ele vive dentro
    // de uma linha com um botão ao lado, e um invólucro a mais aí parte a
    // grelha de quem o chamou — o `Select` faz o mesmo, pela mesma razão.
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
