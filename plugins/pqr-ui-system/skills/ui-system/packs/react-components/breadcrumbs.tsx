import * as React from 'react';

export interface BreadcrumbItemProps extends React.HTMLAttributes<HTMLLIElement> {
  href?: string;
  isCurrent?: boolean;
}

export const BreadcrumbItem = React.forwardRef<HTMLLIElement, BreadcrumbItemProps>(
  ({ href, isCurrent = false, children, ...props }, ref) => {
    return (
      <li ref={ref} data-ui="breadcrumb-item" aria-current={isCurrent ? 'page' : undefined} {...props}>
        {href && !isCurrent ? (
          <a href={href} data-ui="breadcrumb-link">
            {children}
          </a>
        ) : (
          <span data-ui="breadcrumb-current">{children}</span>
        )}
      </li>
    );
  }
);
BreadcrumbItem.displayName = 'BreadcrumbItem';

export interface BreadcrumbsProps extends React.HTMLAttributes<HTMLElement> {
  separator?: React.ReactNode;
}

export const Breadcrumbs = React.forwardRef<HTMLElement, BreadcrumbsProps>(
  ({ separator = '/', children, ...props }, ref) => {
    const items = React.Children.toArray(children);

    return (
      <nav ref={ref} aria-label="Breadcrumb" data-ui="breadcrumbs" {...props}>
        <ol data-ui="breadcrumbs-list">
          {items.map((item, index) => (
            <React.Fragment key={index}>
              {item}
              {index < items.length - 1 && (
                <li data-ui="breadcrumb-separator" aria-hidden="true">
                  {separator}
                </li>
              )}
            </React.Fragment>
          ))}
        </ol>
      </nav>
    );
  }
);
Breadcrumbs.displayName = 'Breadcrumbs';
