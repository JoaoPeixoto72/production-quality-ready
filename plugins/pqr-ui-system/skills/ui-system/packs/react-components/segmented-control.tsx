import * as React from 'react';
import { useArrowChoice } from './arrow-choice';
import { Tooltip } from './tooltip';

export interface SegmentedOption<T extends string> {
  value: T;
  label: React.ReactNode;
  /** Hover text via this catalog's `Tooltip`. Never opens on a disabled option: use `RadioCards` to explain one. */
  title?: React.ReactNode;
  disabled?: boolean;
}

export interface SegmentedControlProps<T extends string> {
  value: T;
  onValueChange: (value: T) => void;
  options: SegmentedOption<T>[];
  /** The group's accessible name. No default: a system component does not know the app's language. */
  label: string;
  className?: string;
}

/**
 * One choice among few, as pills on a line, when each option explains itself by
 * its name; one that needs a sentence is `RadioCards`. Keyboard: `arrow-choice.ts`.
 */
export function SegmentedControl<T extends string>({
  value,
  onValueChange,
  options,
  label,
  className,
}: SegmentedControlProps<T>) {
  const { group, onKeyDown } = useArrowChoice(value, options, onValueChange);

  return (
    <div
      ref={group}
      data-ui="segmented"
      role="radiogroup"
      aria-label={label}
      className={className}
      onKeyDown={onKeyDown}
    >
      {options.map((o) => {
        const chosen = o.value === value;
        const pill = (
          <button
            type="button"
            role="radio"
            aria-checked={chosen}
            data-ui="segmented-item"
            data-value={o.value}
            disabled={o.disabled}
            tabIndex={chosen ? 0 : -1}
            onClick={() => onValueChange(o.value)}
          >
            {o.label}
          </button>
        );
        return o.title === undefined || o.title === '' ? (
          <React.Fragment key={o.value}>{pill}</React.Fragment>
        ) : (
          <Tooltip key={o.value} content={o.title}>
            {pill}
          </Tooltip>
        );
      })}
    </div>
  );
}

SegmentedControl.displayName = 'SegmentedControl';
