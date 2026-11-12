import * as React from 'react';
import { Accordion as BaseAccordion } from '@base-ui/react/accordion';

export const Accordion = BaseAccordion.Root;

export interface AccordionItemProps {
  value: string;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  disabled?: boolean;
}

export function AccordionItem({
  value,
  title,
  subtitle,
  children,
  disabled,
}: AccordionItemProps) {
  return (
    <BaseAccordion.Item value={value} disabled={disabled} data-ui="accordion-item">
      <BaseAccordion.Header data-ui="accordion-header">
        <BaseAccordion.Trigger data-ui="accordion-trigger">
          <div data-ui="accordion-title-wrapper">
            <span data-ui="accordion-title">{title}</span>
            {subtitle && <span data-ui="accordion-subtitle">{subtitle}</span>}
          </div>
          <span data-ui="accordion-indicator" aria-hidden="true">
            ▾
          </span>
        </BaseAccordion.Trigger>
      </BaseAccordion.Header>
      <BaseAccordion.Panel data-ui="accordion-panel">
        <div data-ui="accordion-content">{children}</div>
      </BaseAccordion.Panel>
    </BaseAccordion.Item>
  );
}

AccordionItem.displayName = 'AccordionItem';
