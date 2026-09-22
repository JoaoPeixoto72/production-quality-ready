import * as React from 'react';

export interface KbdProps extends React.HTMLAttributes<HTMLElement> {
  keys?: Array<'command' | 'shift' | 'ctrl' | 'option' | 'alt' | 'enter' | 'delete' | 'escape'>;
}

const KEY_SYMBOLS: Record<string, string> = {
  command: '⌘',
  shift: '⇧',
  ctrl: '⌃',
  option: '⌥',
  alt: '⎇',
  enter: '↵',
  delete: '⌫',
  escape: '⎋',
};

export const Kbd = React.forwardRef<HTMLElement, KbdProps>(
  ({ keys = [], children, ...props }, ref) => {
    return (
      <kbd ref={ref} data-ui="kbd" {...props}>
        {keys.map((key) => (
          <abbr key={key} title={key} data-ui="kbd-abbr">
            {KEY_SYMBOLS[key] || key}
          </abbr>
        ))}
        {children && <span data-ui="kbd-content">{children}</span>}
      </kbd>
    );
  }
);

Kbd.displayName = 'Kbd';
