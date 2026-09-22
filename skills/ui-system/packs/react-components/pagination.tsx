import * as React from 'react';

// O `onChange` daqui leva um número de página, e não um `ChangeEvent`: sem o
// `Omit` colide com o handler nativo que vem do `HTMLAttributes`.
export interface PaginationProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'onChange'> {
  page?: number;
  total?: number;
  onChange?: (page: number) => void;
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

export function Pagination({
  page = 1,
  total = 1,
  onChange,
  color = 'primary',
  ...props
}: PaginationProps) {
  const pages = Array.from({ length: total }, (_, i) => i + 1);

  return (
    <nav data-ui="pagination" data-color={color} aria-label="Paginação" {...props}>
      <button
        type="button"
        data-ui="pagination-item"
        data-action="prev"
        disabled={page <= 1}
        onClick={() => onChange?.(page - 1)}
        aria-label="Página anterior"
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
        aria-label="Página seguinte"
      >
        ›
      </button>
    </nav>
  );
}

Pagination.displayName = 'Pagination';
