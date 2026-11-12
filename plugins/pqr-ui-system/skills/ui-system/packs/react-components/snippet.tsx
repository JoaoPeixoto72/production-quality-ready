import * as React from 'react';

export interface SnippetProps extends React.HTMLAttributes<HTMLDivElement> {
  text?: string;
  variant?: 'solid' | 'flat' | 'bordered';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  /** The copy button's accessible names, before and after copying. No defaults (the app's language). */
  copyLabel?: string;
  copiedLabel?: string;
}

export const Snippet = React.forwardRef<HTMLDivElement, SnippetProps>(
  ({ text, variant = 'flat', color = 'default', copyLabel, copiedLabel, children, ...props }, ref) => {
    const [copied, setCopied] = React.useState(false);
    const contentToCopy = text || (typeof children === 'string' ? children : '');

    const handleCopy = async () => {
      if (!contentToCopy) return;
      try {
        await navigator.clipboard.writeText(contentToCopy);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('copy failed:', err);
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
          aria-label={copied ? copiedLabel : copyLabel}
        >
          {copied ? '✓' : '📋'}
        </button>
      </div>
    );
  }
);

Snippet.displayName = 'Snippet';
