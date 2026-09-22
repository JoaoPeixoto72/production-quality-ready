import * as React from 'react';

export interface SnippetProps extends React.HTMLAttributes<HTMLDivElement> {
  text?: string;
  variant?: 'solid' | 'flat' | 'bordered';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

export const Snippet = React.forwardRef<HTMLDivElement, SnippetProps>(
  ({ text, variant = 'flat', color = 'default', children, ...props }, ref) => {
    const [copied, setCopied] = React.useState(false);
    const contentToCopy = text || (typeof children === 'string' ? children : '');

    const handleCopy = async () => {
      if (!contentToCopy) return;
      try {
        await navigator.clipboard.writeText(contentToCopy);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Falha ao copiar:', err);
      }
    };

    return (
      <div
        ref={ref}
        data-ui="snippet"
        data-variant={variant}
        data-color={color}
        {...props}
      >
        <pre data-ui="snippet-pre">
          <code>{children || text}</code>
        </pre>
        <button
          type="button"
          data-ui="snippet-copy-btn"
          onClick={handleCopy}
          aria-label={copied ? 'Copiado!' : 'Copiar código'}
        >
          {copied ? '✓' : '📋'}
        </button>
      </div>
    );
  }
);

Snippet.displayName = 'Snippet';
