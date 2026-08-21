# -*- coding: utf-8 -*-
"""Le equivalencias confirmadas entre o codigo externo do card e o efeito.

O `boostId` do efHub e o `id` do catalogo do efScout sao namespaces distintos.
Tratar os dois numeros como se fossem a mesma chave foi o que criou os orfaos.
Este modulo converte somente equivalencias confirmadas e para em conflito.
"""
import json
import os


ARQUIVO_OFICIAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'impeto_alias_confirmados.json')
ARQUIVO_DO_BANCO = os.path.join('dados', 'impeto_alias_por_codigo.json')


def _le(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding='utf-8') as f:
        j = json.load(f)
    return j.get('aliases', j) if isinstance(j, dict) else {}


def _normaliza(codigo, valor, origem):
    if not isinstance(valor, dict):
        raise ValueError('alias %s invalido em %s' % (codigo, origem))
    nivel = int(valor.get('nivel') or 0)
    atributos = sorted({int(x) for x in (valor.get('atributos') or [])})
    # Os impetos comuns alteram quatro atributos; os especiais novos podem
    # alterar somente um (por exemplo, Speed +6). O formato de 26 continua
    # reservado aos efeitos que cobrem a ficha inteira.
    if nivel <= 0 or len(atributos) not in (1, 4, 26):
        raise ValueError('alias %s incompleto em %s' % (codigo, origem))
    if any(x < 0 or x >= 26 for x in atributos):
        raise ValueError('alias %s tem atributo fora de 0..25' % codigo)
    nome_pt = (valor.get('nome_pt') or '').strip()
    nome_en = (valor.get('nome_en') or '').strip()
    if not nome_pt and not nome_en:
        raise ValueError('alias %s esta sem nome' % codigo)
    return {
        'codigo_externo': int(codigo),
        'nome_pt': nome_pt or nome_en,
        'nome_en': nome_en or nome_pt,
        'outros_nomes': sorted({str(x).strip() for x in
                                (valor.get('outros_nomes') or []) if str(x).strip()}),
        'nivel': nivel,
        'atributos': atributos,
        'condicional': bool(valor.get('condicional')),
        'confirmado_em': valor.get('confirmado_em'),
        'confirmado_com': valor.get('confirmado_com') or [],
        'origem_alias': origem,
    }


def carregar_aliases():
    """Oficial + banco. Conflito nunca e resolvido silenciosamente."""
    saida = {}
    for origem, caminho in (('arquivo oficial', ARQUIVO_OFICIAL),
                            ('banco', ARQUIVO_DO_BANCO)):
        for codigo, valor in _le(caminho).items():
            novo = _normaliza(codigo, valor, origem)
            chave = int(codigo)
            velho = saida.get(chave)
            if velho:
                identidade_velha = (velho['nivel'], velho['atributos'],
                                     velho['condicional'])
                identidade_nova = (novo['nivel'], novo['atributos'],
                                    novo['condicional'])
                if identidade_velha != identidade_nova:
                    raise ValueError('CONFLITO no alias do impeto %s: %s x %s'
                                     % (chave, velho['origem_alias'], origem))
                # O banco pode acrescentar nomes e comprovacoes, mas nunca
                # trocar o efeito confirmado do arquivo oficial.
                velho['outros_nomes'] = sorted(set(velho['outros_nomes']) |
                                                set(novo['outros_nomes']))
                velho['confirmado_com'] = list(velho['confirmado_com']) + [
                    x for x in novo['confirmado_com'] if x not in velho['confirmado_com']]
                continue
            saida[chave] = novo
    return saida


def como_booster(alias):
    """Formato que o unificador ja sabe somar, sem criar outra conta."""
    nivel = int(alias['nivel'])
    return {
        'id': int(alias['codigo_externo']),
        'name': '%s +%d' % (alias['nome_pt'], nivel),
        'name_en': '%s +%d' % (alias['nome_en'], nivel),
        'aliases': alias.get('outros_nomes') or [],
        'conditional': bool(alias.get('condicional')),
        'stat_modifiers': [[int(a), nivel] for a in alias['atributos']],
        '_codigo_externo': True,
        '_origem_alias': alias.get('origem_alias'),
    }
