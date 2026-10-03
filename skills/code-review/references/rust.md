# code-review — Rust

Ruler for Rust code.

## Panics in production

No `.unwrap()`, `.expect(...)`, `panic!(...)`, `todo!()`, `unimplemented!()`
on paths the app can reach in production. Where one exists, right beside it:

```rust
// SAFETY / OK: <invariant that guarantees this never fires>
let x = maybe.unwrap();
```

Without that comment, `runtime.no-silent-panics` fails.

## Errors

`?` propagates; a `Result` at the binary's top closes with a structured log
(`reliability-audit` §2) and a non-zero exit code. Never swallow with `let _ =`
without a reason — the linter looks for it.

## Concurrency

- State shared between threads: `Mutex`, `RwLock`, or a channel. `Arc` alone
  synchronises nothing.
- `Send`/`Sync` respected; `unsafe impl Send/Sync` only with the invariant
  proven in a comment.
- `async`: cancellation is cooperative — dropping a task leaves resources
  consistent. Test with `tokio::select!` and a timeout branch cancelling the other.

## Tests

- One test per enumerated risk; the risk→test matrix lives in the project's
  state document (`ESTADO.md` or equivalent), kept live by `reliability-audit`.
- Property tests (proptest, quickcheck) where the input has structured space;
  unit tests for concrete cases.
- `#[should_panic]` only when the panic is the contract — its message is the
  oracle only if the contract guarantees it.

## Ownership

- Explicit lifetimes when the compiler asks; otherwise let it infer.
- An expensive `.clone()` (`String`, `Vec`, `Arc<T>` with a large `T`) is
  confirmed by a profiler before being accepted — it crosses `perf.*`.

## Cargo

- `Cargo.lock` committed for binaries. Feature flags documented.
- `cargo audit` clean (`security-audit`'s, but this owner runs it in the pipeline).
