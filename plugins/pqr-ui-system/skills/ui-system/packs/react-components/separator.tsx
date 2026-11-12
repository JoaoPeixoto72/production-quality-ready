import * as React from 'react';
import { Separator as BaseSeparator } from '@base-ui/react/separator';

export interface SeparatorProps extends React.ComponentPropsWithoutRef<typeof BaseSeparator> {
  orientation?: 'horizontal' | 'vertical';
}

export const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  ({ orientation = 'horizontal', ...props }, ref) => {
    return (
      <BaseSeparator
        ref={ref}
        data-ui="separator"
        orientation={orientation}
        {...props}
      />
    );
  }
);

Separator.displayName = 'Separator';

/** HeroUI alias. */
export const Divider = Separator;
