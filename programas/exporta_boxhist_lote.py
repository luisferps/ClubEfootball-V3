# -*- coding: utf-8 -*-
"""Extrai lotes do BOXHIST embutido na prévia para a migração única."""
import io, json, pathlib, re, sys

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

inicio = int(sys.argv[1]) if len(sys.argv) > 1 else 0
quantidade = int(sys.argv[2]) if len(sys.argv) > 2 else 100
pagina = pathlib.Path(__file__).resolve().parents[2] / 'PREVIA-ENCAIXE-MODAL-GULLIT-19-08.html'
texto = pagina.read_text(encoding='utf-8')
achou = re.search(r'const BOXHIST=(\{.*?\});', texto, re.S)
if not achou:
    raise SystemExit('BOXHIST não encontrado')
historico = json.loads(achou.group(1))
itens = [{'nome': nome, 'visto': dados.get('visto'), 'ids': dados.get('ids') or []}
         for nome, dados in historico.items()]
print(json.dumps({'total': len(itens), 'itens': itens[inicio:inicio + quantidade]},
                 ensure_ascii=False))
