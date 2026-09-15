import * as React from 'react';

export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  density?: 'compact' | 'normal' | 'spacious';
}

export const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ density = 'normal', className, ...props }, ref) => (
    <div data-ui="table-container">
      <table ref={ref} data-ui="table" data-density={density} {...props} />
    </div>
  )
);
Table.displayName = 'Table';

export const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>((props, ref) => <thead ref={ref} data-ui="table-header" {...props} />);
TableHeader.displayName = 'TableHeader';

export const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>((props, ref) => <tbody ref={ref} data-ui="table-body" {...props} />);
TableBody.displayName = 'TableBody';

export const TableRow = React.forwardRef<
  HTMLTableRowElement,
  React.HTMLAttributes<HTMLTableRowElement>
>((props, ref) => <tr ref={ref} data-ui="table-row" {...props} />);
TableRow.displayName = 'TableRow';

export const TableHead = React.forwardRef<
  HTMLTableCellElement,
  React.ThHTMLAttributes<HTMLTableCellElement>
>((props, ref) => <th ref={ref} data-ui="table-head" {...props} />);
TableHead.displayName = 'TableHead';

export const TableCell = React.forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>((props, ref) => <td ref={ref} data-ui="table-cell" {...props} />);
TableCell.displayName = 'TableCell';
