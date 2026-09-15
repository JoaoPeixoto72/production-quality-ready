# first-run — commercial-readiness

Régua para o check `first-run-timed`.

## Protocolo

1. **VM virgem.** Windows/Mac limpo, sem nada instalado além do que a app
   assume que existe (ex: WebView2 no Windows 10 antigo).
2. **Sem rede em parte do teste.** Testar arranque sem internet — a app não
   pode ficar presa a esperar por servidor externo.
3. **Cronómetro.** Do duplo-click no instalador ao primeiro resultado útil
   (não ao primeiro pixel na tela — ao primeiro momento em que o utilizador
   consegue fazer o que veio fazer).

## Registar

- Tempo (segundos).
- O que a app descarregou durante esse tempo (binários, modelos).
- Que permissões pediu, e em que ordem.
- Se pediu confirmação de licença antes de servir para alguma coisa
  (fricção de activação vs valor).

## Régua

- Instalador → primeiro resultado útil em < 5 min: `PASS`.
- 5–15 min: `MEDIUM`.
- > 15 min ou "não conseguiu" (rede caiu, download falhou, permissão negada
  a meio sem recovery): `FAIL`.
