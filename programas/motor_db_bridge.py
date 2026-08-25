# -*- coding: utf-8 -*-
"""Adaptador fail-closed entre os contratos v2 do banco e os motores legados.

Este modulo nao calcula nada. Ele valida um snapshot imutavel, preserva o
``card_id`` original e converte apenas nomes/formas de campos para as estruturas
que ``roda_lote_v6.py`` e ``motor_bonus.py`` ja consumiam.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from functools import lru_cache


SNAPSHOT_VERSION = "clubef-motor-db-snapshot-v2"
OPTIMIZATION_INPUT_VERSION = "motor-input-v3.0.0"
BONUS_INPUT_VERSION = "motor-bonus-input-v4.0.0"
EXPECTED_QUEUE_SIZE = 699
EXPECTED_AMBIGUOUS_EXCLUDED = 127
EXPECTED_INCOMPLETE_EXCLUDED = 44
HASH_RE = re.compile(r"^[0-9a-f]{64}$")

SOURCE = os.environ.get("MOTOR_INPUT_SOURCE", "legacy").strip().lower()
SNAPSHOT_PATH = os.environ.get("MOTOR_DB_SNAPSHOT", "").strip()
if SOURCE not in ("legacy", "db_snapshot"):
    raise RuntimeError("MOTOR_INPUT_SOURCE deve ser legacy ou db_snapshot")


class MotorInputError(RuntimeError):
    pass


ATTR_COLUMNS = (
    "atr_ofensividade", "atr_controle_de_bola", "atr_drible",
    "atr_posse_de_bola", "atr_passe_rasteiro", "atr_passe_alto",
    "atr_finalizacao", "atr_cabeceio", "atr_cobranca_de_falta",
    "atr_efeito", "atr_velocidade", "atr_aceleracao",
    "atr_potencia_de_chute", "atr_salto", "atr_contato_fisico",
    "atr_equilibrio", "atr_resistencia", "atr_talento_defensivo",
    "atr_desarme", "atr_agressividade", "atr_envolvimento_defensivo",
    "atr_talento_de_goleiro", "atr_encaixe", "atr_defesa_goleiro",
    "atr_reflexos", "atr_alcance",
)

DELTA_INDEX = {
    "attacking_prowess": 0, "ball_control": 1, "dribbling": 2,
    "tight_possession": 3, "low_pass": 4, "lofted_pass": 5,
    "finishing": 6, "header": 7, "place_kicking": 8, "swerve": 9,
    "speed": 10, "explosive_power": 11, "kicking_power": 12,
    "jump": 13, "physical_contact": 14, "body_control": 15,
    "stamina": 16, "defensive_awareness": 17, "tackling": 18,
    "aggression": 19, "defensive_engagement": 20, "goalkeeping": 21,
    "catching": 22, "clearing": 23, "reflexes": 24, "coverage": 25,
}


def enabled():
    return SOURCE == "db_snapshot"


def _need(ok, message):
    if not ok:
        raise MotorInputError(message)


def _original_id(value):
    value = str(value or "")
    _need(value.isdigit(), "card_id deve ser o ID original numerico, sem @variante")
    return value


def canonical_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_queue(queue):
    _need(isinstance(queue, dict), "manifesto da fila ausente")
    ids = queue.get("card_ids")
    _need(isinstance(ids, list), "fila.card_ids deve ser lista")
    ids = [_original_id(x) for x in ids]
    _need(len(ids) == EXPECTED_QUEUE_SIZE,
          "fila segura deve conter exatamente 699 cards")
    _need(len(set(ids)) == EXPECTED_QUEUE_SIZE, "fila contem card_id duplicado")
    _need(ids == sorted(ids, key=int), "fila deve estar ordenada numericamente")
    _need(queue.get("count") == EXPECTED_QUEUE_SIZE, "fila.count deve ser 699")
    _need(queue.get("ambiguous_excluded") == EXPECTED_AMBIGUOUS_EXCLUDED,
          "manifesto deve registrar 127 ambiguos excluidos")
    _need(queue.get("incomplete_excluded") == EXPECTED_INCOMPLETE_EXCLUDED,
          "manifesto deve registrar 44 incompletos excluidos")
    _need(queue.get("sha256") == canonical_sha256(ids), "hash da fila diverge")
    return ids


def _validate_common(row, expected_version, required_flag):
    _need(isinstance(row, dict), "entrada do motor deve ser objeto")
    cid = _original_id(row.get("card_id"))
    _need(row.get("input_version") == expected_version,
          "input_version inesperada para %s" % cid)
    _need(row.get("input_hash_algorithm") == "sha256", "algoritmo deve ser sha256")
    _need(bool(HASH_RE.fullmatch(str(row.get("input_hash") or ""))),
          "input_hash invalido")
    payload = row.get("input_payload")
    _need(isinstance(payload, dict), "input_payload ausente")
    card = payload.get("card") or {}
    fun = payload.get("funcao") or {}
    completude = payload.get("completude") or {}
    _need(_original_id(card.get("card_id")) == cid, "card_id interno diverge")
    _need(fun.get("codigo") == row.get("funcao_codigo"), "funcao_codigo diverge")
    _need(bool(fun.get("nome")), "nome legado da funcao ausente")
    _need(completude.get(required_flag) is True,
          "%s nao esta verdadeiro" % required_flag)
    return cid, payload


def validate_optimization_input(row):
    cid, payload = _validate_common(
        row, OPTIMIZATION_INPUT_VERSION, "motor_otimizacao_completo")
    card = payload["card"]
    attrs = [card.get(name) for name in ATTR_COLUMNS]
    _need(all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in attrs),
          "card %s nao tem os 26 atributos numericos" % cid)
    _need(isinstance(card.get("orcamento"), int) and card["orcamento"] >= 0,
          "orcamento invalido")
    slots = payload.get("impetos")
    _need(isinstance(slots, list) and len(slots) == 2,
          "entrada exige exatamente dois slots de impeto")
    _need([x.get("slot") for x in slots] == [1, 2], "slots devem ser 1,2")
    for slot in slots:
        _need(slot.get("validacao") == "validado", "slot nao validado")
        _need(not slot.get("divergencias"), "slot com divergencia")
        state = slot.get("estado")
        _need(state in ("preenchido", "vaga_explicita", "sem_impeto_sem_vaga"),
              "estado de impeto nao promovivel: %r" % state)
        if state == "preenchido":
            _need(isinstance(slot.get("impeto_id"), int), "impeto sem ID")
            deltas = slot.get("deltas")
            _need(isinstance(deltas, dict) and set(deltas) == set(DELTA_INDEX),
                  "impeto sem vetor canonico de 26 deltas")
            _need(all(isinstance(x, int) for x in deltas.values()),
                  "delta de impeto nao inteiro")
            if slot.get("condicional"):
                _need(isinstance(slot.get("condicoes"), dict) and slot["condicoes"],
                      "impeto condicional sem condicoes")
        elif state == "vaga_explicita":
            _need((slot.get("booster_type"), slot.get("booster_sub_type"),
                   slot.get("up_point")) == (4, 4, 1),
                  "vaga explicita nao obedece 4/4/1")
            _need(slot.get("impeto_id") is None, "vaga nao pode ter impeto_id")
        else:
            _need(slot.get("impeto_id") is None, "slot vazio nao pode ter impeto_id")
    skills = payload.get("habilidades")
    _need(isinstance(skills, list), "habilidades ausentes")
    allowed = {"native_common", "native_special", "remaining_pool", "ai_playstyle"}
    for skill in skills:
        _need(skill.get("tipo") in allowed, "tipo de habilidade desconhecido")
        _need(skill.get("validacao") == "validado", "habilidade nao validada")
        _need(bool(skill.get("nome")), "habilidade sem nome")


def validate_bonus_input(row):
    cid, payload = _validate_common(row, BONUS_INPUT_VERSION, "motor_bonus_completo")
    card = payload["card"]
    _need(isinstance(card.get("corpo"), list) and len(card["corpo"]) == 12,
          "card %s sem 12 medidas de corpo" % cid)
    _need(isinstance(card.get("pe_ruim"), list) and len(card["pe_ruim"]) == 2,
          "card %s sem pe_ruim [uso,precisao]" % cid)
    _need(card.get("visto_na_casca") is True, "coleta de estilo IA desconhecida")
    _need(isinstance(card.get("com"), list), "estilos IA invalidos")
    _need(bool(card.get("modelo")), "estilo de jogo ausente")


@lru_cache(maxsize=1)
def snapshot():
    _need(enabled(), "snapshot pedido em modo legacy")
    _need(bool(SNAPSHOT_PATH), "MOTOR_DB_SNAPSHOT nao definido")
    try:
        with open(SNAPSHOT_PATH, encoding="utf-8") as handle:
            value = json.load(handle)
    except Exception as exc:
        raise MotorInputError("nao foi possivel ler snapshot: %s" % exc)
    _need(value.get("snapshot_version") == SNAPSHOT_VERSION,
          "snapshot_version inesperada")
    declared_snapshot_hash = value.pop("snapshot_sha256", None)
    _need(bool(HASH_RE.fullmatch(str(declared_snapshot_hash or ""))),
          "snapshot_sha256 invalido")
    _need(declared_snapshot_hash == canonical_sha256(value),
          "snapshot_sha256 diverge")
    value["snapshot_sha256"] = declared_snapshot_hash
    ids = set(_validate_queue(value.get("queue")))
    opt = value.get("optimization_inputs")
    bonus = value.get("bonus_inputs")
    _need(isinstance(opt, list) and opt, "snapshot sem entradas de otimizacao")
    _need(isinstance(bonus, list), "snapshot sem entradas de bonus")
    seen = set()
    opt_cards = set()
    for row in opt:
        validate_optimization_input(row)
        key = (str(row["card_id"]), row["funcao_codigo"])
        _need(key not in seen, "entrada de otimizacao duplicada")
        _need(key[0] in ids, "entrada fora da fila segura")
        seen.add(key); opt_cards.add(key[0])
    _need(opt_cards == ids, "nem todos os 699 cards possuem entrada de otimizacao")
    seen = set()
    for row in bonus:
        validate_bonus_input(row)
        key = (str(row["card_id"]), row["funcao_codigo"])
        _need(key not in seen, "entrada de bonus duplicada")
        _need(key[0] in ids, "entrada de bonus fora da fila segura")
        seen.add(key)
    return value


def model_rows(name):
    rows = (snapshot().get("models") or {}).get(name)
    _need(isinstance(rows, (list, dict)), "snapshot sem modelo %s" % name)
    return rows


def tabm_model():
    return {str(x["ponto"]): float(x["multiplicador"])
            for x in model_rows("insumo_multiplicador")}


def technicians_model():
    return {str(x["id"]): {"id": x["id"], "name": x["nome"],
                            "hasBoost": bool(x["tem_boost"]),
                            "skills": dict(x.get("proficiencias") or {}),
                            "boosts": list(x.get("boosts") or [])}
            for x in model_rows("insumo_tecnico")}


def skills_model():
    return {x["chave"]: {"arquivo": x["nome_pt"], "tipo": x["tipo"],
                           "efeito": dict(x.get("efeito") or {})}
            for x in model_rows("insumo_habilidade")}


def impulses_model():
    return [[x["nome"], 1 if x.get("condicional") else 0,
             list(x.get("efeito") or [])]
            for x in model_rows("insumo_impeto_catalogo")]


def mold_model():
    return [{"funcao": x["funcao"], "attr": x["attr"],
             "peso": x["peso"], "alvo": x["alvo"]}
            for x in model_rows("insumo_molde")]


def blocking_model():
    rows = model_rows("insumo_bloqueio")
    positions = {}
    blocks = {}
    for row in rows:
        positions.setdefault(row["grupo"], set()).add(row["funcao"])
        blocks.setdefault(row["habilidade"], set()).add(row["grupo"])
    return {"_posicoes": {k: sorted(v) for k, v in positions.items()},
            "bloqueios": {k: sorted(v) for k, v in blocks.items()}}


def incidence_model():
    return dict(model_rows("incidencia_comunidade"))


def bonus_model():
    rows = model_rows("insumo_bonus_corpo")
    order = ["Altura", "Coxa", "Panturrilha", "Cintura", "Peito",
             "Tam. braco", "Tam. pescoco", "Compr. perna", "Compr. braco",
             "Compr. pescoco", "Larg. ombro", "Alt. ombro"]
    # O banco usa acentos; a normalizacao abaixo casa sem alterar valores.
    aliases = {"Tam. braço": "Tam. braco", "Tam. pescoço": "Tam. pescoco",
               "Compr. braço": "Compr. braco", "Compr. pescoço": "Compr. pescoco"}
    direction, cuts, weights = {}, {}, {}
    for row in rows:
        measure = aliases.get(row["medida"], row["medida"])
        direction.setdefault(row["funcao"], {})[measure] = row["direcao"]
        cuts.setdefault(row["funcao"], {})[measure] = [
            row["corte1"], row["corte2"], row["corte3"], row["corte4"]]
        weights[measure] = row["peso"]
    positions = {"posicoes_da_funcao": {}, "onde_o_estilo_liga": {}}
    for row in model_rows("insumo_bonus_posicao"):
        target = ("posicoes_da_funcao" if row["tipo"] == "funcao"
                  else "onde_o_estilo_liga")
        positions[target][row["nome"]] = list(row.get("posicoes") or [])
    parameters = {x["chave"]: x["valor"]
                  for x in model_rows("insumo_bonus_parametro")}
    weak = {"teto": parameters.pop("pe_ruim_teto"),
            "frequencia": [parameters.pop("pe_ruim_frequencia_%d" % i)
                            for i in range(4)],
            "precisao": [parameters.pop("pe_ruim_precisao_%d" % i)
                          for i in range(4)]}
    return {"corpo": {"ordem": order,
                       "indice_no_vetor": {name: i for i, name in enumerate(order)},
                       "direcao": direction, "cortes_por_funcao": cuts,
                       "pesos": weights, "cortes": {}, "cortes_altura_goleiro": [],
                       "tipo_de_corpo": {}, "excecoes": {}, "goleiro": {},
                       "piso_teto": {}, "bloco_porte": [], "bloco_proporcao": [],
                       "bloco_ombros": []},
            "posicao": positions, "parametros": parameters, "pe_ruim": weak}


def _skills(payload, kind):
    return [x["nome"] for x in payload.get("habilidades", []) if x.get("tipo") == kind]


def to_legacy_card(row):
    validate_optimization_input(row)
    payload = row["input_payload"]
    card = payload["card"]
    slots = [0, 0]
    delta = [0] * 26
    names = []
    conditional = []
    for slot in payload["impetos"]:
        index = slot["slot"] - 1
        if slot["estado"] == "vaga_explicita":
            slots[index] = 1
        elif slot["estado"] == "preenchido":
            for name, value in slot["deltas"].items():
                delta[DELTA_INDEX[name]] += value
            names.append(slot.get("nome") or str(slot["impeto_id"]))
            conditional.append(bool(slot.get("condicional")))
    return {
        "id": str(row["card_id"]), "nome": card.get("nome"),
        "base": [card[name] for name in ATTR_COLUMNS],
        "orc": card["orcamento"], "sl": slots,
        "nm": [[i, value] for i, value in enumerate(delta) if value],
        "impeto_nomes": names, "impeto_condicional": conditional,
        "fab": _skills(payload, "native_common"),
        "raras": _skills(payload, "native_special"),
        "falta": _skills(payload, "remaining_pool"),
        "com": _skills(payload, "ai_playstyle"),
        "visto_na_casca": ((card.get("input_presence") or {}).get("ai_playstyles")
                            == "known"),
        "corpo": [card.get(x) for x in (
            "corpo_altura", "corpo_coxa", "corpo_panturrilha", "corpo_cintura",
            "corpo_peito", "corpo_tamanho_braco", "corpo_tamanho_pescoco",
            "corpo_comprimento_perna", "corpo_comprimento_braco",
            "corpo_comprimento_pescoco", "corpo_largura_ombro",
            "corpo_altura_ombro")],
        "pe_ruim": [card.get("pe_ruim_uso"), card.get("pe_ruim_precisao")],
        "modelo": card.get("estilo_jogo"), "np": card.get("posicao_nativa"),
        "pos": card.get("posicao_nativa"),
        "sec": list(card.get("posicoes_secundarias") or []),
        "ovr": card.get("ovr"), "tier": card.get("tier"),
    }


@lru_cache(maxsize=1)
def _optimization_index():
    return {(str(x["card_id"]), x["input_payload"]["funcao"]["nome"]): x
            for x in snapshot()["optimization_inputs"]}


@lru_cache(maxsize=1)
def _bonus_index():
    return {(str(x["card_id"]), x["input_payload"]["funcao"]["nome"]): x
            for x in snapshot()["bonus_inputs"]}


def optimization_input(card_id, legacy_function):
    key = (_original_id(card_id), legacy_function)
    _need(key in _optimization_index(), "entrada de otimizacao nao promovida: %s|%s" % key)
    return _optimization_index()[key]


def bonus_input(card_id, legacy_function):
    key = (_original_id(card_id), legacy_function)
    _need(key in _bonus_index(), "entrada de bonus nao promovida: %s|%s" % key)
    return _bonus_index()[key]


def optimization_metadata(card_id, legacy_function):
    row = optimization_input(card_id, legacy_function)
    return {"funcao_codigo": row["funcao_codigo"],
            "input_version": row["input_version"],
            "input_hash_algorithm": row["input_hash_algorithm"],
            "input_hash": row["input_hash"]}


def bonus_metadata(card_id, legacy_function):
    row = bonus_input(card_id, legacy_function)
    return {"funcao_codigo": row["funcao_codigo"],
            "input_version": row["input_version"],
            "input_hash_algorithm": row["input_hash_algorithm"],
            "input_hash": row["input_hash"]}


def cards():
    out = {}
    for row in snapshot()["optimization_inputs"]:
        cid = str(row["card_id"])
        card = to_legacy_card(row)
        if cid in out:
            for key in ("base", "orc", "sl", "nm", "fab", "raras", "falta"):
                _need(out[cid][key] == card[key],
                      "card diverge entre funcoes no campo %s" % key)
        else:
            out[cid] = card
    return out


def bonus_cards():
    out = {}
    for row in snapshot()["bonus_inputs"]:
        card = row["input_payload"]["card"]
        cid = str(row["card_id"])
        converted = {"id": cid, "corpo": list(card["corpo"]),
                     "pe_ruim": list(card["pe_ruim"]), "modelo": card["modelo"],
                     "com": list(card["com"]), "visto_na_casca": True}
        _need(cid not in out or out[cid] == converted,
              "entrada de bonus diverge entre funcoes")
        out[cid] = converted
    return out


def queue_entries():
    return [{"n": i + 1, "card_id": cid,
             "funcao": row["input_payload"]["funcao"]["nome"]}
            for i, (cid, row) in enumerate(sorted(
                ((str(x["card_id"]), x) for x in snapshot()["optimization_inputs"]),
                key=lambda item: (int(item[0]), item[1]["funcao_codigo"])))]


def validate_runtime_queue(rows):
    expected = {(x["card_id"], x["funcao"]) for x in queue_entries()}
    got = {(str(x.get("card_id") or ""), x.get("funcao")) for x in rows}
    _need(got == expected, "fila_v6.json diverge do snapshot canonico")
