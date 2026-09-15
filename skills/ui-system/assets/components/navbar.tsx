import * as React from 'react';

export interface NavbarProps extends React.HTMLAttributes<HTMLElement> {
  isBordered?: boolean;
}

export const Navbar = React.forwardRef<HTMLElement, NavbarProps>(
  ({ isBordered = false, children, ...props }, ref) => {
    return (
      <header
        ref={ref}
        data-ui="navbar"
        data-bordered={isBordered ? '' : undefined}
        {...props}
      >
        <div data-ui="navbar-container">{children}</div>
      </header>
    );
  }
);
Navbar.displayName = 'Navbar';

export const NavbarBrand = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => <div ref={ref} data-ui="navbar-brand" {...props} />
);
NavbarBrand.displayName = 'NavbarBrand';

export const NavbarContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => <div ref={ref} data-ui="navbar-content" {...props} />
);
NavbarContent.displayName = 'NavbarContent';

export const NavbarItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => <div ref={ref} data-ui="navbar-item" {...props} />
);
NavbarItem.displayName = 'NavbarItem';
