import * as React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  surface?: 'content1' | 'content2';
  isPressable?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ surface = 'content1', isPressable = false, ...props }, ref) => {
    return (
      <div
        ref={ref}
        data-ui="card"
        data-surface={surface}
        data-pressable={isPressable ? 'true' : undefined}
        {...props}
      />
    );
  }
);
Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => <header ref={ref} data-ui="card-header" {...props} />
);
CardHeader.displayName = 'CardHeader';

export const CardBody = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => <div ref={ref} data-ui="card-body" {...props} />
);
CardBody.displayName = 'CardBody';

export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => <footer ref={ref} data-ui="card-footer" {...props} />
);
CardFooter.displayName = 'CardFooter';
