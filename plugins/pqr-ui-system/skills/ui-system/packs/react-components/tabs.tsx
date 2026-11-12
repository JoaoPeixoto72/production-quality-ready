import * as React from 'react';
import { Tabs as BaseTabs } from '@base-ui/react/tabs';

export const Tabs = BaseTabs.Root;

export const TabsList = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof BaseTabs.List>
>((props, ref) => <BaseTabs.List ref={ref} data-ui="tabs-list" {...props} />);
TabsList.displayName = 'TabsList';

export const TabsTab = React.forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<typeof BaseTabs.Tab>
>((props, ref) => <BaseTabs.Tab ref={ref} data-ui="tabs-tab" {...props} />);
TabsTab.displayName = 'TabsTab';

export const TabsPanel = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof BaseTabs.Panel>
>((props, ref) => <BaseTabs.Panel ref={ref} data-ui="tabs-panel" {...props} />);
TabsPanel.displayName = 'TabsPanel';
