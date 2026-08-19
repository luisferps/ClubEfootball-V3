# -*- coding: utf-8 -*-
"""
FONTE UNICA — o motor passa a beber de UM lugar so.

ORDEM DO LUIS, repetida varias vezes e finalmente atendida em 14/08/2026:
    "O problema nao e a fonte vir de lugares diferentes. O problema e elas nao
     ficarem num mesmo lugar, porque ai o motor procura em varios lugares.
     O motor tem que procurar num lugar so."

COMO ERA
    o motor montava o card lendo DOIS arquivos e fazendo o merge na mao:
        dados/cards.json   +   cards_efhub.json   (precedencia por campo)

COMO FICA
        dados/base_unica.json      <- e so. UM lugar.

    A base unica JA e o resultado desse merge, feito pelo unificar_base.py, que
    obedece o precedencia.json e ainda aplica a trava da data e o CONFERIDO.json.
    Ou seja: nao e uma fonte nova. E a MESMA regra, num arquivo so, ja resolvida.

    E a base_unica.json e o espelho da tabela `cards_base` no Supabase:
        SUBIR-BASE.bat   manda daqui para o banco
        BAIXAR-BASE.bat  traz do banco para ca

POR QUE ISSO IMPORTA — o erro de 14/08 nao teria acontecido
    145 cards estavam com a vaga de impeto [1,1], que nao existe no jogo.
    A base unica ja tinha corrigido os 145 de manha. O cards.json nao.
    O motor le o cards.json -> rodou 562 linhas com nota inflada.
    Lendo a base, esse erro seria impossivel.
"""

# ===========================================================================
#  ⛔ 19/08 — ESTE PROGRAMA MORA NO ClubEfootball\programas.
#     "Nao existe mais essa pasta pro futebol. A pasta agora e ClubEfootball.
#      E tudo la." (Luis, 19/08)
#
#  ⛔ ESTE BLOCO VEM ANTES DOS IMPORTS, E POR MEDIDA. Quando ele ficava
#     DEPOIS, o `from equacao import ...` la de cima ja tinha rodado e pegava
#     o arquivo errado — o programa nem chegava a saber onde estava a casa.
#
#     Ele faz duas coisas, e as duas importam:
#       1. acha a pasta que tem o config.txt e trabalha LA (os dados nao se
#          mudaram: dados\, saida_v6\, encaixe\ continuam na casa);
#       2. poe `programas\` na frente do caminho de busca, para os modulos
#          vizinhos serem achados aqui e nao na raiz.
# ===========================================================================
import os as _os, sys as _sys

def _acha_a_casa(inicio):
    p = inicio
    for _ in range(5):
        if _os.path.exists(_os.path.join(p, 'config.txt')):
            return p
        pai = _os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None

_MEU_LUGAR = _os.path.dirname(_os.path.abspath(__file__))
_CASA = _acha_a_casa(_MEU_LUGAR) or _acha_a_casa(_os.getcwd())
if _CASA:
    if _os.path.abspath(_os.getcwd()) != _os.path.abspath(_CASA):
        _os.chdir(_CASA)
    if _CASA not in _sys.path:
        _sys.path.append(_CASA)          # a casa vem DEPOIS
if _MEU_LUGAR in _sys.path:
    _sys.path.remove(_MEU_LUGAR)
_sys.path.insert(0, _MEU_LUGAR)          # `programas` vem PRIMEIRO
# --------------------------------------------------------------------------
import json, os

BASE_UNICA = os.path.join('dados', 'base_unica.json')


def existe():
    return os.path.exists(BASE_UNICA)


def carrega_base():
    """Devolve {id_base: card} no mesmo formato que o motor ja espera.

    Mesma regra do _recarrega_cards() antigo para escolher entre variantes do
    mesmo card (id@POS): fica a de maior orcamento.
    """
    with open(BASE_UNICA, encoding='utf-8') as f:
        bu = json.load(f)
    base = {}
    for c in (bu.get('cards') or []):
        b = str(c.get('id')).split('@')[0]
        if b not in base or (c.get('orc') or 0) > (base[b].get('orc') or 0):
            base[b] = c
    return base


def carrega_tudo():
    """Todos os insumos do motor, do MESMO arquivo. Um lugar so.

    Devolve o dicionario inteiro da base. Quem chama pega o que precisa:
        base['molde']              o denominador da nota
        base['tecnicos_catalogo']  CHAVE = id
        base['habilidades']        CHAVE = camelCase
        base['bloqueio']           em que funcao cada habilidade nao entra
    """
    with open(BASE_UNICA, encoding='utf-8') as f:
        return json.load(f)


def carimbo():
    try:
        return int(os.path.getmtime(BASE_UNICA))
    except Exception:
        return None
