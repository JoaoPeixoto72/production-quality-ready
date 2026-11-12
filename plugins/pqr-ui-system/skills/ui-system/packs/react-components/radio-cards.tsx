import * as React from 'react';
import { useArrowChoice } from './arrow-choice';
import { Tooltip } from './tooltip';

export interface RadioCardOption<T extends string> {
  value: T;
  title: React.ReactNode;
  /** The sentence under the name — the reason for a card instead of a pill. */
  description?: React.ReactNode;
  /** Something to look at above the name (a filter sample, a subtitle style). */
  media?: React.ReactNode;
  disabled?: boolean;
  /** Hover text via `Tooltip`. Never opens on a disabled card: say why in `description`. */
  hint?: React.ReactNode;
}

export interface RadioCardsProps<T extends string> {
  value: T;
  onValueChange: (value: T) => void;
  options: RadioCardOption<T>[];
  /** The group's accessible name; no default, as in `SegmentedControl`. */
  label: string;
  /** Wrapper class — it decides the grid. */
  className?: string;
}

/** One choice among few, as cards: when there is something to read or look at. Keyboard: `arrow-choice.ts`. */
export function RadioCards<T extends string>({
  value,
  onValueChange,
  options,
  label,
  className,
}: RadioCardsProps<T>) {
  const { group, onKeyDown } = useArrowChoice(value, options, onValueChange);

  return (
    <div
      ref={group}
      data-ui="radio-cards"
      role="radiogroup"
      aria-label={label}
      className={className}
      onKeyDown={onKeyDown}
    >
      {options.map((o) => {
        const chosen = o.value === value;
        const card = (
          <button
            type="button"
            role="radio"
            aria-checked={chosen}
            data-ui="radio-card"
            data-value={o.value}
            disabled={o.disabled}
            tabIndex={chosen ? 0 : -1}
            onClick={() => onValueChange(o.value)}
          >
            {o.media && <span data-ui="radio-card-media">{o.media}</span>}
            <span data-ui="radio-card-title">{o.title}</span>
            {o.description && (
              <span data-ui="radio-card-description">{o.description}</span>
            )}
          </button>
        );
        return o.hint === undefined || o.hint === '' ? (
          <React.Fragment key={o.value}>{card}</React.Fragment>
        ) : (
          <Tooltip key={o.value} content={o.hint}>
            {card}
          </Tooltip>
        );
      })}
    </div>
  );
}

RadioCards.displayName = 'RadioCards';
