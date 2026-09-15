import * as React from 'react';
import { useEscolhaPorSetas } from './escolha';
import { Tooltip } from './tooltip';

export interface SegmentedOption<T extends string> {
  value: T;
  /** Um nó, e não só uma string — como no `Select`. */
  label: React.ReactNode;
  /**
   * O que aparece ao passar o rato, no `Tooltip` deste catálogo e não num
   * `title` do browser.
   *
   * **Numa opção desligada não abre**, e não há volta a dar aqui: o browser não
   * entrega eventos de rato a um controlo com `disabled`, e o invólucro que
   * resolveria isso passaria a ser o item da linha de pílulas. Uma opção que
   * precise de explicar porque está desligada pede cartões (`RadioCards`), que
   * têm uma `description` à vista.
   */
  title?: React.ReactNode;
  disabled?: boolean;
}

export interface SegmentedControlProps<T extends string> {
  value: T;
  onValueChange: (value: T) => void;
  options: SegmentedOption<T>[];
  /**
   * O nome do grupo, para quem lê por som. **Não tem texto por omissão** — um
   * grupo de escolhas sem nome é uma lista de palavras soltas a meio de uma
   * página, e um componente de sistema não sabe em que língua a app está.
   */
  label: string;
  /** Classe do invólucro, como no `Select` e no `Input`. */
  className?: string;
}

/**
 * Uma escolha entre poucas, em pílulas na mesma linha.
 *
 * É um `radiogroup` de `<button>`s; o porquê e a mecânica do teclado estão no
 * `escolha.ts`, que esta e os `RadioCards` partilham.
 *
 * **Quando é que se usa isto e não os `RadioCards`:** quando cada opção se
 * explica pelo próprio nome. Uma linha de sete pílulas diz «16:9» e acabou; se
 * for preciso uma frase por opção — quem não sabe o que é um Matroska não
 * decide por um nome de três letras —, são cartões.
 */
export function SegmentedControl<T extends string>({
  value,
  onValueChange,
  options,
  label,
  className,
}: SegmentedControlProps<T>) {
  const { grupo, aoTeclar } = useEscolhaPorSetas(value, options, onValueChange);

  return (
    <div
      ref={grupo}
      data-ui="segmented"
      role="radiogroup"
      aria-label={label}
      className={className}
      onKeyDown={aoTeclar}
    >
      {options.map((o) => {
        const escolhida = o.value === value;
        const pilula = (
          <button
            type="button"
            role="radio"
            aria-checked={escolhida}
            data-ui="segmented-item"
            data-value={o.value}
            disabled={o.disabled}
            tabIndex={escolhida ? 0 : -1}
            onClick={() => onValueChange(o.value)}
          >
            {o.label}
          </button>
        );
        // Sem `title`, sai a pílula nua: o `Tooltip` cola-se por dentro do
        // filho, mas um `Root` por pílula é estado que não faz falta nenhuma
        // numa linha de sete.
        return o.title === undefined || o.title === '' ? (
          <React.Fragment key={o.value}>{pilula}</React.Fragment>
        ) : (
          <Tooltip key={o.value} content={o.title}>
            {pilula}
          </Tooltip>
        );
      })}
    </div>
  );
}

SegmentedControl.displayName = 'SegmentedControl';
