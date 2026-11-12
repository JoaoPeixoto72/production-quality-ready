import * as React from 'react';

export interface FieldProps {
  label?: React.ReactNode;
  /** A short sentence below, for what the label cannot hold. */
  description?: React.ReactNode;
  error?: React.ReactNode;
  /**
   * The `id` of the control this label names: a real `<label for>`. Without it
   * the label is a `<span>` naming the group by `aria-labelledby` — a `<label>`
   * names nothing around a group of `<button>`s.
   */
  htmlFor?: string;
  className?: string;
  children: React.ReactNode;
}

/** Label, note and error around something that is not a single control (a row with a button, a group of chips). */
export function Field({
  label,
  description,
  error,
  htmlFor,
  className,
  children,
}: FieldProps) {
  const id = React.useId();
  const labelId = `${id}-label`;

  const labelElement =
    label &&
    (htmlFor ? (
      <label htmlFor={htmlFor} data-ui="field-label">
        {label}
      </label>
    ) : (
      <span id={labelId} data-ui="field-label">
        {label}
      </span>
    ));

  return (
    <div
      data-ui="field"
      className={className}
      role={!htmlFor && label ? 'group' : undefined}
      aria-labelledby={!htmlFor && label ? labelId : undefined}
    >
      {labelElement}
      {children}
      {description && !error && (
        <p data-ui="field-description">{description}</p>
      )}
      {error && (
        <p data-ui="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

Field.displayName = 'Field';
