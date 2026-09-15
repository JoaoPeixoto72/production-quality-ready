# Diretrizes Globais do Plugin `production-quality-ready`

Este plugin implementa um sistema de qualidade composto por owners independentes:

1. **Um assunto, um owner, uma regra**: Cada tema de qualidade tem um único owner canónico e critérios binários de aceitação.
2. **Evidência é um ficheiro, não uma chamada**: Nenhuma skill invoca outra skill. Os owners gravam evidências em `.audit/<owner>/<producer>--<check>.evidence.yaml`.
3. **Orquestrador estritamente leitor**: `audit-app` apenas lê evidências e aplica gates declarativos de `.agents/gates.json`.
4. **Gate binário, nunca um score**: Ausência de prova nunca é aprovação (`BLOCKED (n/m)`).
5. **Ciclo de trabalho local**:
   - Abrir sessão com `start-work`
   - Rever código com `review-change`
   - Fechar sessão e atualizar `ESTADO.md` com `close-work`
   - Provar funcionamento em runtime com `verify`
