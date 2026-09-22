import * as React from 'react';
import { useEscolhaPorSetas } from './escolha';
import { Tooltip } from './tooltip';

export interface RadioCardOption<T extends string> {
  value: T;
  /** O nome da opção. */
  title: React.ReactNode;
  /**
   * A frase por baixo do nome. É o que justifica o cartão existir em vez de uma
   * pílula: se a opção se explica pelo próprio nome, é um `SegmentedControl`.
   */
  description?: React.ReactNode;
  /**
   * Uma coisa para olhar, por cima do nome — uma amostra do filtro, o desenho
   * de uma legenda. **É a outra razão para um cartão**: um nome numa lista
   * obriga a escolher às cegas e a esperar para saber.
   */
  media?: React.ReactNode;
  disabled?: boolean;
  /**
   * O que aparece ao passar o rato, no `Tooltip` deste catálogo e não num
   * `title` do browser.
   *
   * **Num cartão desligado não abre** — o browser não entrega eventos de rato a
   * um controlo com `disabled`, e o invólucro que resolveria isso passava a ser
   * o item da grelha. Para dizer *porque* é que um cartão está desligado há a
   * `description`, que está à vista e não precisa do rato.
   */
  hint?: React.ReactNode;
}

export interface RadioCardsProps<T extends string> {
  value: T;
  onValueChange: (value: T) => void;
  options: RadioCardOption<T>[];
  /**
   * O nome do grupo, para quem lê por som. **Sem texto por omissão**, pela
   * mesma razão do `SegmentedControl`.
   */
  label: string;
  /** Classe do invólucro — é por ela que a grelha se decide. */
  className?: string;
}

/**
 * Uma escolha entre poucas, em cartões.
 *
 * **Um cartão e não uma pílula quando há alguma coisa para ler ou para olhar.**
 * Um filtro é uma coisa que se vê, e um nome numa lista («Desbotado — filme
 * gasto») obrigava a escolher às cegas; um formato de vídeo precisa de uma
 * frase, porque três letras não explicam um recipiente.
 *
 * É um `radiogroup` de `<button>`s; o porquê e a mecânica do teclado estão no
 * `escolha.ts`.
 */
export function RadioCards<T extends string>({
  value,
  onValueChange,
  options,
  label,
  className,
}: RadioCardsProps<T>) {
  const { grupo, aoTeclar } = useEscolhaPorSetas(value, options, onValueChange);

  return (
    <div
      ref={grupo}
      data-ui="radio-cards"
      role="radiogroup"
      aria-label={label}
      className={className}
      onKeyDown={aoTeclar}
    >
      {options.map((o) => {
        const escolhido = o.value === value;
        const cartao = (
          <button
            type="button"
            role="radio"
            aria-checked={escolhido}
            data-ui="radio-card"
            data-value={o.value}
            disabled={o.disabled}
            tabIndex={escolhido ? 0 : -1}
            onClick={() => onValueChange(o.value)}
          >
            {o.media && <span data-ui="radio-card-media">{o.media}</span>}
            <span data-ui="radio-card-title">{o.title}</span>
            {o.description && (
              <span data-ui="radio-card-description">{o.description}</span>
            )}
          </button>
        );
        // Sem `hint`, sai o cartão nu — um `Tooltip.Root` por cartão numa
        // grelha de nove é estado que não faz falta a ninguém.
        return o.hint === undefined || o.hint === '' ? (
          <React.Fragment key={o.value}>{cartao}</React.Fragment>
        ) : (
          <Tooltip key={o.value} content={o.hint}>
            {cartao}
          </Tooltip>
        );
      })}
    </div>
  );
}

RadioCards.displayName = 'RadioCards';
