import { Progress as BaseProgress } from '@base-ui/react/progress';

export interface ProgressProps {
  value?: number;
  max?: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  isIndeterminate?: boolean;
  /** Root class: the surrounding grid and, outside `color`, the indicator's colour. */
  className?: string;
}

export function Progress({
  value = 0,
  max = 100,
  label,
  size = 'md',
  color = 'primary',
  isIndeterminate = false,
  className,
}: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <BaseProgress.Root
      value={isIndeterminate ? null : value}
      max={max}
      data-ui="progress"
      data-size={size}
      data-color={color}
      data-indeterminate={isIndeterminate ? '' : undefined}
      className={className}
    >
      {label && (
        <div data-ui="progress-header">
          <span data-ui="progress-label">{label}</span>
          {!isIndeterminate && (
            <span data-ui="progress-value">{Math.round(percentage)}%</span>
          )}
        </div>
      )}
      <BaseProgress.Track data-ui="progress-track">
        <BaseProgress.Indicator
          data-ui="progress-indicator"
          // Indeterminate gets no inline transform: core.css animates it.
          style={
            isIndeterminate
              ? undefined
              : { transform: `translateX(-${100 - percentage}%)` }
          }
        />
      </BaseProgress.Track>
    </BaseProgress.Root>
  );
}

Progress.displayName = 'Progress';
