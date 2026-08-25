# -*- coding: utf-8 -*-
"""Writer opt-in para tabelas de resultado v2; nunca altera a tabela-base."""

from __future__ import annotations

import datetime
import json
import os
import urllib.error
import urllib.request
import uuid


class MotorOutputError(RuntimeError):
    pass


ENABLED = os.environ.get("MOTOR_OUTPUT_WRITE_ENABLED", "0") == "1"
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_ENGINE_WRITE_KEY", "")
SCHEMA = os.environ.get("MOTOR_RESULT_SCHEMA", "clubef_read_v2")
EXECUTION_ID = os.environ.get("MOTOR_EXECUTION_ID") or str(uuid.uuid4())


def configured():
    return ENABLED


def _need(ok, message):
    if not ok:
        raise MotorOutputError(message)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _post(table, row):
    _need(ENABLED, "writer desligado; defina MOTOR_OUTPUT_WRITE_ENABLED=1")
    _need(URL.startswith("https://") and KEY, "credencial de escrita ausente")
    request = urllib.request.Request(
        "%s/rest/v1/%s" % (URL, table), method="POST",
        data=json.dumps(row, ensure_ascii=False, allow_nan=False).encode("utf-8"),
        headers={"apikey": KEY, "Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json", "Content-Profile": SCHEMA,
                 "Accept-Profile": SCHEMA, "Prefer": "return=representation"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            rows = json.loads(response.read().decode("utf-8") or "[]")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise MotorOutputError("POST %s falhou: HTTP %s %s" %
                               (table, exc.code, detail))
    _need(isinstance(rows, list) and len(rows) == 1 and rows[0].get("result_id"),
          "banco nao devolveu result_id para %s" % table)
    return rows[0]


def optimization_row(result):
    from motor_db_bridge import optimization_metadata
    _need(not result.get("ERRO"), "resultado com ERRO nao pode ser escrito")
    meta = optimization_metadata(result.get("card_id"), result.get("funcao"))
    return {"card_id": str(result["card_id"]),
            "funcao_codigo": meta["funcao_codigo"],
            "motor_name": "motor_otimizacao_v6", "motor_version": 6,
            "input_version": meta["input_version"],
            "input_hash_algorithm": meta["input_hash_algorithm"],
            "input_hash": meta["input_hash"], "execution_id": EXECUTION_ID,
            "executed_at": _now(), "status": "pendente_validacao",
            "result_payload": result, "error_payload": None,
            "is_current": False, "approved_at": None,
            "provenance": {"origin": "external_user_environment",
                           "writer": "motor_db_results.py"}}


def write_optimization(result):
    return _post("motor_optimization_results_v2", optimization_row(result))


def bonus_row(result, optimization_result_id):
    from motor_db_bridge import bonus_metadata
    _need(isinstance(optimization_result_id, int),
          "bonus exige optimization_result_id persistido")
    meta = bonus_metadata(result.get("card_id"), result.get("funcao"))
    return {"card_id": str(result["card_id"]),
            "funcao_codigo": meta["funcao_codigo"],
            "optimization_result_id": optimization_result_id,
            "motor_name": "motor_bonus_v1", "motor_version": 1,
            "input_version": meta["input_version"],
            "input_hash_algorithm": meta["input_hash_algorithm"],
            "input_hash": meta["input_hash"], "execution_id": EXECUTION_ID,
            "executed_at": _now(), "status": "pendente_validacao",
            "result_payload": result, "error_payload": None,
            "is_current": False, "approved_at": None,
            "provenance": {"origin": "external_user_environment",
                           "writer": "motor_db_results.py"}}


def write_bonus(result, optimization_result_id):
    return _post("motor_bonus_results_v2", bonus_row(result, optimization_result_id))

