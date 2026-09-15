# code-review-runtime — Frontend

Régua para código de frontend (React, Vue, Svelte, vanilla; o essencial é
comum).

## Efeitos

Cada `useEffect` / `onMounted` / `$effect` responde a três perguntas
respondidas em comentário adjacente ou por óbvio no código:

1. **Quando corre?** — dependências enumeradas.
2. **Como pára?** — função de cleanup ou desregisto.
3. **O que faz se o componente desmonta a meio?** — cancelamento (Abort
   Controller, flag) ou justificação de que não pode.

## Estado

- Estado que sobrevive a re-render vive em `useState`/`ref`/store, não em
  variáveis de closure.
- Estado derivável **não** é armazenado — calculado. `useMemo` só depois
  de medir; senão, cache prematura.
- Refs (`useRef`) são para valores mutáveis que NÃO disparam re-render.
  Colocar estado que a UI mostra num ref é bug silencioso.

## Cancelamento

`fetch` sem `AbortController` num efeito é bug. Ver:

```js
useEffect(() => {
  const ctrl = new AbortController();
  fetch(url, { signal: ctrl.signal })
    .then(r => r.ok && setData(await r.json()))
    .catch(e => e.name !== 'AbortError' && setError(e));
  return () => ctrl.abort();
}, [url]);
```

## Bundle

Budget declarado em `performance-audit`; verificado por este owner com o
bundle analyser do stack. Nenhum import de biblioteca inteira quando basta
uma função (lodash, moment, date-fns → tree-shakeable ou substituir).

## Tipos

`any` só com comentário justificando; `as` só quando o compilador não pode
inferir e a invariante está declarada. `strict: true` no tsconfig.

## Testes

- Teste de comportamento, não de implementação: dispara input, verifica
  saída visível (Testing Library filosofia).
- Snapshots só onde o output é canónico e estável; senão viram
  "aceito tudo".
- Cada teste declara o risco (comentário no topo). Oráculo é a asserção
  específica, não "não crashou".
