import * as React from 'react';
import { Select as BaseSelect } from '@base-ui/react/select';

export interface SelectOption {
  value: string;
  /**
   * Um nó, e não só uma string: há listas que precisam de desenhar cada linha
   * à sua maneira — uma lista de fontes que escreve cada nome na própria
   * fonte, por exemplo. Num `<select>` nativo isso não era de confiança (o
   * Chromium ignora quase tudo o que se põe num `<option>`); aqui cada item é
   * um elemento normal.
   */
  label: React.ReactNode;
  disabled?: boolean;
}

export interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  options: SelectOption[];
  /**
   * O que se lê quando não há escolha nenhuma. **Não tem texto por omissão de
   * propósito**: um componente de sistema não sabe em que língua a app está, e
   * uma frase embutida aqui saía em português numa interface inglesa sem nada
   * a avisar — nem o `tsc` nem o auditor apanham isso. Sem valor, não se lê
   * nada, que é errado de forma visível em vez de errado em silêncio.
   */
  placeholder?: React.ReactNode;
  disabled?: boolean;
  /**
   * A etiqueta por cima do controlo. Rende um `field-label` e liga-o ao
   * gatilho por `aria-labelledby` — o gatilho é um `<button>`, e um
   * `<label htmlFor>` não lhe dá nome nenhum.
   */
  label?: React.ReactNode;
  /** Uma frase curta por baixo, para o que não cabe na etiqueta. */
  description?: React.ReactNode;
  /** Classe do invólucro, para quem já tem uma grelha própria. */
  className?: string;
  /**
   * Estilo do gatilho, para o caso em que o próprio valor escolhido tem de se
   * desenhar de outra maneira — outra vez, a lista das fontes.
   */
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
      // O Base UI entrega `string | null` (o `null` é a limpeza da escolha) e
      // um segundo argumento com o evento. Cá fora a API fica com a assinatura
      // simples: quem usa um `Select` de opções fixas nunca quer tratar o
      // `null` — e sem esta ponte o valor limpo chegava como `null` a quem
      // espera uma `string`.
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
        {/* Sem esta função, o `Select.Value` escreve o **valor** e não a
            etiqueta: uma opção `{ value: 'best', label: 'Melhor' }` aparecia
            como `best`. O `placeholder` sozinho não chega — só cobre o caso de
            não haver escolha nenhuma. */}
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
