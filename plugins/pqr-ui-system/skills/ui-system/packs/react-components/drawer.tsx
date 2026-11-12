import * as React from 'react';
import { Dialog as BaseDialog } from '@base-ui/react/dialog';

export interface DrawerProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

export function Drawer({ open, onOpenChange, children }: DrawerProps) {
  return (
    <BaseDialog.Root open={open} onOpenChange={onOpenChange}>
      {children}
    </BaseDialog.Root>
  );
}

export const DrawerTrigger = BaseDialog.Trigger;
export const DrawerClose = BaseDialog.Close;

export interface DrawerContentProps {
  title?: string;
  description?: string;
  placement?: 'left' | 'right' | 'bottom';
  children: React.ReactNode;
}

export function DrawerContent({
  title,
  description,
  placement = 'right',
  children,
}: DrawerContentProps) {
  return (
    <BaseDialog.Portal>
      <BaseDialog.Backdrop data-ui="dialog-backdrop" />
      <BaseDialog.Popup data-ui="drawer-popup" data-placement={placement}>
        {title && (
          <header data-ui="drawer-header">
            <BaseDialog.Title data-ui="drawer-title">{title}</BaseDialog.Title>
            {description && (
              <BaseDialog.Description data-ui="drawer-description">
                {description}
              </BaseDialog.Description>
            )}
          </header>
        )}
        <div data-ui="drawer-body">{children}</div>
      </BaseDialog.Popup>
    </BaseDialog.Portal>
  );
}

Drawer.displayName = 'Drawer';
