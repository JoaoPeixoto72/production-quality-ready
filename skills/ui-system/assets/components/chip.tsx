import * as React from 'react';

export interface ChipProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'onClick'> {
  variant?: 'solid' | 'flat' | 'bordered' | 'dot';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  /**
   * **Ligado, desligado, ou nem uma coisa nem outra.**
   *
   * Com um booleano, o chip deixa de ser uma etiqueta e passa a ser um
   * interruptor: rende um `<button>` com `aria-pressed`, e é isso que diz a
   * quem lê por som que aquilo se carrega e tem dois estados. Sem ele, é uma
   * etiqueta — um `<span>`, que não se carrega e não entra no Tab.
   *
   * É a diferença entre «este ficheiro está escolhido» e «este ficheiro está
   * aqui», e não se adivinha do aspecto: os dois são a mesma pílula.
   */
  pressed?: boolean;
  onClick?: React.MouseEventHandler<HTMLElement>;
  /**
   * O que fazer no `×` do canto. Sem isto não há `×` nenhum.
   *
   * **Não coexiste com o `pressed`**, e não é uma limitação arbitrária: um
   * interruptor já é um `<button>`, e um `<button>` dentro de outro é HTML
   * inválido — o browser desfaz o aninhamento sozinho e o resultado é um chip
   * partido em dois. Com os dois postos, o `×` não aparece.
   */
  onClose?: () => void;
  /**
   * O nome desse `×`, para quem lê por som. **Não tem texto por omissão**, pela
   * mesma razão do `placeholder` do `Select`: um componente de sistema não sabe
   * em que língua a app está, e um `aria-label` embutido saía sempre na língua
   * errada em metade das apps sem nada a avisar.
   */
  closeLabel?: string;
  /** O que se desenha dentro do `×`. Por omissão, um `✕`. */
  closeIcon?: React.ReactNode;
  avatar?: React.ReactNode;
}

export const Chip = React.forwardRef<HTMLElement, ChipProps>(
  (
    {
      variant = 'flat',
      color = 'default',
      size = 'md',
      pressed,
      onClose,
      closeLabel,
      closeIcon,
      avatar,
      children,
      ...props
    },
    ref
  ) => {
    const interruptor = pressed !== undefined;
    const Etiqueta = (interruptor ? 'button' : 'span') as 'span';

    return (
      <Etiqueta
        ref={ref as React.Ref<HTMLSpanElement>}
        data-ui="chip"
        data-variant={variant}
        data-color={color}
        data-size={size}
        {...(interruptor
          ? { type: 'button' as const, 'aria-pressed': pressed }
          : {})}
        {...props}
      >
        {variant === 'dot' && <span data-ui="chip-dot" aria-hidden="true" />}
        {avatar && <span data-ui="chip-avatar">{avatar}</span>}
        <span data-ui="chip-content">{children}</span>
        {onClose && !interruptor && (
          <button
            type="button"
            data-ui="chip-close-btn"
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            aria-label={closeLabel}
          >
            {closeIcon ?? '✕'}
          </button>
        )}
      </Etiqueta>
    );
  }
);

Chip.displayName = 'Chip';
