# Impacto de vagas de ímpeto hipotéticas — 20/08/2026

Auditoria somente de leitura. Nenhum cálculo foi executado e nenhuma linha do Supabase foi alterada.

## Critério

Entraram na lista os cards com `card_impeto.por_que = "vaga livre — A COLETAR"` que também possuem um build com `impeto` preenchido.

## Totais validados

- 443 cards tinham a marca antiga `vaga livre — A COLETAR`;
- 261 deles possuem build efetivamente afetado;
- 1.142 registros únicos de build (card + função) foram identificados;
- 0 linhas de `tela_encaixe` têm ímpeto explícito no JSON para esse conjunto.

## Arquivos

- `impacto-261-cards-1142-builds.json`: lista completa por card, com versão/box disponível, motivo, registros de `card_impeto` e chaves dos builds afetados.
- `fila-refazer-261-cards-1142-builds.json`: fila segura de planejamento, uma linha por card + função. Ela não é executada automaticamente.
- `impacto-1142-builds.csv`: conferência tabular das 1.142 linhas.

## Segurança

A fila contém `executar_agora: false`. Ela só deve ser convertida em fila do motor depois de validar a vaga de cada card e aplicar a regra oficial corrigida.

