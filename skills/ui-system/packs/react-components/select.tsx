import * as React from 'react';
import { Select as BaseSelect } from '@base-ui/react/select';

export interface SelectOption {
  value: string;
  /** A node, so a row can draw itself (a font list in its own font) — what a native `<option>` cannot. */
  label: React.ReactNode;
  disabled?: boolean;
}

export interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  options: SelectOption[];
  /** Shown with no choice. No default text: a system component does not know the app's language. */
  placeholder?: React.ReactNode;
  disabled?: boolean;
  /** Rendered as `field-label`, tied to the trigger by `aria-labelledby` (a `<label for>` cannot name a `<button>`). */
  label?: React.ReactNode;
  /** A short sentence below, for what the label cannot hold. */
  description?: React.ReactNode;
  /** Wrapper class. */
  className?: string;
  /** Trigger style, for a chosen value that draws itself differently (the font list again). */
  triggerStyle?: React.CSSProperties;
}

export function Select({
  value,
  defaultValue,
  onValueChange,
  options,
  placeholder,
  disabled,
  label,
  description,
  className,
  triggerStyle,
}: SelectProps) {
  const id = React.useId();
  const labelId = `${id}-label`;
  const descId = `${id}-desc`;

  const control = (
    <BaseSelect.Root
      value={value}
      defaultValue={defaultValue}
      // Base UI sends `string | null` (null = cleared); fixed-option callers only want strings.
      onValueChange={(v) => {
        if (v !== null) onValueChange?.(v);
      }}
      disabled={disabled}
    >
      <BaseSelect.Trigger
        data-ui="select-trigger"
        style={triggerStyle}
        aria-labelledby={label ? labelId : undefined}
        aria-describedby={description ? descId : undefined}
      >
        {/* Without this function `Select.Value` prints the value, not the label. */}
        <BaseSelect.Value data-ui="select-value" placeholder={placeholder}>
          {(v: string | null) => {
            if (v === null || v === undefined || v === '') return placeholder;
            return options.find((o) => o.value === v)?.label ?? v;
          }}
        </BaseSelect.Value>
        <span data-ui="select-icon" aria-hidden="true">
          ▾
        </span>
      </BaseSelect.Trigger>
      <BaseSelect.Portal>
        <BaseSelect.Positioner sideOffset={6} data-ui="select-positioner">
          <BaseSelect.Popup data-ui="select-popup">
            <BaseSelect.List data-ui="select-list">
              {options.map((option) => (
                <BaseSelect.Item
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                  data-ui="select-item"
                >
                  <BaseSelect.ItemText>{option.label}</BaseSelect.ItemText>
                  <BaseSelect.ItemIndicator data-ui="select-indicator">
                    ✓
                  </BaseSelect.ItemIndicator>
                </BaseSelect.Item>
              ))}
            </BaseSelect.List>
          </BaseSelect.Popup>
        </BaseSelect.Positioner>
      </BaseSelect.Portal>
    </BaseSelect.Root>
  );

  if (!label && !description) {
    return className ? (
      <div data-ui="field" className={className}>
        {control}
      </div>
    ) : (
      control
    );
  }

  return (
    <div data-ui="field" className={className}>
      {label && (
        <span data-ui="field-label" id={labelId}>
          {label}
        </span>
      )}
      {control}
      {description && (
        <span data-ui="field-description" id={descId}>
          {description}
        </span>
      )}
    </div>
  );
}
