import * as React from 'react';

export interface CircularProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  showValueLabel?: boolean;
}

export function CircularProgress({
  value = 0,
  max = 100,
  size = 'md',
  color = 'primary',
  showValueLabel = false,
  ...props
}: CircularProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const strokeWidth = size === 'sm' ? 3 : size === 'lg' ? 5 : 4;
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div
      data-ui="circular-progress"
      data-size={size}
      data-color={color}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      {...props}
    >
      <svg data-ui="circular-progress-svg" viewBox="0 0 44 44" aria-hidden="true">
        <circle
          data-ui="circular-progress-track"
          cx="22"
          cy="22"
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          data-ui="circular-progress-indicator"
          cx="22"
          cy="22"
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      {showValueLabel && (
        <span data-ui="circular-progress-label">
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  );
}

CircularProgress.displayName = 'CircularProgress';
