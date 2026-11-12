import * as React from 'react';

// `onChange` takes a page number, not a `ChangeEvent`: `Omit` avoids the native handler clash.
export interface PaginationProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'onChange'> {
  page?: number;
  total?: number;
  onChange?: (page: number) => void;
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  /** Accessible names. No defaults: a system component does not know the app's language. */
  label?: string;
  previousLabel?: string;
  nextLabel?: string;
}

export function Pagination({
  page = 1,
  total = 1,
  onChange,
  color = 'primary',
  label,
  previousLabel,
  nextLabel,
  ...props
}: PaginationProps) {
  const pages = Array.from({ length: total }, (_, i) => i + 1);

  return (
    <nav data-ui="pagination" data-color={color} aria-label={label} {...props}>
      <button
        type="button"
        data-ui="pagination-item"
        data-action="prev"
        disabled={page <= 1}
        onClick={() => onChange?.(page - 1)}
        aria-label={previousLabel}
      >
        ‹
      </button>

      {pages.map((p) => (
        <button
          key={p}
          type="button"
          data-ui="pagination-item"
          aria-current={p === page ? 'page' : undefined}
          onClick={() => onChange?.(p)}
        >
          {p}
        </button>
      ))}

      <button
        type="button"
        data-ui="pagination-item"
        data-action="next"
        disabled={page >= total}
        onClick={() => onChange?.(page + 1)}
        aria-label={nextLabel}
      >
        ›
      </button>
    </nav>
  );
}

Pagination.displayName = 'Pagination';
