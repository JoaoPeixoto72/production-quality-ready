# code-review — Rust

Régua específica para código Rust.

## Pânico em produção

Nenhum `.unwrap()`, `.expect(...)`, `panic!(...)`, `todo!()`, `unimplemented!()`
em caminhos que a aplicação consegue atingir em produção. Onde existe,
imediatamente adjacente:

```rust
// SAFETY / OK: <invariante que garante que isto nunca dispara>
let x = maybe.unwrap();
```

Sem esse comentário: `runtime.no-silent-panics` falha.

## Erros

`?` propaga; `Result` no topo do binário fecha com log estruturado
(`reliability-audit` §2) e código de saída não-zero. Nunca engolir com `let _ =`
sem justificação — o linter procura isso.

## Concorrência

- Estado partilhado entre threads: `Mutex`, `RwLock`, ou canal. `Arc` sozinho
  não sincroniza nada.
- `Send`/`Sync` respeitados. `unsafe impl Send/Sync` só com invariante
  provada em comentário.
- `async`: cancelamento é cooperativo — `drop` da task tem de deixar
  recursos consistentes. Testar com `tokio::select!` e branch de timeout
  que cancela o outro.

## Testes

- Um teste por risco enumerado; a matriz risco→teste vive em
  no documento de estado do projecto (`ESTADO.md` ou equivalente) (é reliability-audit
  responsibility keeping it live, não deste owner).
- Property tests (proptest, quickcheck) preferidos onde o input tem
  espaço estruturado; unit test onde é caso concreto.
- `#[should_panic]` só quando o pânico é o contrato — a mensagem é o
  oráculo apenas se o contrato a garantir.

## Ownership

- Lifetimes explícitos quando o compilador pede; senão, deixar inferir.
- `.clone()` que é caro (`String`, `Vec`, `Arc<T>` onde `T` é grande)
  identificado por profiler antes de aceitar como necessário — cruza com
  `perf.*` deste owner.

## Cargo

- Lock file (`Cargo.lock`) commitado para binários. Feature flags
  documentadas.
- `cargo audit` limpo (isso é `security-audit`, mas este owner corre-o no
  pipeline).
