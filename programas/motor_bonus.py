# -*- coding: utf-8 -*-
"""
O MOTOR DOS BONUS — 15/08/2026

ORDEM DO LUIS, 15/08:
    "A gente ja tem um motor pra organizar os atributos. Por que voce nao faz
     tipo uma especie de motor tambem pra organizar o restante dos bonus?"
    "O encaixe que eu tenho na minha maquina hoje puxa da maquina. Quando ele
     for pra internet, vai puxar do banco de dados. E assim que tem que ser —
     hoje os atributos ele puxa da maquina tambem."

ENTAO E EXATAMENTE COMO O MOTOR DOS ATRIBUTOS:
    le da PASTA  ->  calcula  ->  grava saida_v6/bonus.jsonl  (a maquina)
                              ->  grava a tabela `bonus`      (o banco)

    O gera_encaixe.py le o ARQUIVO e cola os numeros dentro do HTML.
    Quando o encaixe for para a internet, ele passa a ler a tabela.
    Sem internet o sistema inteiro continua rodando.

OS QUATRO BONUS
    corpo ......... de -1,5 a +1,5   as 12 medidas contra o molde da funcao
    pe ruim ....... de  0  a +1,0    frequencia x precisao
    estilo ativo .. +1               se o estilo do card liga numa posicao da funcao
    estilo da IA .. de  0  a +1,0    quantos estilos de IA o card tem, sobre o teto

DE ONDE PUXA CADA COISA (⛔ 17/08: um lugar so — a base, que vem do banco)
    dados/insumos_bonus.json    o molde do fisico, as posicoes, as constantes
    dados/base_unica.json       ⛔ 17/08: A FONTE UNICA. corpo, pe ruim, estilo
                                de jogo da IA e o `visto_na_casca`. Ela vem do
                                BANCO, pelo BAIXAR-BASE.
    saida_v6/linhas.jsonl       os pares card x funcao que o motor rodou

O QUE GRAVA
    saida_v6/bonus.jsonl        <- o gera_encaixe.py le daqui
    NAO-SEI.txt                 <- a lista de tudo que nao deu para puxar
    tabela bonus                <- so se o config.txt existir
    insumo_bonus_corpo · insumo_bonus_posicao · insumo_bonus_parametro

A CHAVE sai do config.txt na hora de rodar. Nunca e gravada nem impressa aqui.
Sem config.txt ele roda igual e grava so na maquina.
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
import json, os, sys, io, re, time, urllib.request, urllib.error, urllib.parse
import motor_db_bridge as _db

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# ⛔ 19/08 — O QUE APARECE NA TELA FICA GRAVADO NUM ARQUIVO TAMBEM.
#    Ordem do Luis, 19/08: "como e que o Python fecha a janela antes de eu
#    poder copiar?". A janela preta e o unico lugar onde o resultado existia:
#    fechou, perdeu. Agora tudo que ele escreve na tela vai junto para
#    ULTIMA-RODADA-BONUS.txt, na pasta da casa. Abre no bloco de notas e
#    copia com calma, quantas vezes quiser.
#    A tela continua igual — isto nao esconde nada, so guarda uma copia.
# ---------------------------------------------------------------------------
LOG_DA_RODADA = 'ULTIMA-RODADA-BONUS.txt'


class _DoisDestinos(object):
    """Escreve na tela E no arquivo. Se o arquivo falhar, a tela continua."""

    def __init__(self, tela, caminho):
        self.tela = tela
        try:
            self.arq = open(caminho, 'w', encoding='utf-8', errors='replace')
        except Exception:
            self.arq = None

    def write(self, texto):
        self.tela.write(texto)
        if self.arq is not None:
            try:
                # o \r e da barrinha de progresso: no arquivo ele vira linha
                self.arq.write(texto.replace('\r', '\n'))
            except Exception:
                pass
        return len(texto)

    def flush(self):
        try:
            self.tela.flush()
        except Exception:
            pass
        if self.arq is not None:
            try:
                self.arq.flush()
            except Exception:
                pass

    def isatty(self):
        try:
            return self.tela.isatty()
        except Exception:
            return False


try:
    sys.stdout = _DoisDestinos(sys.stdout, LOG_DA_RODADA)
except Exception:
    pass

MOTOR_BONUS = 1          # a versao deste motor. Sobe quando a conta mudar.
LOTE = 200
PAUSA = 0.05
INSUMOS = os.path.join('dados', 'insumos_bonus.json')
BASE = os.path.join('dados', 'base_unica.json')
CARDS = os.path.join('dados', 'cards.json')
# ============================================================================
#  ⛔ 17/08 — AS QUATRO FONTES DE FORA SAIRAM. AGORA E SO A BASE.
# ============================================================================
#  Ordem do Luis, 17/08:
#     "Vamos continuar a transformacao do sistema, porque nao e pra pegar esses
#      dados em dois lugares. A gente vai pegar so no banco de dados."
#
#  O QUE SAIU, E O QUE FOI MEDIDO ANTES DE TIRAR (17/08, carta por carta):
#
#   encaixe/corpo_efhub.js   congelado em 10/08.
#       10.056 cards · a base tem 2.783 · DIVERGEM ZERO nas 2.623 que os dois
#       conhecem. Nao estava errado: o fisico de uma carta nao muda depois do
#       lancamento. Estava INCOMPLETO — nao conhece 160 cartas da base.
#       As 2 cartas da base sem corpo, ele tambem nao tem. Perda: zero.
#
#   pe_ruim.json             2.649 cards · a base tem 2.779 · DIVERGEM ZERO.
#       A base tem 130 A MAIS. Perda: zero. Ganho: 130 cartas passam a ter
#       bonus de pe ruim em vez de "nao sei".
#
#   efootbase_coletado.json  entrava so como reserva do corpo, e quando
#       discordava do arquivo de 10/08 o arquivo ganhava e a divergencia era
#       apenas CONTADA (6 cartas, ninguem desempatou). O corpo dele ja subiu
#       para o banco pelo caminho normal.
#
#   as CASCAS (o HTML gerado)  ⛔ ESTA E A PIOR: o motor lia o estilo de jogo
#       da IA de dentro do arquivo de 38 MB que ESTE SISTEMA gera. O plano da
#       transformacao proibe em letra grande: "nao usar a propria saida do
#       sistema como fonte — a tela passou a provar o dado dela mesma".
#       Agora o `com` e o `visto_na_casca` descem do banco (17/08, baixar_base).
#
#  ⛔ O QUE NAO PODE SE PERDER NA TROCA: a diferenca entre "conferi e a carta
#     NAO tem estilo de IA" (zero legitimo) e "nunca perguntei" (nao sei). Quem
#     guarda isso e o `visto_na_casca`. Se ele nao estiver na base, este
#     programa PARA — melhor parar que transformar 2.284 "nao sei" em zero.
PERUIM_LEGADO = 'pe_ruim.json'          # so para o aviso de que virou legado
CORPO_JS_LEGADO = os.path.join('encaixe', 'corpo_efhub.js')
LINHAS = os.path.join('saida_v6', 'linhas.jsonl')
SAIDA = os.path.join('saida_v6', 'bonus.jsonl')
NAOSEI = 'NAO-SEI.txt'


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


def le(p, padrao=None):
    if _db.enabled():
        if p == INSUMOS:
            return _db.bonus_model()
        if p == BASE:
            return list(_db.bonus_cards().values())
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return padrao


# ================================================================ A CONTA
# A MESMA conta que roda no HTML hoje, traduzida para Python. Nenhuma regra
# nova: o que muda e de onde o insumo vem e onde o resultado fica.

def nota_da_medida(valor, cortes):
    """-2 a +2, pelos quatro cortes."""
    if valor <= cortes[0]:
        return -2
    if valor <= cortes[1]:
        return -1
    if valor <= cortes[2]:
        return 0
    if valor <= cortes[3]:
        return 1
    return 2


class Molde(object):
    def __init__(self, ins):
        c = ins['corpo']
        self.ordem = c['ordem']
        self.cortes = c['cortes']
        self.cortes_gk = c['cortes_altura_goleiro']
        self.direcao = c['direcao']
        self.tipo = c['tipo_de_corpo']
        self.excecoes = c['excecoes']
        self.goleiro = c['goleiro']
        self.piso_teto = c['piso_teto']
        self.idx = c['indice_no_vetor']
        self.porte = c['bloco_porte']
        self.proporcao = c['bloco_proporcao']
        self.ombros = c['bloco_ombros']
        self.cortes_por_funcao = c.get('cortes_por_funcao') or {}
        self.pesos = c.get('pesos') or {}
        self.peso_altura = c.get('peso_altura', 5)
        self.peso_demais = c.get('peso_demais', 1)

    def peso(self, medida):
        if medida in self.pesos:
            return self.pesos[medida]
        return self.peso_altura if medida == 'Altura' else self.peso_demais

    def dir(self, medida, funcao):
        d = self.direcao.get(funcao)
        if d and medida in d:
            return d[medida]
        e = self.excecoes.get(funcao + '|' + medida)
        if e is not None:
            return e
        t = self.tipo.get(funcao)
        if not t:
            return 0
        if t[0] == 'GK':
            return self.goleiro.get(medida, 0)
        if medida in self.porte:
            return 1 if t[0] == 'G' else -1
        if medida in self.proporcao:
            return 1 if t[1] == 'L' else -1
        return self.ombros.get(medida, 0)

    def corte(self, medida, funcao):
        if funcao in self.cortes_por_funcao:
            return self.cortes_por_funcao[funcao][medida]
        t = self.tipo.get(funcao)
        if t and t[0] == 'GK' and medida == 'Altura':
            return self.cortes_gk
        return self.cortes[medida]

    def alvo(self, medida, funcao):
        d = self.dir(medida, funcao)
        if not d:
            return '—'
        c = self.corte(medida, funcao)
        return ('≥' + str(c[3] + 1)) if d > 0 else ('≤' + str(c[0]))

    def teto(self, funcao):
        t = 0
        for m in self.ordem:
            if self.dir(m, funcao):
                t += self.peso(m) * 2
        return t or 1

    def conhece(self, funcao):
        return funcao in self.direcao or funcao in self.tipo


def bonus_do_corpo(molde, corpo, funcao, corpo_max):
    """(bonus, soma, pct, as 12 linhas) — ou None se faltar medida."""
    if not molde.conhece(funcao):
        return None
    if not isinstance(corpo, (list, tuple)) or len(corpo) < 12:
        return None
    soma = 0
    linhas = []
    for m in molde.ordem:
        v = corpo[molde.idx[m]]
        if not isinstance(v, (int, float)):
            return None
        d = molde.dir(m, funcao)
        pe = molde.peso(m)
        n = nota_da_medida(v, molde.corte(m, funcao))
        pts = n * d * pe
        soma += pts
        linhas.append({'medida': m, 'valor': v, 'alvo': molde.alvo(m, funcao),
                       'nota': n, 'peso': pe if d else 0, 'direcao': d,
                       'pontos': pts})
    te = molde.teto(funcao)
    pct = max(-100.0, min(100.0, soma / float(te) * 100.0))
    return round(pct / 100.0 * corpo_max, 4), soma, round(pct, 2), linhas


def bonus_do_pe_ruim(ins, uso, prec):
    f = ins['pe_ruim']['frequencia']
    q = ins['pe_ruim']['precisao']
    teto = ins['pe_ruim']['teto']
    if uso is None or prec is None:
        return 0.0
    try:
        u, p = int(uso), int(prec)
    except Exception:
        return 0.0
    if not (0 <= u < len(f)) or not (0 <= p < len(q)):
        return 0.0
    return round(f[u] * q[p] * teto, 4)


def bonus_do_estilo(ins, estilo, funcao):
    pf = (ins['posicao']['posicoes_da_funcao'] or {}).get(funcao)
    pe = (ins['posicao']['onde_o_estilo_liga'] or {}).get(estilo)
    if not pf or not pe:
        return 0.0
    for p in pf:
        if p in pe:
            return float(ins['parametros']['estilo_ativo'])
    return 0.0


def bonus_do_estilo_ia(ins, lista):
    if not lista:
        return 0.0
    pt = ins['parametros']['estilo_ia_ponto']
    teto = ins['parametros']['estilo_ia_teto'] or 1
    return round(pt * min(len(lista), teto) / float(teto), 4)


# ================================================================== RODA
print('=' * 70)
print('  O MOTOR DOS BONUS  —  corpo · pe ruim · estilo ativo · estilo da IA')
print('=' * 70)

ins = le(INSUMOS)
if not ins:
    print('')
    print('Falta o %s — e ele quem guarda o molde do fisico,' % INSUMOS)
    print('as posicoes e as constantes.')
    pausa(); sys.exit(1)
molde = Molde(ins)
CORPO_MAX = ins['parametros']['bonus_corpo_max']

# ---------------------------------------------------- 1) O QUE CADA CARD TEM
print('')
print('[1/4] lendo a pasta')

# ============================================================================
#  A BASE UNICA — a fonte, e a unica. Ela vem do banco pelo BAIXAR-BASE.
# ============================================================================
B = le(BASE, {})
if isinstance(B, dict):
    B = B.get('cards') or B.get('dados') or []
BASEC = {}
for c in (B or []):
    cid = str(c.get('id') or '').split('@')[0]
    if cid and cid not in BASEC:
        BASEC[cid] = c
if not BASEC:
    print('')
    print('  PAREI: a base unica veio vazia. Rode o BAIXAR-BASE.bat.')
    sys.exit(1)
print('   base unica (vem do banco) .......... %d cards' % len(BASEC))

CORPO, PE, IA, VISTO_IA = {}, {}, {}, set()
_sem_corpo = _sem_pe = 0
for cid, c in BASEC.items():
    v = c.get('corpo')
    if isinstance(v, list) and len(v) >= 12:
        CORPO[cid] = v
    else:
        _sem_corpo += 1
    p = c.get('pe_ruim')
    if isinstance(p, (list, tuple)) and len(p) >= 2:
        PE[cid] = list(p)
    else:
        _sem_pe += 1
    if c.get('visto_na_casca'):
        VISTO_IA.add(cid)
    x = c.get('com')
    if isinstance(x, list) and x:
        IA[cid] = x

print('   corpo .............................. %d cards' % len(CORPO))
print('   pe ruim ............................ %d cards' % len(PE))
print('   estilo de jogo da IA ............... %d com valor · %d conferidos'
      % (len(IA), len(VISTO_IA)))

# ⛔ A TRAVA DO "CONFERIDO E NAO TEM". Sem o `visto_na_casca` na base, TODO card
#    sem estilo de IA viraria "nao sei" — ou, pior, zero. Sao coisas opostas e o
#    Luis foi expresso: "nao ter nao significa que voce nao achou".
#    Se ele nao desceu do banco, PARO. Melhor parar que pontuar no escuro.
if not VISTO_IA:
    print('')
    print('  PAREI: a base nao tem o `visto_na_casca`.')
    print('  Sem ele eu nao sei separar "conferi e a carta NAO tem estilo de IA"')
    print('  de "nunca perguntei" — e os dois viram bonus diferente.')
    print('')
    print('  Ele existe no banco (2.785 cartas). Para ele descer:')
    print('     BAIXAR-BASE.bat   (com o baixar_base.py de 17/08 ou mais novo)')
    sys.exit(1)

# ⚠️ os dois arquivos que ERAM fonte ate 17/08 continuam na pasta. Aviso para
#    ninguem achar que eles ainda mandam em alguma coisa.
for _velho, _oq in ((CORPO_JS_LEGADO, 'o corpo'), (PERUIM_LEGADO, 'o pe ruim')):
    if os.path.exists(_velho):
        print('   (legado, NAO e mais lido: %s — era %s)' % (_velho, _oq))

# os pares card x funcao que o motor dos atributos rodou
pares = []
OPTIMIZATION_RESULT_IDS = {}
vistos = set()
try:
    with open(LINHAS, encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                d = json.loads(linha)
            except Exception:
                continue
            cid = str(d.get('card_id') or '').split('@')[0]
            fun = d.get('funcao')
            if not cid or not fun:
                continue
            k = (cid, fun)
            if k in vistos:
                continue
            vistos.add(k)
            pares.append((cid, fun, d.get('estilo')))
            if d.get('optimization_result_id') is not None:
                OPTIMIZATION_RESULT_IDS[k] = int(d['optimization_result_id'])
except Exception as e:
    print('   NAO ACHEI o %s (%s)' % (LINHAS, e))
print('   pares card x funcao ................ %d' % len(pares))

if not pares:
    print('')
    print('Sem o saida_v6/linhas.jsonl nao ha o que calcular.')
    pausa(); sys.exit(1)

# --------------------------------------------------------- 2) A CONTA
print('')
print('[2/4] calculando')
saida = []
sem_corpo = sem_pe = sem_ia = sem_est = 0
soma = {'corpo': 0.0, 'pe': 0.0, 'est': 0.0, 'ia': 0.0}
conta = {'corpo': 0, 'pe': 0, 'est': 0, 'ia': 0}
for cid, fun, est_linha in pares:
    c = BASEC.get(cid, {})
    r = bonus_do_corpo(molde, CORPO.get(cid), fun, CORPO_MAX)
    if r is None:
        sem_corpo += 1
        b_corpo, c_soma, c_pct, detalhe = None, None, None, None
    else:
        b_corpo, c_soma, c_pct, detalhe = r
        soma['corpo'] += b_corpo; conta['corpo'] += 1

    pr = PE.get(cid)
    if isinstance(pr, (list, tuple)) and len(pr) >= 2:
        b_pe = bonus_do_pe_ruim(ins, pr[0], pr[1])   # inclui o 0 legitimo (pe [0,0])
    else:
        sem_pe += 1
        b_pe = None          # a base nao tem pe ruim desta carta: NAO SEI
    if b_pe:
        soma['pe'] += b_pe; conta['pe'] += 1

    estilo = c.get('modelo') or est_linha
    if not estilo:
        sem_est += 1
    b_est = bonus_do_estilo(ins, estilo, fun)
    if b_est:
        soma['est'] += b_est; conta['est'] += 1

    lst = IA.get(cid)
    if lst:
        b_ia = bonus_do_estilo_ia(ins, lst)
    elif cid in VISTO_IA:
        b_ia = 0.0           # conferido na fonte: o card NAO TEM. Zero de verdade.
    else:
        sem_ia += 1
        b_ia = None          # nunca foi coletado: NAO SEI
    if b_ia:
        soma['ia'] += b_ia; conta['ia'] += 1

    _meta = _db.bonus_metadata(cid, fun) if _db.enabled() else None
    saida.append({
        'card_id': cid, 'funcao': fun,
        'b_corpo': b_corpo, 'b_pe_ruim': b_pe, 'b_estilo': b_est, 'b_ia': b_ia,
        'b_total': round(sum(x for x in (b_corpo, b_pe, b_est, b_ia)
                            if isinstance(x, (int, float))), 4),
        # ⛔ 15/08 ORDEM DO LUIS: "se ele nao sabe, ele vai querer colocar zero,
        #    e um numero inventado". Entao o que faltou fica ESCRITO, com nome.
        'faltou': [n for n, v in (('corpo', b_corpo), ('pe ruim', b_pe),
                                  ('estilo da IA', b_ia))
                   if not isinstance(v, (int, float))],
        'corpo_soma': c_soma, 'corpo_pct': c_pct,
        'detalhe': detalhe, 'motor_bonus': MOTOR_BONUS,
        'input_version': _meta.get('input_version') if _meta else None,
        'input_hash': _meta.get('input_hash') if _meta else None,
        'input_hash_algorithm': _meta.get('input_hash_algorithm') if _meta else None,
        'funcao_codigo': _meta.get('funcao_codigo') if _meta else None})
print('   %d pares calculados' % len(saida))

# --------------------------------------- 2b) A LISTA DOS "NAO SEI"
# ORDEM DO LUIS, 15/08:
#   "quando nao souber o numero, tem que avisar que nao foi possivel puxar,
#    senao a gente nao vai saber nunca, vai ficar la eternamente desse jeito.
#    Nao tem que inventar numero velho, tem que falar nao sei, coloca la nao
#    sei. E faz um arquivo de uma lista de tudo que tem dependencia de nao sei."
print('')
print('[2b] a lista dos NAO SEI')
falta_por_tipo = {}
falta_por_card = {}
for x in saida:
    for f in x['faltou']:
        falta_por_tipo.setdefault(f, set()).add(x['card_id'])
        falta_por_card.setdefault(x['card_id'], set()).add(f)
try:
    with open(NAOSEI, 'w', encoding='utf-8') as f:
        f.write('=' * 74 + '\n')
        f.write('  NAO SEI — tudo que o motor dos bonus nao conseguiu puxar\n')
        f.write('  gerado em %s\n' % time.strftime('%d/%m/%Y %H:%M'))
        f.write('=' * 74 + '\n\n')
        f.write('REGRA (ordem do Luis, 15/08): quando o dado nao existe, o motor\n')
        f.write('NAO poe zero. Poe NAO SEI, e o card aparece nesta lista. Zero e um\n')
        f.write('numero inventado — e numero inventado some, "nao sei" cobra.\n\n')
        f.write('-' * 74 + '\n')
        f.write('O RESUMO\n')
        f.write('-' * 74 + '\n')
        f.write('  %d pares card x funcao ao todo\n' % len(saida))
        f.write('  %d pares com pelo menos um NAO SEI\n' %
                sum(1 for x in saida if x['faltou']))
        f.write('  %d cards distintos afetados\n\n' % len(falta_por_card))
        for tipo in sorted(falta_por_tipo, key=lambda k: -len(falta_por_tipo[k])):
            ids = falta_por_tipo[tipo]
            npar = sum(1 for x in saida if tipo in x['faltou'])
            f.write('  %-16s %6d cards  %6d pares\n' % (tipo, len(ids), npar))
        f.write('\n')
        f.write('-' * 74 + '\n')
        f.write('DE ONDE CADA UM DEVERIA VIR\n')
        f.write('-' * 74 + '\n')
        f.write('  ⛔ A DIFERENCA QUE IMPORTA (ordem do Luis, 15/08):\n')
        f.write('     NAO ACHEI  = o card nunca foi coletado nessa fonte -> NAO SEI\n')
        f.write('     ACHEI E NAO TEM = o card esta na fonte e o campo veio vazio\n')
        f.write('                       -> isso e ZERO de verdade, e NAO entra aqui.\n\n')
        f.write('  ⛔ 17/08: TUDO ABAIXO VEM DE UM LUGAR SO — a base unica,\n')
        f.write('     que desce do BANCO pelo BAIXAR-BASE. Ate 16/08 vinha de\n')
        f.write('     quatro arquivos soltos, um deles o HTML que este proprio\n')
        f.write('     sistema gera.\n\n')
        f.write('  corpo .......... as 12 medidas, campo `corpo` da base.\n')
        f.write('                   Falta = a carta nunca foi coletada no efHub.\n')
        f.write('  pe ruim ........ campo `pe_ruim` da base (frequencia, precisao).\n')
        f.write('  estilo da IA ... campo `com` da base. Quem separa "conferi e\n')
        f.write('                   nao tem" de "nunca perguntei" e o campo\n')
        f.write('                   `visto_na_casca`, que tambem desce do banco.\n\n')
        f.write('-' * 74 + '\n')
        f.write('A LISTA, CARD POR CARD\n')
        f.write('-' * 74 + '\n')
        nomes = {}
        for cid, c in BASEC.items():
            nomes[cid] = c.get('nome') or ''
        for cid in sorted(falta_por_card,
                          key=lambda k: (-len(falta_por_card[k]), nomes.get(k, ''))):
            f.write('  %-16s %-34s nao sei: %s\n' % (
                cid, (nomes.get(cid) or '?')[:34],
                ' · '.join(sorted(falta_por_card[cid]))))
    print('   %s  ...  %d cards' % (NAOSEI, len(falta_por_card)))
except Exception as e:
    print('   ERRO gravando o %s: %s' % (NAOSEI, e))

# --------------------------------------------- 3) GRAVA NA MAQUINA
print('')
print('[3/4] gravando na maquina')

# ⛔ 17/08 — O ANTES E DEPOIS, NA MESMA RODADA.
#    A troca das fontes (quatro arquivos soltos -> so a base) MUDA nota. Trocar
#    e nao mostrar o que mudou e como o sistema chegou a ter cinco de-paras: a
#    mudanca passa, ninguem ve, e dois meses depois ninguem sabe de onde veio o
#    numero. Entao o proprio motor le o bonus.jsonl ANTERIOR antes de escrever
#    por cima, e diz linha por linha o que mudou.
try:
    _antes = {}
    if os.path.exists(SAIDA):
        with open(SAIDA, encoding='utf-8') as f:
            for _l in f:
                _l = _l.strip()
                if not _l:
                    continue
                try:
                    _r = json.loads(_l)
                    _antes[(_r.get('card_id'), _r.get('funcao'))] = _r
                except Exception:
                    pass
    if _antes:
        _agora = {(x.get('card_id'), x.get('funcao')): x for x in saida}
        _nos_dois = set(_antes) & set(_agora)

        def _n(v):
            return round(v, 4) if isinstance(v, (int, float)) else None

        _mud, _por = [], {}
        for k in _nos_dois:
            if _n(_antes[k].get('b_total')) != _n(_agora[k].get('b_total')):
                _mud.append(k)
                for _c in ('b_corpo', 'b_pe_ruim', 'b_estilo', 'b_ia'):
                    if _n(_antes[k].get(_c)) != _n(_agora[k].get(_c)):
                        _por[_c] = _por.get(_c, 0) + 1
        _ganhou = [k for k in _nos_dois
                   if _antes[k].get('b_pe_ruim') is None
                   and _agora[k].get('b_pe_ruim') is not None]
        _perdeu = [k for k in _nos_dois
                   if _antes[k].get('b_pe_ruim') is not None
                   and _agora[k].get('b_pe_ruim') is None]
        print('')
        print('   O ANTES E O DEPOIS — contra o bonus.jsonl que estava aqui')
        print('      linhas antes / agora ....... %s / %s'
              % ('{:,}'.format(len(_antes)), '{:,}'.format(len(_agora))))
        print('      linhas novas ............... %s' % '{:,}'.format(len(set(_agora) - set(_antes))))
        print('      linhas que sumiram ......... %s' % '{:,}'.format(len(set(_antes) - set(_agora))))
        print('      MUDARAM de nota ............ %s de %s'
              % ('{:,}'.format(len(_mud)), '{:,}'.format(len(_nos_dois))))
        for _c, _q in sorted(_por.items(), key=lambda x: -x[1]):
            print('         por %-12s %s' % (_c, '{:,}'.format(_q)))
        if _ganhou:
            print('      GANHARAM pe ruim (era nao sei) . %s' % '{:,}'.format(len(_ganhou)))
        if _perdeu:
            print('      ⛔ PERDERAM pe ruim ............. %s  <<< OLHE ISTO'
                  % '{:,}'.format(len(_perdeu)))
        if _mud:
            print('      os primeiros que mudaram:')
            for k in _mud[:8]:
                print('         %-16s %-24s %s -> %s'
                      % (k[0], str(k[1])[:24], _antes[k].get('b_total'),
                         _agora[k].get('b_total')))
            try:
                with open('BONUS-O-QUE-MUDOU.txt', 'w', encoding='utf-8') as f:
                    f.write('as linhas de bonus que mudaram de nota nesta rodada\n')
                    f.write('%d de %d\n\n' % (len(_mud), len(_nos_dois)))
                    for k in _mud:
                        a, b = _antes[k], _agora[k]
                        f.write('%s | %s | %s -> %s | corpo %s->%s pe %s->%s '
                                'estilo %s->%s ia %s->%s\n'
                                % (k[0], k[1], a.get('b_total'), b.get('b_total'),
                                   a.get('b_corpo'), b.get('b_corpo'),
                                   a.get('b_pe_ruim'), b.get('b_pe_ruim'),
                                   a.get('b_estilo'), b.get('b_estilo'),
                                   a.get('b_ia'), b.get('b_ia')))
                print('      a lista inteira .......... BONUS-O-QUE-MUDOU.txt')
            except Exception:
                pass
        print('')
except Exception as _e:
    print('   (nao consegui comparar com o anterior: %s)' % str(_e)[:60])

try:
    os.makedirs('saida_v6', exist_ok=True)
    with open(SAIDA, 'w', encoding='utf-8') as f:
        for x in saida:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    print('   %s  ...  %d linhas' % (SAIDA, len(saida)))
    print('   (e daqui que o gera_encaixe.py le)')
except Exception as e:
    print('   ERRO gravando o %s: %s' % (SAIDA, e))

# ------------------------------------------------- 4) GRAVA NO BANCO
print('')
print('[4/4] gravando no banco')
resumo = []
cfg = {}
if os.path.exists('config.txt'):
    for linha in open('config.txt', encoding='utf-8'):
        linha = linha.strip()
        if linha and not linha.startswith('#') and '=' in linha:
            k, v = linha.split('=', 1)
            cfg[k.strip()] = v.strip()
URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')

if _db.enabled():
    import motor_db_results as _dbout
    if _dbout.configured():
        for x in saida:
            key = (x['card_id'], x['funcao'])
            if key not in OPTIMIZATION_RESULT_IDS:
                raise SystemExit('PARE: %s|%s sem optimization_result_id' % key)
            _dbout.write_bonus(x, OPTIMIZATION_RESULT_IDS[key])
        resumo.append(('motor_bonus_results_v2', len(saida), 0))
    else:
        print('   writer v2 desligado — somente arquivo local foi gravado.')
elif not URL or not KEY or 'COLE_AQUI' in KEY:
    print('   sem config.txt com a chave do Supabase — pulei o banco.')
    print('   A maquina ja tem tudo: o encaixe funciona do mesmo jeito.')
else:
    CAB = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
           'Content-Type': 'application/json'}

    def manda(tabela, linhas, chave, sem=None):
        """upsert em lotes. `sem` = campos a tirar se o banco nao os conhecer."""
        if not linhas:
            print('   nada a subir'); return 0, 0
        ok = falha = 0
        cortado = []
        for i in range(0, len(linhas), LOTE):
            lote = linhas[i:i + LOTE]
            corpo = json.dumps(lote, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                '%s/rest/v1/%s?on_conflict=%s' % (URL, tabela, chave),
                data=corpo,
                headers=dict(CAB, **{'Prefer':
                                     'resolution=merge-duplicates,return=minimal'}),
                method='POST')
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    r.read(); ok += len(lote)
            except urllib.error.HTTPError as e:
                det = e.read().decode('utf-8', 'replace')[:300]
                # ⛔ 15/08: coluna que o banco ainda nao tem. Em vez de perder a
                #    rodada inteira, tira o campo e manda o resto. O que ficou de
                #    fora sai avisado no fim — nunca em silencio.
                achou = None
                if 'PGRST204' in det:
                    for campo in (sem or []):
                        if "'%s'" % campo in det:
                            achou = campo
                            break
                if achou:
                    if achou not in cortado:
                        cortado.append(achou)
                        print('   o banco nao tem a coluna \'%s\' — mandando sem '
                              'ela' % achou)
                    for x in linhas:
                        x.pop(achou, None)
                    for x in lote:
                        x.pop(achou, None)
                    corpo = json.dumps(lote, ensure_ascii=False).encode('utf-8')
                    req2 = urllib.request.Request(
                        '%s/rest/v1/%s?on_conflict=%s' % (URL, tabela, chave),
                        data=corpo,
                        headers=dict(CAB, **{'Prefer':
                                             'resolution=merge-duplicates,'
                                             'return=minimal'}),
                        method='POST')
                    try:
                        with urllib.request.urlopen(req2, timeout=120) as r:
                            r.read(); ok += len(lote)
                    except Exception as e2:
                        print('   ERRO no lote %d: %s' % (i // LOTE + 1, e2))
                        falha += len(lote)
                else:
                    print('   ERRO %s no lote %d: %s' % (e.code, i // LOTE + 1, det))
                    falha += len(lote)
            except Exception as e:
                print('   ERRO no lote %d: %s' % (i // LOTE + 1, e))
                falha += len(lote)
            print('   %d/%d' % (min(i + LOTE, len(linhas)), len(linhas)), end='\r')
            time.sleep(PAUSA)
        print('   %d subiram · %d falharam        ' % (ok, falha))
        if cortado:
            print('   ⚠ ficaram DE FORA do banco: %s' % ' · '.join(cortado))
            print('     rode o sql/23-bonus-faltou.sql no Supabase para ter isso la')
        return ok, falha

    print('   o molde do fisico -> insumo_bonus_corpo')
    linhas = []
    for f in sorted(set(list(molde.direcao.keys()) + list(molde.tipo.keys()))):
        for m in molde.ordem:
            ct = molde.corte(m, f)
            linhas.append({'funcao': f, 'medida': m, 'direcao': molde.dir(m, f),
                           'peso': molde.peso(m), 'corte1': ct[0], 'corte2': ct[1],
                           'corte3': ct[2], 'corte4': ct[3]})
    resumo.append(('insumo_bonus_corpo',) + manda('insumo_bonus_corpo', linhas,
                                                  'funcao,medida'))

    print('   as posicoes -> insumo_bonus_posicao')
    linhas = [{'tipo': 'funcao', 'nome': k, 'posicoes': v}
              for k, v in (ins['posicao']['posicoes_da_funcao'] or {}).items()]
    linhas += [{'tipo': 'estilo', 'nome': k, 'posicoes': v}
               for k, v in (ins['posicao']['onde_o_estilo_liga'] or {}).items()]
    resumo.append(('insumo_bonus_posicao',) + manda('insumo_bonus_posicao',
                                                    linhas, 'tipo,nome'))

    print('   as constantes -> insumo_bonus_parametro')
    DESC = {'bonus_corpo_max': 'o tamanho do bonus de corpo: de -1,5 a +1,5',
            'estilo_ia_ponto': 'quanto vale o bonus cheio de estilo de jogo da IA',
            'estilo_ia_teto': 'quantos estilos de IA dao o bonus cheio',
            'estilo_ativo': 'quanto ganha quem tem o estilo ligado na posicao',
            'pe_ruim_teto': 'o teto do bonus de pe ruim'}
    linhas = [{'chave': k, 'valor': v, 'descricao': DESC.get(k, '')}
              for k, v in ins['parametros'].items()]
    linhas.append({'chave': 'pe_ruim_teto', 'valor': ins['pe_ruim']['teto'],
                   'descricao': DESC['pe_ruim_teto']})
    for i, v in enumerate(ins['pe_ruim']['frequencia']):
        linhas.append({'chave': 'pe_ruim_frequencia_%d' % i, 'valor': v,
                       'descricao': 'multiplicador da frequencia %d' % i})
    for i, v in enumerate(ins['pe_ruim']['precisao']):
        linhas.append({'chave': 'pe_ruim_precisao_%d' % i, 'valor': v,
                       'descricao': 'multiplicador da precisao %d' % i})
    resumo.append(('insumo_bonus_parametro',) + manda('insumo_bonus_parametro',
                                                      linhas, 'chave'))

    print('   o estilo de jogo da IA -> cards_base.estilo_ia')
    linhas = [{'card_id': k, 'estilo_ia': v} for k, v in IA.items()]
    resumo.append(('cards_base.estilo_ia',) + manda('cards_base', linhas,
                                                    'card_id'))

    print('   o resultado -> bonus')
    agora = time.strftime('%Y-%m-%dT%H:%M:%S')
    resumo.append(('bonus',) + manda(
        'bonus', [dict(x, rodado_em=agora) for x in saida], 'card_id,funcao',
        sem=['faltou', 'corpo_soma', 'corpo_pct', 'detalhe', 'motor_bonus']))

# ------------------------------------------------------------- o relatorio
print('')
print('=' * 70)
print('  RESUMO')
print('=' * 70)
for nome, ok, falha in resumo:
    print('  %-26s %6d subiram   %5d falharam' % (nome, ok, falha))
if resumo:
    print('')
print('  MEDIA DE CADA BONUS (so as linhas que ganharam alguma coisa)')
for k, rot in (('corpo', 'corpo'), ('pe', 'pe ruim'),
               ('est', 'estilo ativo'), ('ia', 'estilo da IA')):
    n = conta[k]
    print('  %-14s %6d linhas   media %+0.3f' % (
        rot, n, (soma[k] / n) if n else 0))
print('')
if sem_corpo:
    print('  %d pares sem as 12 medidas do corpo — bonus de corpo ficou 0' % sem_corpo)
if sem_pe:
    print('  %d pares sem o dado do pe ruim — bonus ficou 0' % sem_pe)
if sem_est:
    print('  %d pares sem estilo de jogo' % sem_est)
if sem_ia:
    print('  %d pares sem estilo de jogo da IA — bonus ficou 0' % sem_ia)
print('')
print('  AGORA RODE O GERAR-ENCAIXE.bat: a tela passa a usar estes numeros')
print('  em vez de calcular por conta propria.')
pausa()
