import * as React from 'react';
import { Slider as BaseSlider } from '@base-ui/react/slider';

export interface SliderProps {
  value?: number | number[];
  defaultValue?: number | number[];
  onValueChange?: (value: number | number[]) => void;
  min?: number;
  max?: number;
  step?: number;
  /** A etiqueta do cabeçalho. Um nó, como no `Input` e no `Select`. */
  label?: React.ReactNode;
  /**
   * Escrever o valor cru no canto do cabeçalho. **Desliga-se quando quem chama
   * já o escreve dentro da própria etiqueta** — há valores que não se leem em
   * número solto: um `-30` que é `-30 dB` e um `55` que é `5,5 %` só ganham
   * sentido com a unidade, e quem a sabe é quem chama.
   */
  showValue?: boolean;
  disabled?: boolean;
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  /** Classe do **invólucro**, como no `Input` e no `Select`. */
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
      {/* A pista pinta-se sozinha até ao polegar: o indicador é um elemento a
          sério. Um `<input type="range"` nativo não tem nada disto — a única
          forma de a pista saber o valor era uma custom property calculada por
          fora, e era o que esta app fazia. */}
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
