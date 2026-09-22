import * as React from 'react';
import { Tooltip as BaseTooltip } from '@base-ui/react/tooltip';

/**
 * A seta, quando ela é pedida. **Um `<div>` vazio não tem forma nenhuma** — o
 * `Tooltip.Arrow` do Base UI rende um `<div>`, e a regra do `core.css` só lhe
 * dava uma `color`. Um desenho com `currentColor` é o que faz essa `color`
 * querer dizer alguma coisa, e é por isso que ele está aqui e não no CSS.
 */
function Seta() {
  return (
    <svg width="10" height="5" viewBox="0 0 10 5" aria-hidden="true">
      <path d="M0 5 L5 0 L10 5 Z" fill="currentColor" />
    </svg>
  );
}

export interface TooltipProps {
  /** O que a dica diz. */
  content: React.ReactNode;
  /**
   * **Um elemento só, e a dica cola-se por dentro dele** (o `render` do Base
   * UI): os gestos do rato e do teclado vão para o próprio filho, e não sobra
   * elemento nenhum a mais no DOM.
   *
   * O `Tooltip.Trigger` rende um `<button>` por omissão, e embrulhar o filho
   * nele punha um botão dentro de outro em metade dos sítios — HTML inválido,
   * que o browser desfaz sozinho e deixa o gatilho partido em dois.
   *
   * **Um filho desligado não recebe o rato.** O browser não entrega eventos de
   * rato a um controlo com `disabled`, e por isso a dica nunca abre. Quem a
   * quer aí tem de pôr por fora um invólucro com caixa própria e dá-lo como
   * filho — um `display: contents` não serve, porque sem caixa não há
   * rectângulo contra o qual posicionar a dica.
   */
  children: React.ReactElement;
  /** De que lado do gatilho ela aparece. Vira-se sozinha se não couber. */
  placement?: 'top' | 'bottom' | 'left' | 'right';
  /** Como se alinha contra o gatilho, nesse lado. */
  align?: 'start' | 'center' | 'end';
  /**
   * A distância ao gatilho. Com seta é maior, porque a seta ocupa a folga —
   * os mesmos dois valores do HeroUI.
   */
  offset?: number;
  /** @default false */
  showArrow?: boolean;
  /** Quanto tempo o rato tem de lá ficar antes de ela abrir, em ms. */
  delay?: number;
  /** Quanto tempo ela fica depois de o rato sair, em ms. */
  closeDelay?: number;
  /** Desligada, não abre de maneira nenhuma — nem por rato nem por foco. */
  isDisabled?: boolean;
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** Classe da caixa da dica, para quem precise de a alargar ou apertar. */
  className?: string;
}

/**
 * A frase que aparece ao parar o rato — ou o foco do teclado — sobre uma coisa.
 *
 * **É o substituto do `title` do browser**, que não tem formatação nenhuma e
 * não aparece a quem anda pelo teclado. Aqui é um `role="tooltip"` com a
 * superfície do tema, ligado ao gatilho por `aria-describedby`: uma *descrição*
 * e não um nome, e por isso um botão só com um ícone continua a precisar do seu
 * `aria-label`.
 */
export function Tooltip({
  content,
  children,
  placement = 'top',
  align = 'center',
  offset,
  showArrow = false,
  delay = 700,
  closeDelay = 0,
  isDisabled = false,
  open,
  defaultOpen,
  onOpenChange,
  className,
}: TooltipProps) {
  return (
    <BaseTooltip.Root
      open={open}
      defaultOpen={defaultOpen}
      onOpenChange={onOpenChange}
      disabled={isDisabled}
    >
      {/* Sem `data-ui` nenhum, e de propósito: com o `render`, o gatilho **é**
          o filho, e um elemento só pode ter um slot. Pôr-lhe
          `tooltip-trigger` apagava o `button` (ou o `chip`, ou o `input`) que
          ele já era, e com ele o desenho todo. */}
      <BaseTooltip.Trigger
        delay={delay}
        closeDelay={closeDelay}
        render={children}
      />
      <BaseTooltip.Portal>
        <BaseTooltip.Positioner
          side={placement}
          align={align}
          sideOffset={offset ?? (showArrow ? 7 : 3)}
          data-ui="tooltip-positioner"
        >
          <BaseTooltip.Popup data-ui="tooltip-popup" className={className}>
            {showArrow && (
              <BaseTooltip.Arrow data-ui="tooltip-arrow">
                <Seta />
              </BaseTooltip.Arrow>
            )}
            {content}
          </BaseTooltip.Popup>
        </BaseTooltip.Positioner>
      </BaseTooltip.Portal>
    </BaseTooltip.Root>
  );
}
