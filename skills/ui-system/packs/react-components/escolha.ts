import * as React from 'react';

/**
 * A mecânica de um grupo de rádio **desenhado à mão** — pílulas, cartões, o que
 * for.
 *
 * Vive aqui e não dentro de um dos dois componentes que a usam porque é a mesma
 * em ambos, e uma segunda cópia divergia na primeira vez que uma delas mudasse
 * de ideias sobre o que a seta faz no fim da lista.
 *
 * **Porque é que estes grupos não são `<input type="radio">`:** o desenho. Uma
 * pílula que se enche e um cartão com uma amostra lá dentro não têm onde pôr o
 * círculo do rádio nativo, e escondê-lo com CSS é pedir que ele reapareça no dia
 * em que o browser mude de ideias. O que interessa — que aquilo é **uma**
 * escolha entre várias, e qual está feita — diz-se pelo `role` e pelo
 * `aria-checked`, e quem lê por som ouve o mesmo.
 *
 * O que esta peça garante é a outra metade, a do teclado:
 *
 * - **as setas andam entre as opções** e escolhem a que calha, dando a volta no
 *   fim. Parar na última não diz nada a ninguém;
 * - **só a escolhida entra no Tab.** É a regra de um grupo de rádio: o Tab leva
 *   ao grupo, e lá dentro andam as setas. Sem isto, sete proporções eram sete
 *   paragens do Tab.
 */
export function useEscolhaPorSetas<T extends string>(
  valor: T,
  opcoes: { value: T; disabled?: boolean }[],
  aoEscolher: (v: T) => void,
) {
  const grupo = React.useRef<HTMLDivElement>(null);

  const aoTeclar = (e: React.KeyboardEvent) => {
    const passo = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[
      e.key
    ];
    if (passo === undefined) return;
    const vivos = opcoes.filter((o) => !o.disabled);
    if (vivos.length === 0) return;
    e.preventDefault();
    const i = vivos.findIndex((o) => o.value === valor);
    const seguinte = vivos[(i + passo + vivos.length) % vivos.length];
    aoEscolher(seguinte.value);
    grupo.current
      ?.querySelector<HTMLElement>(`[data-value="${seguinte.value}"]`)
      ?.focus();
  };

  return { grupo, aoTeclar };
}
