# code-review — Frontend

Ruler for frontend code (React, Vue, Svelte, vanilla; the essentials are shared).

## Effects

Every `useEffect` / `onMounted` / `$effect` answers three questions, in an
adjacent comment or obviously in the code:

1. **When does it run?** — dependencies listed.
2. **How does it stop?** — cleanup or unsubscribe.
3. **What if the component unmounts midway?** — cancellation (AbortController,
   flag) or why it cannot happen.

## State

- State that survives a re-render lives in `useState`/`ref`/a store, not in
  closure variables.
- Derivable state is **not** stored — it is computed. `useMemo` only after
  measuring; otherwise it is a premature cache.
- Refs (`useRef`) are for mutable values that must NOT trigger a re-render.
  State the UI shows kept in a ref is a silent bug.

## Cancellation

A `fetch` without an `AbortController` in an effect is a bug:

```jsx
useEffect(() => {
  const ctrl = new AbortController();
  fetch(url, { signal: ctrl.signal })
    .then(r => r.ok && setData(await r.json()))
    .catch(e => e.name !== 'AbortError' && setError(e));
  return () => ctrl.abort();
}, [url]);
```

## Bundle

Budget declared by the project (`perf.budgets-declared`), checked by this owner
with the stack's bundle analyser. No whole-library import when one function
will do (lodash, moment, date-fns → tree-shakeable or replaced).

## Types

`any` only with a justifying comment; `as` only when the compiler cannot infer
and the invariant is stated. `strict: true` in tsconfig.

## Tests

- Test behaviour, not implementation: fire input, check visible output
  (Testing Library philosophy).
- Snapshots only where the output is canonical and stable; otherwise they
  become "accept everything".
- Each test states its risk (comment at the top). The oracle is the specific
  assertion, not "it did not crash".
