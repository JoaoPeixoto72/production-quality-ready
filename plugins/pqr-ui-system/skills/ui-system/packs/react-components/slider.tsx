import * as React from 'react';
import { Slider as BaseSlider } from '@base-ui/react/slider';

export interface SliderProps {
  value?: number | number[];
  defaultValue?: number | number[];
  onValueChange?: (value: number | number[]) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: React.ReactNode;
  /** Print the raw value in the header. Off when the caller writes it with its unit inside the label. */
  showValue?: boolean;
  disabled?: boolean;
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  /** Wrapper class, as in `Input` and `Select`. */
  className?: string;
}

export function Slider({
  value,
  defaultValue = 0,
  onValueChange,
  min = 0,
  max = 100,
  step = 1,
  label,
  showValue = true,
  disabled = false,
  color = 'primary',
  className,
}: SliderProps) {
  const id = React.useId();
  const labelId = `${id}-label`;

  return (
    <BaseSlider.Root
      value={value}
      defaultValue={defaultValue}
      onValueChange={onValueChange}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      data-ui="slider"
      data-color={color}
      className={className}
    >
      {label && (
        <div data-ui="slider-header">
          <span data-ui="slider-label" id={labelId}>
            {label}
          </span>
          {showValue && <BaseSlider.Value data-ui="slider-value" />}
        </div>
      )}
      {/* The track fills up to the thumb by itself: the indicator is a real element. */}
      <BaseSlider.Control data-ui="slider-control">
        <BaseSlider.Track data-ui="slider-track">
          <BaseSlider.Indicator data-ui="slider-indicator" />
          <BaseSlider.Thumb
            data-ui="slider-thumb"
            aria-labelledby={label ? labelId : undefined}
          />
        </BaseSlider.Track>
      </BaseSlider.Control>
    </BaseSlider.Root>
  );
}

Slider.displayName = 'Slider';
