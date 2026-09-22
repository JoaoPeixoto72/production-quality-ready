import { Progress as BaseProgress } from '@base-ui/react/progress';

export interface ProgressProps {
  value?: number;
  max?: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  isIndeterminate?: boolean;
  /**
   * Classe da raiz, como no resto do catálogo. É por ela que quem usa decide a
   * grelha à volta — e, num estado que o `color` não cubra, a cor do indicador.
   */
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
          /**
           * **Indeterminado não leva `transform` nenhum daqui**: quem o move é a
           * animação do `core.css`, e um valor escrito em linha sobrevivia a uma
           * barra que passasse de determinada a indeterminada.
           *
           * Isto era um `useEffect` a escrever `style.transform` num `ref`. Um
           * efeito para pôr um valor que se sabe no render é uma volta a mais —
           * e era ele que deixava o valor velho para trás, porque só escrevia no
           * ramo determinado e nunca limpava o outro.
           */
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
