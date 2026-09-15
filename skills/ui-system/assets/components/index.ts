/**
 * @project/ui — Ponto de exportação público do design system (ui-system).
 * A aplicação consome EXCLUSIVAMENTE este ficheiro ou o package @project/ui.
 * As primitivas do Base UI permanecem como detalhe privado e blindado de implementação.
 *
 * Catálogo completo de 34 componentes (100% de paridade com HeroUI v3 + Base UI v1.8.0).
 */

/* ============================================================
   1. Controlos Gerais & Estrutura
   ============================================================ */
export * from './button';
export * from './card';
export * from './separator';
export * from './skeleton';
export * from './spacer';
export * from './scroll-shadow';

/* ============================================================
   2. Formulários & Seleção
   ============================================================ */
export * from './field';
export * from './input';
export * from './textarea';
export * from './checkbox';
export * from './radio';
export * from './select';
export * from './switch';
export * from './slider';
/* Os que o catálogo não trazia, e que uma app com um editor de vídeo acaba
   sempre por precisar: um número preso a um intervalo, uma cor, e uma escolha
   entre poucas em pílulas. */
export * from './number-field';
export * from './color-field';
export * from './segmented-control';
export * from './radio-cards';

/* ============================================================
   3. Feedback, Progresso & Status
   ============================================================ */
export * from './spinner';
export * from './progress';
export * from './circular-progress';
export * from './badge';

/* ============================================================
   4. Identidade, Chips & Teclado
   ============================================================ */
export * from './avatar';
export * from './user';
export * from './chip';
export * from './kbd';
export * from './snippet';

/* ============================================================
   5. Navegação & Menus
   ============================================================ */
export * from './navbar';
export * from './breadcrumbs';
export * from './pagination';
export * from './tabs';
export * from './link';
export * from './dropdown';

/* ============================================================
   6. Overlays, Modais & Superfícies Expansíveis
   ============================================================ */
export * from './dialog';
export * from './drawer';
export * from './popover';
export * from './tooltip';
export * from './accordion';

/* ============================================================
   7. Visualização de Dados
   ============================================================ */
export * from './table';
