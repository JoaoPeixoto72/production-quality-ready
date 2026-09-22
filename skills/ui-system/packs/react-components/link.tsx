import * as React from 'react';

export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  underline?: 'none' | 'hover' | 'always';
  isExternal?: boolean;
}

export const Link = React.forwardRef<HTMLAnchorElement, LinkProps>(
  ({ color = 'primary', underline = 'hover', isExternal = false, href, children, ...props }, ref) => {
    return (
      <a
        ref={ref}
        href={href}
        data-ui="link"
        data-color={color}
        data-underline={underline}
        target={isExternal ? '_blank' : undefined}
        rel={isExternal ? 'noopener noreferrer' : undefined}
        {...props}
      >
        {children}
        {isExternal && (
          <span data-ui="link-external-icon" aria-hidden="true">
            ↗
          </span>
        )}
      </a>
    );
  }
);

Link.displayName = 'Link';
