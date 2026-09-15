import * as React from 'react';
import { Switch as BaseSwitch } from '@base-ui/react/switch';

export interface SwitchProps extends React.ComponentPropsWithoutRef<typeof BaseSwitch.Root> {
  label?: string;
}

export const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ label, id, ...props }, ref) => {
    return (
      <label data-ui="switch-label">
        <BaseSwitch.Root ref={ref} data-ui="switch" id={id} {...props}>
          <BaseSwitch.Thumb data-ui="switch-thumb" />
        </BaseSwitch.Root>
        {label && <span data-ui="switch-text">{label}</span>}
      </label>
    );
  }
);

Switch.displayName = 'Switch';
