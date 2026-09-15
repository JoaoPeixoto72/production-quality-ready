import * as React from 'react';
import { Popover as BasePopover } from '@base-ui/react/popover';

type PositionerProps = React.ComponentPropsWithoutRef<typeof BasePopover.Positioner>;

export interface PopoverProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

export function Popover({ open, onOpenChange, children }: PopoverProps) {
  return (
    <BasePopover.Root open={open} onOpenChange={onOpenChange}>
      {children}
    </BasePopover.Root>
  );
}

export const PopoverTrigger = BasePopover.Trigger;

export function PopoverContent({
  children,
  side,
  align,
  sideOffset = 8,
  alignOffset,
  ...props
}: {
  children: React.ReactNode;
  /**
   * De que lado do gatilho o painel abre, e como se alinha com ele.
   *
   * **Vão ao positioner e não ao popup**, como o `z-index` — e pela mesma
   * razão: quem está posicionado é ele. Um painel que escolhia o lado por
   * `position: absolute` no CSS da app ficava preso a essa escolha; aqui o
   * Base UI vira-o sozinho quando não cabe do lado pedido, que é o que uma
   * regra de CSS não tem como saber.
   */
  side?: PositionerProps['side'];
  align?: PositionerProps['align'];
  sideOffset?: number;
  alignOffset?: PositionerProps['alignOffset'];
} & React.ComponentPropsWithoutRef<typeof BasePopover.Popup>) {
  return (
    <BasePopover.Portal>
      <BasePopover.Positioner
        side={side}
        align={align}
        sideOffset={sideOffset}
        alignOffset={alignOffset}
        data-ui="popover-positioner"
      >
        <BasePopover.Popup data-ui="popover-popup" {...props}>
          {children}
        </BasePopover.Popup>
      </BasePopover.Positioner>
    </BasePopover.Portal>
  );
}
