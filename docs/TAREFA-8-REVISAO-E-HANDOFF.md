# Tarefa 8 — revisão somente leitura e handoff

## Entradas antigas e substituição

| Insumo | Fonte antiga | Fonte/camada nova |
|---|---|---|
| Card, 26 atributos, orçamento, posições, estilo | `dados/base_unica.json`, antes `cards.json` + `cards_efhub.json` | `clubef_read_v2.motor_input_v2.input_payload.card` por `card_id` original |
| Slots, deltas, condicional e vagas | campos `nm`, `sl` e derivados locais | `motor_input_v2.input_payload.impetos`; vaga somente 4/4/1 |
| Habilidades nativas, raras, pool e IA | `raras_por_card.json`, `falta_por_card.json`, base local | `motor_input_v2.input_payload.habilidades` |
| Função compatível | `fila_v6.json` e molde local | `motor_input_v2.input_payload.funcao`, materializado em fila local imutável |
| Corpo, pé ruim, estilo e IA | `dados/base_unica.json` | `clubef_read_v2.motor_bonus_input_v2.input_payload.card` |
| Molde, técnicos, habilidades, bloqueios, régua, multiplicador e parâmetros de bônus | JSONs locais | tabelas `public.insumo_*`, congeladas dentro do snapshot exportado |
| Otimização | `saida_v6/linhas.jsonl` e opcionalmente `public.builds` | arquivo local de recuperação + `motor_optimization_results_v2` |
| Bônus | `saida_v6/bonus.jsonl` e `public.bonus` | arquivo local de recuperação + `motor_bonus_results_v2` |

Os dois links de imagem permanecem no payload/proveniência canônico, mas não
entram em fórmula nem bloqueiam o motor. A autoridade de cálculo é separada da
publicação e da imagem.

## Revisão da lógica atual

### Comprovado

- O principal trabalha com vetor fixo de 26 atributos, dez barras e orçamento
  acumulado por nível; salto pertence ao par `aerialStrength`/`gk1` e é tratado
  conjuntamente no DP.
- A cadeia preservada é base+barras com trava 99, multiplicador tático com a
  tabela medida, depois técnico/ímpeto; os efeitos de habilidade usam a
  referência base+barras.
- O motor maximiza a régua e mantém as podas CORTE 8/9/10/11 existentes.
- O bônus mantém quatro parcelas independentes: corpo, pé ruim, estilo ativo e
  estilos de IA. Ausência conhecida de IA vale zero; dado não coletado vira
  `faltou`.
- O módulo de bônus executa I/O no import; comportamento antigo preservado.
- No legado, o bônus também escrevia insumos e `cards_base.estilo_ia`. No modo
  DB v2 esse bloco é totalmente pulado.
- Os hashes AST das funções/classes matemáticas selecionadas são idênticos ao
  commit-base `32cd942e6c4ced81ee1741c06cece7941cba8a3d`.

### Suspeita / risco operacional, sem correção nesta tarefa

- `b_total` soma apenas parcelas numéricas mesmo quando `faltou` contém campos;
  consumidores que ignorem `faltou` podem interpretar uma nota parcial como
  completa.
- Linhas JSONL inválidas no bônus são ignoradas. O modo DB valida cada par que
  chegou, mas uma linha local corrompida pode reduzir o conjunto calculado.
- O principal usa multiprocessing e arquivos de checkpoint sem lock entre duas
  instâncias; duas rodadas simultâneas na mesma pasta não foram provadas seguras.
- O writer não tenta promover ou resolver conflitos; uma repetição com o mesmo
  `execution_id/card_id/funcao_codigo` falha pela restrição única. Isso é
  intencionalmente fail-closed, mas exige novo ID para rerun.

### Sem evidência de defeito

- Não foi encontrada mudança matemática causada pela adaptação.
- Não foi encontrada escrita da nova interface em tabela-base, staging,
  UI/Ranking/Ficha/builds ou tabela pública antiga.
- Não foi executada carga ampla nem reconstrução de ímpetos neste ambiente.

## Gates de promoção

O motor não promove. A cadeia correta é: staging/proveniência e quarentena →
entidade canônica → flags de completude → views de entrada → resultado
`pendente_validacao` → validação externa → promoção explícita separada. Uma
linha de staging, um resultado pendente ou um card sem a flag do motor nunca é
fonte final.

