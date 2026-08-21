# Reconhecimento de ímpetos no eFootball DB

## Objetivo

Para cada espaço de ímpeto, reconhecer ausência de espaço, vaga livre ou ímpeto nativo ocupado; depois traduzir para o formato interno.

## Método validado

O jogo/Konami foi a fonte de verdade. O usuário conferiu no videogame e as caixas foram comparadas com os retornos do eFootball DB.

| Amostra | Estado confirmado |
| --- | --- |
| CAF Africa Cup of Nations Selection — 13 ago 2026 | Sem ímpeto/sem vaga |
| Tactical Defence — 13 ago 2026 | Sem ímpeto/sem vaga |
| English League Selection — 13 ago 2026 | Uma vaga livre |
| New Season Campaign 2027 | Sem ímpeto/sem vaga |
| National Team Selection Malaysia — mai 2026 | Uma vaga livre |
| National Team Selection Thailand — mai 2026 | Uma vaga livre |
| Moroccan League Selection — 13 ago 2026 | Sem ímpeto/sem vaga |

## Regra resultante

- Sem objeto de booster = sem ímpeto e sem vaga.
- `Booster Slot` = vaga livre.
- Qualquer booster diferente = ímpeto nativo ocupado.
- A ausência nunca pode virar vaga por inferência.
- O código de `Booster Slot` não pode ser tratado como código de ímpeto real; tipo e subtipo devem ser lidos juntos.

## Coleta e normalização

1. Partir do identificador canônico da carta.
2. Consultar a variação no eFootball DB.
3. Ler cada espaço de booster.
4. Aplicar a regra de reconhecimento.
5. Guardar o código se o espaço estiver ocupado.
6. Consultar o catálogo de boosters da fonte.
7. Traduzir para nome e nível pelo catálogo interno.
8. Persistir estado, ímpeto e condição na tabela agregada.

O retorno oferece efeitos e campos de categoria/alvo que permitem normalizar se o ímpeto é condicional e qual é a regra condicional.

## Responsabilidade

Tudo relativo a ímpetos — vagas, nativos, nível, efeitos e condicionais — pertence ao eFootball DB. Outras rotinas não devem trazer nem sobrescrever esses dados.
