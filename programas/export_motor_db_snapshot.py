# -*- coding: utf-8 -*-
"""Exporta os insumos canônicos para um snapshot local imutável.

Somente GET. Não calcula, não promove e não escreve no banco. A fila externa é
obrigatória e precisa comprovar 699 prontos, 127 ambíguos excluídos e 44
incompletos excluídos.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import urllib.parse
import urllib.request

from motor_db_bridge import (SNAPSHOT_VERSION, canonical_sha256,
                             validate_bonus_input, validate_optimization_input,
                             _validate_queue)


def _get(url, key, schema, resource, params):
    query = urllib.parse.urlencode(params, doseq=True, safe="(),.*")
    request = urllib.request.Request(
        "%s/rest/v1/%s?%s" % (url.rstrip("/"), resource, query),
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Accept-Profile": schema})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8") or "[]")


def _pages(url, key, schema, resource, params, page_size=1000):
    offset = 0
    while True:
        page = _get(url, key, schema, resource,
                    dict(params, limit=page_size, offset=offset))
        yield from page
        if len(page) < page_size:
            return
        offset += page_size


def _by_card_chunks(url, key, schema, resource, card_ids):
    out = []
    for start in range(0, len(card_ids), 80):
        ids = card_ids[start:start + 80]
        out.extend(_pages(url, key, schema, resource,
                          {"select": "*", "card_id": "in.(%s)" % ",".join(ids),
                           "order": "card_id.asc,funcao_codigo.asc"}))
    return out


def _model_rows(url, key, table):
    return list(_pages(url, key, "public", table, {"select": "*"}))


def _incidence(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        source = handle.read()
    match = re.search(r"const FILA=(\{.*?\});", source, re.DOTALL)
    if not match:
        raise SystemExit("fail-closed: const FILA nao encontrada em %s" % path)
    return json.loads(match.group(1))


def _models(url, key, incidence_html):
    tables = (
        "insumo_molde", "insumo_tecnico", "insumo_habilidade",
        "insumo_bloqueio", "insumo_impeto_catalogo", "insumo_multiplicador",
        "insumo_bonus_corpo", "insumo_bonus_posicao", "insumo_bonus_parametro",
    )
    result = {name: _model_rows(url, key, name) for name in tables}
    result["incidencia_comunidade"] = _incidence(incidence_html)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True,
                        help="manifesto JSON fechado da fila de 699 card_ids")
    parser.add_argument("--output", required=True)
    parser.add_argument("--fila-output", default="fila_v6.json")
    parser.add_argument("--incidence-html",
                        default="encaixe-web/arquivo/ENCAIXE-DE-ONTEM.html")
    args = parser.parse_args(argv)

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ENGINE_READ_KEY", "")
    schema = os.environ.get("MOTOR_DB_SCHEMA", "clubef_read_v2")
    if not url.startswith("https://") or not key:
        raise SystemExit("SUPABASE_URL/SUPABASE_ENGINE_READ_KEY ausentes")

    with open(args.queue, encoding="utf-8") as handle:
        queue = json.load(handle)
    card_ids = _validate_queue(queue)

    optimization = _by_card_chunks(url, key, schema, "motor_input_v2", card_ids)
    bonus = _by_card_chunks(url, key, schema, "motor_bonus_input_v2", card_ids)
    for row in optimization:
        validate_optimization_input(row)
    for row in bonus:
        validate_bonus_input(row)
    got = {str(row["card_id"]) for row in optimization}
    if got != set(card_ids):
        missing = sorted(set(card_ids) - got, key=int)
        raise SystemExit("fail-closed: %d cards da fila sem flag/input de otimizacao" %
                         len(missing))

    snapshot = {
        "snapshot_version": SNAPSHOT_VERSION,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": {"schema": schema, "optimization_view": "motor_input_v2",
                   "bonus_view": "motor_bonus_input_v2"},
        "queue": queue,
        "optimization_inputs": optimization,
        "bonus_inputs": bonus,
        "models": _models(url, key, args.incidence_html),
    }
    snapshot["snapshot_sha256"] = canonical_sha256(snapshot)

    directory = os.path.dirname(os.path.abspath(args.output))
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = args.output + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(snapshot, handle, ensure_ascii=False, sort_keys=True,
                  separators=(",", ":"), allow_nan=False)
        handle.write("\n")
    os.replace(tmp, args.output)

    fila = [{"n": i + 1, "card_id": str(row["card_id"]),
             "funcao": row["input_payload"]["funcao"]["nome"]}
            for i, row in enumerate(optimization)]
    with open(args.fila_output, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(fila, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("snapshot: %d cards · %d otimizacoes · %d bonus" %
          (len(card_ids), len(optimization), len(bonus)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

