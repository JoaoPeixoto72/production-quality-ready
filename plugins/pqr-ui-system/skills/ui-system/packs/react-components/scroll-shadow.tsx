import * as React from 'react';

export interface ScrollShadowProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'vertical' | 'horizontal';
  hideScrollBar?: boolean;
}

export const ScrollShadow = React.forwardRef<HTMLDivElement, ScrollShadowProps>(
  ({ orientation = 'vertical', hideScrollBar = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        data-ui="scroll-shadow"
        data-orientation={orientation}
        data-hide-scrollbar={hideScrollBar ? '' : undefined}
        {...props}
      >
        {children}
      </div>
    );
  }
);

ScrollShadow.displayName = 'ScrollShadow';
