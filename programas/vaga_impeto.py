# -*- coding: utf-8 -*-
"""Regra unica e conservadora para a vaga de impeto.

Ausencia de booster, ``sl=[0, 1]`` vindo de fonte antiga e resposta vazia de
uma API NAO provam vaga livre. O motor so pode testar um impeto hipotetico
quando uma fonte especifica marcou ``VAGA`` ou quando existe uma confirmacao
manual rastreavel.
"""

ESTADO_LIVRE = "confirmada_livre"
ESTADO_SEM_VAGA = "confirmada_sem_vaga"
ESTADO_DESCONHECIDA = "desconhecida"


def _lista_vaga(card):
    valor = card.get("vaga")
    if isinstance(valor, dict):
        valor = valor.get("v")
    return list(valor) if isinstance(valor, (list, tuple)) else []


def _marcador(valor):
    return str(valor or "").strip().upper()


def estado_da_vaga(card):
    """Devolve o estado comprovavel sem inferir pela ausencia de booster."""
    estado = str(card.get("vaga_estado") or "").strip().lower()
    if estado in (ESTADO_LIVRE, "livre", "vaga_livre", "confirmada livre"):
        return ESTADO_LIVRE
    if estado in (ESTADO_SEM_VAGA, "sem_vaga", "sem vaga", "confirmada sem vaga"):
        return ESTADO_SEM_VAGA

    # Campo novo e explicito: ele nunca e deduzido a partir de `sl`.
    if card.get("vaga_livre_confirmada") is True:
        return ESTADO_LIVRE

    vagas = _lista_vaga(card)
    marcadores = [_marcador(x) for x in vagas if x is not None]
    if "VAGA" in marcadores:
        return ESTADO_LIVRE
    if marcadores:
        # NATIVO/ZERADO? sao respostas do coletor. Se nenhuma posicao e VAGA,
        # nao ha autorizacao para o motor inventar candidato.
        return ESTADO_SEM_VAGA

    situacao = str(card.get("impeto_situacao") or "").lower()
    if "conferid" in situacao and ("vaga vazia" in situacao or "vaga livre" in situacao):
        return ESTADO_LIVRE

    if card.get("vaga_confirmada") is True:
        # Confirmacao explicita sem indicacao de vaga livre significa sem vaga.
        return ESTADO_SEM_VAGA
    return ESTADO_DESCONHECIDA


def normaliza_vaga(card):
    """Aplica a regra segura no card e devolve o estado final.

    ``sl`` continua existindo por compatibilidade com o motor, mas deixa de ser
    uma fonte. Ele passa a ser somente o resultado da confirmacao.
    """
    estado = estado_da_vaga(card)
    livre = estado == ESTADO_LIVRE
    card["sl"] = [0, 1] if livre else [0, 0]
    card["vaga_estado"] = estado
    card["vaga_confirmada"] = estado != ESTADO_DESCONHECIDA
    card["vaga_livre_confirmada"] = livre
    card["vagas_livres"] = 1 if livre else 0
    return estado


def pode_testar_impeto(card):
    """Defesa final do motor: so uma vaga livre confirmada abre candidatos."""
    return estado_da_vaga(card) == ESTADO_LIVRE

