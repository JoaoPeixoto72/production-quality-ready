# legal — commercial-readiness

Checklist para o check `legal-clean`. Factos verificáveis no repo. **A
conclusão jurídica é de quem vende**, não desta skill.

## RGPD (GDPR)

- Política de privacidade escrita, acessível na app e no site.
- Base legal declarada para cada tipo de dado colectado.
- Direito ao esquecimento tem caminho documentado.
- Nenhum tracker de terceiros sem consentimento prévio.

## CRA (EU Cyber Resilience Act)

- Vulnerabilidades reportáveis a canal declarado (SECURITY.md).
- Atualizações de segurança separadas de atualizações de feature.
- Suporte de segurança declarado por N anos após venda.

## EAA (European Accessibility Act)

- WCAG 2.2 AA cumprida (cross-reference `design-pro`).
- Declaração de conformidade acessível.

## EULA

- Existe. Foi escrita ou revista por advogado.
- Limitação de responsabilidade coerente com o preço.
- Cláusulas de garantia claras.

## Licenças de dependências

- FFmpeg e codecs comerciais têm licença compatível com o modelo de venda.
- Cada dependência com licença copyleft (GPL, AGPL) tem carve-out ou
  substituto planeado.
- SBOM da release inclui cada licença.
