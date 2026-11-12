import * as React from 'react';

/**
 * Keyboard for a hand-drawn radio group (pills, cards; `role` + `aria-checked`, not native radios):
 * arrows move and choose, wrapping at the ends; only the chosen option is in the Tab order.
 */
export function useArrowChoice<T extends string>(
  value: T,
  options: { value: T; disabled?: boolean }[],
  onChoose: (v: T) => void,
) {
  const group = React.useRef<HTMLDivElement>(null);

  const onKeyDown = (e: React.KeyboardEvent) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[
      e.key
    ];
    if (step === undefined) return;
    const enabled = options.filter((o) => !o.disabled);
    if (enabled.length === 0) return;
    e.preventDefault();
    const i = enabled.findIndex((o) => o.value === value);
    const next = enabled[(i + step + enabled.length) % enabled.length];
    onChoose(next.value);
    group.current
      ?.querySelector<HTMLElement>(`[data-value="${next.value}"]`)
      ?.focus();
  };

  return { group, onKeyDown };
}
