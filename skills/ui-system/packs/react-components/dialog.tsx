import * as React from 'react';
import { Dialog as BaseDialog } from '@base-ui/react/dialog';

export interface DialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  return (
    <BaseDialog.Root open={open} onOpenChange={onOpenChange}>
      {children}
    </BaseDialog.Root>
  );
}

export const DialogTrigger = BaseDialog.Trigger;
export const DialogClose = BaseDialog.Close;

export function DialogContent({
  title,
  description,
  icon,
  footer,
  closeLabel,
  closeIcon,
  children,
  size = 'md',
  className,
}: {
  /** A node: some titles carry a value. */
  title?: React.ReactNode;
  description?: React.ReactNode;
  /** A mark left of the title, outside `Title` so a screen reader does not read it twice. */
  icon?: React.ReactNode;
  /** The bottom row for action buttons; without it the dialog is read-only. */
  footer?: React.ReactNode;
  /** The close button's accessible name. No default (the component does not know the app's language); without it there is no button — Escape, outside click and the footer close. */
  closeLabel?: string;
  /** Drawn inside the close button. Default `×`. */
  closeIcon?: React.ReactNode;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  return (
    <BaseDialog.Portal>
      {/* Backdrop as a direct child of Portal, for iOS Safari. */}
      <BaseDialog.Backdrop data-ui="dialog-backdrop" />
      <div data-ui="dialog-viewport">
        <BaseDialog.Popup
          data-ui="dialog-popup"
          data-size={size}
          className={className}
        >
          {(title || icon) && (
            <header data-ui="dialog-header">
              {icon && (
                <span data-ui="dialog-icon" aria-hidden="true">
                  {icon}
                </span>
              )}
              <BaseDialog.Title data-ui="dialog-title">{title}</BaseDialog.Title>
              {description && (
                <BaseDialog.Description data-ui="dialog-description">
                  {description}
                </BaseDialog.Description>
              )}
              {closeLabel && (
                <BaseDialog.Close data-ui="dialog-close" aria-label={closeLabel}>
                  {closeIcon ?? '×'}
                </BaseDialog.Close>
              )}
            </header>
          )}
          <div data-ui="dialog-body">{children}</div>
          {footer && <footer data-ui="dialog-footer">{footer}</footer>}
        </BaseDialog.Popup>
      </div>
    </BaseDialog.Portal>
  );
}
