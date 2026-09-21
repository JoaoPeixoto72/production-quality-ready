# Heurísticas de CRO e Conversão Comercial (`audit-website`)

A otimização da taxa de conversão (CRO) avalia a capacidade da montra ou landing page de conduzir o utilizador à conclusão de objetivos sem fricção nem enganos.

---

## 1. Princípios de Avaliação de Conversão

### 1.1 Proposta de Valor Acima da Dobra (*Above the Fold*)
- O visitante deve compreender em menos de 5 segundos:
  1. O que é o produto ou serviço?
  2. Para quem é?
  3. Qual é o benefício ou diferenciação concreta?
- **Defeito Típico:** Sliders em carrossel rotativo automático (distração visual que diminui o CTR) ou títulos poéticos/vagos que não dizem o que o negócio faz.

### 1.2 Call to Action (CTA) Principal
- Deve existir **um CTA primário evidente** por ecrã (ex.: "Começar Grátis", "Comprar Agora", "Pedir Demonstração").
- O botão deve ter contraste visual superior em relação ao fundo da página (cumprindo WCAG AA).
- Ação claramente expressa no verbo (evitar palavras passivas como "Clique aqui" ou "Submeter").

### 1.3 Minimização de Fricção em Formulários
- Cada campo adicional num formulário de captação reduz a taxa de conversão entre 3% e 10%.
- **Campos obrigatórios:** Devem ser estritamente necessários à transação inicial (ex.: apenas Email e Nome para newsletter/lead; nunca exigir morada completa ou telefone num contacto simples).
- **Usabilidade:**
  - Uso de `autocomplete` para preenchimento automático pelo browser (`autocomplete="name"`, `autocomplete="email"`).
  - Teclado adequado em mobile (`type="tel"`, `type="email"`, `inputmode="numeric"`).
  - Mensagens de validação em linha e claras (não genéricas como "Erro").

### 1.4 Ausência de Padrões Manipuladores (*Dark Patterns*)
- **Checkboxes Pré-assinaladas:** Proibidas para consentimento de marketing ou subscrição adicional sob o RGPD e Diretiva dos Direitos dos Consumidores da UE.
- **Custos Ocultos:** Transparência de taxas, portes e IVA antes da etapa de pagamento final.
- **Falsa Urgência:** Temporizadores regressivos fictícios que reiniciam em cada reload.

### 1.5 Prova Social e Confiança
- Presença de sinais verificáveis de autoridade:
  - Testemunhos com identificação real, logótipos de clientes ou certificações.
  - Informações de apoio ao cliente (contacto, email, NIF da empresa no rodapé).
  - Selos de segurança e métodos de pagamento reconhecidos no checkout.
