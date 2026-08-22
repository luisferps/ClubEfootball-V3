# Plano de ação — reconstrução da base agregada

**Status:** plano acordado

**Registrado em:** 21/08/2026 às 21:44:04 (America/Sao_Paulo, UTC-03:00)

## 1. Fontes e responsabilidades

- O **eFScout sai totalmente** do fluxo. Ele não será consultado, usado como fonte, mantido como produtor nem autorizado a sobrescrever dados.
- Os únicos produtores da tabela agregada serão:
  1. **Vigia**;
  2. **eFootball DB**;
  3. **Motor Principal**;
  4. **Motor de bônus**.
- O **catálogo** e a **tabela de topo** permanecem como fontes internas do sistema.
- A tela será responsável por calcular o **percentual** e a **etiqueta** apresentados ao usuário.

## 2. Reaproveitamento dos dados do Vigia

- Os dados confiáveis já coletados pelo Vigia para as **2.568 cartas** serão reutilizados.
- Todos os campos antigos relacionados a **ímpetos** serão ignorados, mesmo quando estiverem preenchidos nessas cartas.

## 3. Fonte oficial de ímpetos e boxes

O **eFootball DB será a fonte única e oficial** dos dados de ímpetos e boxes. A nova coleta deverá obter e registrar:

- slots de ímpeto;
- estado de cada slot;
- identificadores estáveis;
- tipo e subtipo;
- condição ou caráter condicional, quando existir;
- efeitos;
- nome da box;
- data da box;
- vínculo entre a carta e a box.

Nenhuma dessas informações será preenchida a partir do eFScout ou dos campos antigos de ímpeto.

## 4. Comparação, gravação e reconstrução

- A coleta nova será comparada com o banco antigo **somente para marcar divergências**.
- Todos os dados obtidos na nova coleta serão gravados no **banco novo**, inclusive quando não houver divergência.
- As linhas da tabela agregada das cartas divergentes serão refeitas com base nas fontes e regras deste plano.
- A confirmação direta no jogo prevalecerá como **auditoria final** quando houver dúvida ou conflito.

## 5. Preservação das bases existentes

- A tabela agregada foi esvaziada **somente em relação aos 21 registros de teste**.
- As demais tabelas não deverão ser apagadas.
- Tabelas que deixarem de participar do fluxo poderão, quando necessário, ser aposentadas e preservadas como arquivo histórico.

## 6. Implantação controlada

- O Vigia, o coletor do eFootball DB, o Motor Principal e o Motor de bônus serão testados primeiro em um **grupo controlado de cartas**.
- A ampliação da execução ocorrerá somente após a validação dos resultados desse grupo.
- O trabalho de design poderá avançar em paralelo à coleta, sem alterar as responsabilidades das fontes nem as regras de gravação definidas acima.
