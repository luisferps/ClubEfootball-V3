# Plano de consolidação de rotinas legadas

## Objetivo

Eliminar sobrescritas concorrentes de rotinas JavaScript do preview sem alterar o comportamento já validado. A execução deve ocorrer em blocos independentes, sempre com teste prático antes de avançar.

## Pré-requisitos

- Trabalhar apenas sobre a cópia atual já separada em CSS e JavaScript externos.
- Manter a ordem de carregamento dos arquivos externos.
- Não alterar dados, Supabase, motor remoto ou frontend publicado durante esta consolidação.
- Os controles de **recalcular** continuam ocultos intencionalmente. Eles não são defeito nem entram na validação de uso comum; só deverão ser testados quando forem expostos em uma área administrativa protegida.

## Backup obrigatório

Antes de cada bloco, criar uma cópia datada do arquivo JavaScript que será alterado. Se a validação do bloco falhar, restaurar somente a cópia criada para aquele bloco e interromper a sequência.

## Ordem de execução

### 1. `otimizar` e `otimizarBarras`

**Escopo:** consolidar as várias definições dessas duas rotinas em uma única fonte pública para cada uma, preservando assinaturas, chamadas existentes e os wrappers necessários para restaurar o retrato do motor e redistribuir barras.

**Restrições:** não tocar em `fechar`, `encModo`, `abrir` ou `t6ReabreFicha`; não tornar visíveis os controles de recalcular.

**Validação obrigatória:** Home; Elenco; Ranking; Boxes atuais e anteriores; abrir e fechar ficha; controles de build; retorno/Voltar; Elenco sem duplicação; console sem função ausente.

**Reversão:** qualquer falha nesses fluxos restaura apenas o backup deste bloco.

### 2. `encModo`

**Escopo:** consolidar exclusivamente a rotina e seus wrappers de modo da ficha, mantendo a mesma troca entre modos e a mesma marcação visual atual.

**Restrições:** não alterar os grupos 1, 3 ou 4 nem a visibilidade dos controles administrativos.

**Validação obrigatória:** todos os fluxos gerais acima, mais alternância entre os modos visíveis da ficha.

**Reversão:** restaurar somente o backup datado deste bloco diante da primeira regressão.

### 3. `fechar`

**Escopo:** consolidar somente os fechamentos de ficha e seus retornos de página, preservando URL, estado anterior e limpeza visual.

**Restrições:** não alterar abertura de ficha, Elenco ou navegação de abas.

**Validação obrigatória:** abrir ficha por Ranking, Boxes e Elenco quando aplicável; fechar pelo controle próprio; Voltar; recarregar após o retorno; confirmar que Elenco não duplica.

**Reversão:** restaurar somente o backup deste bloco se qualquer retorno falhar.

### 4. `abrir` e `t6ReabreFicha`

**Escopo:** consolidar a abertura e reabertura da ficha em uma cadeia única, mantendo cartão, função, build selecionada e URL corretos.

**Restrições:** não reintroduzir rotas residuais, cabeçalhos de Ranking no Elenco ou alterações de layout não pedidas.

**Validação obrigatória:** abrir por Home, Ranking, Boxes e Elenco; trocar build quando o seletor estiver disponível; fechar e voltar; primeiro clique em Elenco; recarregar no Elenco; console sem função ausente.

**Reversão:** restaurar somente o backup deste bloco ao primeiro erro.

## Estado já validado da separação

O HTML passou a carregar, nesta ordem: `clubefut.css`, `dados-e-catalogos.js`, `motor-e-ficha-base.js`, `elenco.js`, `ficha-ajustes.js` e `paginas-e-navegacao.js`.

Validações já concluídas no servidor local:

- Home abriu.
- Elenco abriu no primeiro clique e não duplicou ao abrir novamente.
- Ranking abriu e o filtro Ataque alterou a listagem.
- Boxes atuais e anteriores carregaram.
- Uma ficha abriu e fechou pelo botão Voltar.
- Não houve erros ou avisos no console nesses fluxos.

## Pendência controlada

Os comandos de recalcular foram encontrados ocultos na interface atual. A pendência é testá-los somente se forem disponibilizados em uma área administrativa protegida; não expô-los como parte desta consolidação.
