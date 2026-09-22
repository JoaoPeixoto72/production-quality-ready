# code-review — Rust + Frontend (Tauri, Electron-like)

Régua para projectos com Rust no backend e frontend web (Tauri é o caso
padrão).

Ler primeiro `rust.md` e `frontend.md`. Este ficheiro cobre **só** o que
é específico da combinação, dentro de cada camada — a fronteira entre elas
(invoke, eventos, permissões IPC) é a secção *Contract* deste owner.

## Do lado Rust

- Comandos `#[tauri::command]` são fronteira, não runtime — vão para
  a secção *Contract*. Aqui: se o *corpo* do comando aguenta o input
  já validado.
- `AppHandle`/`Window`/`State<'_, T>` passados a threads: `T: Send + Sync`
  respeitado.
- Painço num comando não crasha a aplicação (Tauri isola), mas emite
  erro genérico ao cliente — logar antes de deixar propagar.

## Do lado frontend

- `invoke(...)` devolve `Promise` — trata-se como qualquer chamada
  cancelável (secção "Cancelamento" de `frontend.md`).
- Eventos vindos do Rust (`listen(...)`) precisam de `unlisten()` no
  cleanup do efeito.
- Nada de assumir que o backend está pronto no primeiro render: espera
  pelo evento `tauri://ready` ou pelo primeiro `invoke` bem-sucedido.

## Bundle Tauri

- Bundle inclui runtime web + binário Rust. Budget é sobre o instalador
  final (`perf.bundle-within-budget`).
- Assets estáticos: `tauri.conf.json → build.distDir`; nada fora dessa
  pasta chega ao produto.
