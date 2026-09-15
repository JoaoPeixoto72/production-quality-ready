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
  /** Um nó, e não só uma string: há títulos que levam um valor por dentro. */
  title?: React.ReactNode;
  description?: React.ReactNode;
  /**
   * Uma marca à esquerda do título — o ícone da coisa que o diálogo abriu.
   * Fica fora do `Title` de propósito: quem lê por som já ouve o título, e um
   * ícone lido a seguir é ruído.
   */
  icon?: React.ReactNode;
  /**
   * A linha de baixo, onde vivem os botões de acção. Sem ela o diálogo é só de
   * leitura, e não há nada a fechar a caixa por baixo do corpo.
   */
  footer?: React.ReactNode;
  /**
   * O nome do botão de fechar, no canto do cabeçalho. **Não tem texto por
   * omissão**, pela mesma razão do `placeholder` do `Select`: um componente de
   * sistema não sabe em que língua a app está, e um `aria-label` embutido saía
   * em inglês sem nada a avisar. Sem ele não há botão — e quem fecha é o
   * Escape, o clique fora, e o que estiver no rodapé.
   */
  closeLabel?: string;
  /** O que se desenha dentro desse botão. Por omissão, um `×`. */
  closeIcon?: React.ReactNode;
  children: React.ReactNode;
  /** `sm | md | lg`, como no resto do catálogo e como no HeroUI. */
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  return (
    <BaseDialog.Portal>
      {/* Backdrop é filho direto do Portal para garantir suporte a iOS Safari */}
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
