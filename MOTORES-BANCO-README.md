# Motores lendo a base canônica v2

Esta entrega troca somente a interface de entrada/saída. As funções de cálculo
do Motor Principal v6 e do Motor de bônus v1 foram preservadas e protegidas por
hash de AST em `tests/test_formula_guard.py`.

## Contratos usados

- Otimização lê `clubef_read_v2.motor_input_v2`, versão
  `motor-input-v3.0.0`. A própria view já filtra
  `motor_otimizacao_completo = true` e o adaptador confere a flag novamente.
- Bônus lê `clubef_read_v2.motor_bonus_input_v2`, versão
  `motor-bonus-input-v4.0.0`, e exige `motor_bonus_completo = true`.
- Resultados do principal vão exclusivamente para
  `clubef_read_v2.motor_optimization_results_v2`.
- Resultados de bônus vão exclusivamente para
  `clubef_read_v2.motor_bonus_results_v2` e referenciam o `result_id` da
  otimização.
- Toda gravação nasce `status=pendente_validacao` e `is_current=false`.
  Nenhum script promove resultado e nenhum resultado é escrito em `cards_v2`,
  `cards_base` ou outra tabela autoritativa.

Staging não é fonte do motor. `clubef_stage_v2.*` serve para ingestão,
proveniência, quarentena e readback; os motores usam apenas as duas views de
leitura promovidas acima.

## Trava obrigatória da fila

O exportador exige um manifesto com exatamente:

- 699 `card_id` originais, únicos e ordenados;
- `ambiguous_excluded: 127`;
- `incomplete_excluded: 44`;
- SHA-256 canônico da lista.

Se um dos 699 não estiver exposto por `motor_input_v2`, se uma flag estiver
falsa, se houver slot ambíguo/divergente ou se o hash não casar, a exportação
para. Os 127 ambíguos e 44 incompletos nunca entram no snapshot ou na
`fila_v6.json`.

## Configuração local (sem segredos no Git)

Copie `config.motor.example` para um arquivo local fora do Git e exporte as
variáveis no terminal. Use chave de leitura no exportador e uma chave de
backend restrita às duas tabelas de resultado no writer. Nunca use chave de
escrita no frontend.

Instale a dependência:

```bash
python -m pip install -r requirements-motores.txt
```

Exporte um snapshot imutável e a fila de pares card/função:

```bash
python programas/export_motor_db_snapshot.py \
  --queue filas/fila_impetos_699.json \
  --output snapshots/motores-699.json \
  --fila-output fila_v6.json
```

Antes de qualquer execução, rode:

```bash
python -m unittest discover -s tests -v
```

Ative a nova interface:

```bash
export MOTOR_INPUT_SOURCE=db_snapshot
export MOTOR_DB_SNAPSHOT=snapshots/motores-699.json
export MOTOR_OUTPUT_WRITE_ENABLED=1
export MOTOR_EXECUTION_ID="execucao-definida-pelo-usuario"
python programas/roda_lote_v6.py
python programas/motor_bonus.py
```

Não crie `GRAVA-DIRETO.txt` no modo DB v2: o principal para se detectar o
writer legado. O bônus também pula integralmente os upserts legados de insumos,
`cards_base` e `bonus` quando o modo DB está ativo.

## Readback

Depois da execução externa, confira a execução sem promover nada:

```sql
select card_id, funcao_codigo, input_version, input_hash, status, is_current,
       result_id, created_at
from clubef_read_v2.motor_optimization_results_v2
where execution_id = '<MOTOR_EXECUTION_ID>'
order by card_id, funcao_codigo;

select card_id, funcao_codigo, optimization_result_id, input_version,
       input_hash, status, is_current, result_id, created_at
from clubef_read_v2.motor_bonus_results_v2
where execution_id = '<ID DA EXECUCAO DO BONUS>'
order by card_id, funcao_codigo;
```

O resultado esperado antes de validação é sempre `pendente_validacao` e
`is_current=false`.

## Rollback

O rollback operacional é imediato e não destrutivo: desligue
`MOTOR_OUTPUT_WRITE_ENABLED`, remova `MOTOR_INPUT_SOURCE=db_snapshot` e volte ao
snapshot/arquivos locais anteriores. No Git, restaure a referência criada em
`backup/pre-tarefa8-motores-20260824`. Resultados já inseridos permanecem como
histórico não atual; não apague nem marque como atuais durante o rollback.

