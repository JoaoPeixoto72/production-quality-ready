import * as React from 'react';

export interface SpacerProps extends React.HTMLAttributes<HTMLSpanElement> {
  x?: number | string;
  y?: number | string;
}

export const Spacer = React.forwardRef<HTMLSpanElement, SpacerProps>(
  ({ x, y, className, ...props }, ref) => {
    return (
      <span
        ref={ref}
        data-ui="spacer"
        data-orientation={x ? 'horizontal' : 'vertical'}
        aria-hidden="true"
        {...props}
      />
    );
  }
);

Spacer.displayName = 'Spacer';
