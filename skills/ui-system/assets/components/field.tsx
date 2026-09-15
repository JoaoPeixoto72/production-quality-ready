import * as React from 'react';

export interface FieldProps {
  /** A etiqueta por cima. Um nó, como no resto do catálogo. */
  label?: React.ReactNode;
  /** Uma frase curta por baixo, para o que não cabe na etiqueta. */
  description?: React.ReactNode;
  error?: React.ReactNode;
  /**
   * **O `id` do controlo que esta etiqueta nomeia.** Com ele, a etiqueta é um
   * `<label for>` a sério e carregar nela leva o foco ao controlo; sem ele, é um
   * `<span>` e o grupo ganha o nome pelo `aria-labelledby`.
   *
   * A escolha não é de gosto: **um `<label>` só nomeia um controlo de
   * formulário.** À volta de um grupo de `<button>`s — as fichas da qualidade,
   * os modos de captura — ele não nomeia nada, e o browser não faz nada com o
   * clique. O que essas precisam é do `aria-labelledby`, que é o que sai daqui
   * quando não há `htmlFor`.
   */
  htmlFor?: string;
  /** Classe do invólucro, como no `Input` e no `Select`. */
  className?: string;
  children: React.ReactNode;
}

/**
 * O invólucro de um campo: etiqueta, o que quer que seja, nota e erro.
 *
 * **É para o que não é um controlo só.** Um `Input` ou um `Select` já trazem
 * este invólucro por dentro — passar-lhes `label` chega. Isto é para quando o
 * que a etiqueta nomeia é uma **linha com um botão ao lado** ou um **grupo de
 * fichas**: ali não há um controlo a que uma etiqueta se possa colar, e o
 * padrão repetia-se à mão em oito sítios.
 */
export function Field({
  label,
  description,
  error,
  htmlFor,
  className,
  children,
}: FieldProps) {
  const id = React.useId();
  const labelId = `${id}-label`;

  const etiqueta =
    label &&
    (htmlFor ? (
      <label htmlFor={htmlFor} data-ui="field-label">
        {label}
      </label>
    ) : (
      <span id={labelId} data-ui="field-label">
        {label}
      </span>
    ));

  return (
    <div
      data-ui="field"
      className={className}
      // Sem `htmlFor` a etiqueta não nomeia nada por si — nomeia o grupo, e é
      // isto que o diz. Com ele, a ligação já está feita e um segundo nome aqui
      // só faria o leitor de ecrã repeti-lo.
      role={!htmlFor && label ? 'group' : undefined}
      aria-labelledby={!htmlFor && label ? labelId : undefined}
    >
      {etiqueta}
      {children}
      {description && !error && (
        <p data-ui="field-description">{description}</p>
      )}
      {error && (
        <p data-ui="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

Field.displayName = 'Field';
