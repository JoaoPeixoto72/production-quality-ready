import * as React from 'react';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  isLoaded?: boolean;
}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ isLoaded = false, children, ...props }, ref) => {
    if (isLoaded) {
      return <>{children}</>;
    }
    return (
      <div
        ref={ref}
        data-ui="skeleton"
        aria-hidden="true"
        {...props}
      >
        <span data-ui="skeleton-content">{children}</span>
      </div>
    );
  }
);

Skeleton.displayName = 'Skeleton';
