import * as React from 'react';

export interface TextareaProps
  extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {
  /** A etiqueta por cima do campo — um nó, como no `Input` e no `Select`. */
  label?: React.ReactNode;
  /** Uma frase curta por baixo, para o que não cabe na etiqueta. */
  description?: React.ReactNode;
  error?: React.ReactNode;
  /** Classe do **invólucro**, e não do campo. Ver o `Input`. */
  className?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, description, error, className, id, ...props }, ref) => {
    // Ver o `input.tsx`: o hook é sempre chamado, e a escolha vem depois.
    const gerado = React.useId();
    const textareaId = id || gerado;
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
