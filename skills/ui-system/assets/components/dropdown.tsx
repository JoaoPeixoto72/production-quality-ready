import * as React from 'react';
import { Menu as BaseMenu } from '@base-ui/react/menu';

export const Dropdown = BaseMenu.Root;
export const DropdownTrigger = BaseMenu.Trigger;

export interface DropdownMenuProps {
  children: React.ReactNode;
  sideOffset?: number;
  /** How the menu lines up with its trigger. A small trigger near a window edge
   *  needs `"start"`: centred, a wide menu opened by a 26px button in the left
   *  corner is born half outside the window. */
  align?: 'start' | 'center' | 'end';
}

export function DropdownMenu({ children, sideOffset = 6, align }: DropdownMenuProps) {
  return (
    <BaseMenu.Portal>
      <BaseMenu.Positioner
        sideOffset={sideOffset}
        align={align}
        data-ui="dropdown-positioner"
      >
        <BaseMenu.Popup data-ui="dropdown-menu">
          {children}
        </BaseMenu.Popup>
      </BaseMenu.Positioner>
    </BaseMenu.Portal>
  );
}

export const DropdownItem = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof BaseMenu.Item>
>((props, ref) => <BaseMenu.Item ref={ref} data-ui="dropdown-item" {...props} />);
DropdownItem.displayName = 'DropdownItem';

export const DropdownSeparator = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof BaseMenu.Separator>
>((props, ref) => <BaseMenu.Separator ref={ref} data-ui="dropdown-separator" {...props} />);
DropdownSeparator.displayName = 'DropdownSeparator';
