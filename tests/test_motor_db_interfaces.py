import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROGRAMAS = Path(__file__).resolve().parents[1] / "programas"
sys.path.insert(0, str(PROGRAMAS))


def optimization_row(card_id):
    card = {name: 60 for name in (
        "atr_ofensividade", "atr_controle_de_bola", "atr_drible",
        "atr_posse_de_bola", "atr_passe_rasteiro", "atr_passe_alto",
        "atr_finalizacao", "atr_cabeceio", "atr_cobranca_de_falta", "atr_efeito",
        "atr_velocidade", "atr_aceleracao", "atr_potencia_de_chute", "atr_salto",
        "atr_contato_fisico", "atr_equilibrio", "atr_resistencia",
        "atr_talento_defensivo", "atr_desarme", "atr_agressividade",
        "atr_envolvimento_defensivo", "atr_talento_de_goleiro", "atr_encaixe",
        "atr_defesa_goleiro", "atr_reflexos", "atr_alcance")}
    card.update({"card_id": card_id, "nome": "Teste", "orcamento": 20,
                 "input_presence": {"ai_playstyles": "known"}})
    return {"card_id": card_id, "funcao_codigo": "zagueiro_de_saida",
            "input_version": "motor-input-v3.0.0",
            "input_hash_algorithm": "sha256", "input_hash": "a" * 64,
            "input_payload": {"card": card,
                "funcao": {"codigo": "zagueiro_de_saida", "nome": "Zagueiro de saída"},
                "completude": {"motor_otimizacao_completo": True},
                "impetos": [
                    {"slot": 1, "estado": "sem_impeto_sem_vaga",
                     "impeto_id": None, "validacao": "validado", "divergencias": []},
                    {"slot": 2, "estado": "sem_impeto_sem_vaga",
                     "impeto_id": None, "validacao": "validado", "divergencias": []}],
                "habilidades": []}}


def bonus_row(card_id):
    return {"card_id": card_id, "funcao_codigo": "zagueiro_de_saida",
            "input_version": "motor-bonus-input-v4.0.0",
            "input_hash_algorithm": "sha256", "input_hash": "b" * 64,
            "input_payload": {"card": {"card_id": card_id, "corpo": [1] * 12,
                "pe_ruim": [2, 2], "modelo": "Destruidor", "com": [],
                "visto_na_casca": True},
                "funcao": {"codigo": "zagueiro_de_saida", "nome": "Zagueiro de saída"},
                "completude": {"motor_bonus_completo": True}}}


def snapshot_file(directory):
    import motor_db_bridge as bridge
    ids = [str(100000 + i) for i in range(699)]
    queue = {"count": 699, "card_ids": ids,
             "ambiguous_excluded": 127, "incomplete_excluded": 44,
             "sha256": bridge.canonical_sha256(ids), "queue_version": "test"}
    measures = ["Altura", "Coxa", "Panturrilha", "Cintura", "Peito",
                "Tam. braço", "Tam. pescoço", "Compr. perna", "Compr. braço",
                "Compr. pescoço", "Larg. ombro", "Alt. ombro"]
    bonus_parameters = [
        {"chave": "bonus_corpo_max", "valor": 1.5},
        {"chave": "estilo_ia_ponto", "valor": 1.0},
        {"chave": "estilo_ia_teto", "valor": 4},
        {"chave": "estilo_ativo", "valor": 0.5},
        {"chave": "pe_ruim_teto", "valor": 1.0},
    ] + [{"chave": "pe_ruim_frequencia_%d" % i, "valor": i / 3}
         for i in range(4)] + [
        {"chave": "pe_ruim_precisao_%d" % i, "valor": i / 3}
        for i in range(4)]
    models = {
        "insumo_multiplicador": [{"ponto": 65, "multiplicador": 1.0}],
        "insumo_tecnico": [{"id": 1, "nome": "T", "tem_boost": True,
                             "proficiencias": {"quickCounter": 65}, "boosts": []}],
        "insumo_habilidade": [{"chave": "heading", "nome_pt": "Cabeceio",
                                "tipo": "comum", "efeito": {}}],
        "insumo_impeto_catalogo": [{"nome": "Chute +1", "condicional": False,
                                     "efeito": [[6, 1]]}],
        "insumo_molde": [{"funcao": "Zagueiro de saída", "attr": 17,
                           "peso": 12, "alvo": 80}],
        "insumo_bloqueio": [], "incidencia_comunidade": {},
        "insumo_bonus_corpo": [
            {"funcao": "Zagueiro de saída", "medida": name,
             "peso": 5 if name == "Altura" else 1, "direcao": 1,
             "corte1": 1, "corte2": 2, "corte3": 3, "corte4": 4}
            for name in measures],
        "insumo_bonus_posicao": [
            {"tipo": "funcao", "nome": "Zagueiro de saída", "posicoes": ["ZC"]},
            {"tipo": "estilo", "nome": "Destruidor", "posicoes": ["ZC"]}],
        "insumo_bonus_parametro": bonus_parameters,
    }
    value = {"snapshot_version": bridge.SNAPSHOT_VERSION, "queue": queue,
             "optimization_inputs": [optimization_row(x) for x in ids],
             "bonus_inputs": [bonus_row(x) for x in ids], "models": models}
    value["snapshot_sha256"] = bridge.canonical_sha256(value)
    path = Path(directory) / "snapshot.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path, ids


class InterfaceTests(unittest.TestCase):
    def _reload(self, path):
        with patch.dict(os.environ, {"MOTOR_INPUT_SOURCE": "db_snapshot",
                                     "MOTOR_DB_SNAPSHOT": str(path)}):
            import motor_db_bridge as bridge
            return importlib.reload(bridge)

    def test_maps_699_original_ids_and_both_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            path, ids = snapshot_file(directory)
            bridge = self._reload(path)
            self.assertEqual(len(bridge.cards()), 699)
            self.assertEqual(bridge.cards()[ids[0]]["id"], ids[0])
            self.assertEqual(len(bridge.queue_entries()), 699)
            self.assertEqual(bridge.bonus_cards()[ids[-1]]["pe_ruim"], [2, 2])
            self.assertEqual(bridge.bonus_model()["corpo"]["pesos"]["Altura"], 5)

    def test_rejects_flag_false(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = snapshot_file(directory)
            value = json.loads(path.read_text(encoding="utf-8"))
            value["optimization_inputs"][0]["input_payload"]["completude"][
                "motor_otimizacao_completo"] = False
            value.pop("snapshot_sha256")
            import motor_db_bridge as bridge
            value["snapshot_sha256"] = bridge.canonical_sha256(value)
            path.write_text(json.dumps(value), encoding="utf-8")
            bridge = self._reload(path)
            with self.assertRaisesRegex(bridge.MotorInputError,
                                        "motor_otimizacao_completo"):
                bridge.snapshot()

    def test_rejects_variant_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = snapshot_file(directory)
            value = json.loads(path.read_text(encoding="utf-8"))
            value["optimization_inputs"][0]["card_id"] += "@ZC"
            value.pop("snapshot_sha256")
            import motor_db_bridge as bridge
            value["snapshot_sha256"] = bridge.canonical_sha256(value)
            path.write_text(json.dumps(value), encoding="utf-8")
            bridge = self._reload(path)
            with self.assertRaisesRegex(bridge.MotorInputError, "original"):
                bridge.snapshot()

    def test_writer_is_off_and_never_marks_current(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MOTOR_OUTPUT_WRITE_ENABLED", None)
            import motor_db_results as writer
            writer = importlib.reload(writer)
            self.assertFalse(writer.configured())
        with patch("motor_db_bridge.optimization_metadata", return_value={
                "funcao_codigo": "zc", "input_version": "motor-input-v3.0.0",
                "input_hash_algorithm": "sha256", "input_hash": "a" * 64}):
            row = writer.optimization_row({"card_id": "123", "funcao": "ZC"})
        self.assertEqual(row["status"], "pendente_validacao")
        self.assertFalse(row["is_current"])

    def test_db_mode_imports_formula_modules_without_legacy_models(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = snapshot_file(directory)
            env = dict(os.environ, MOTOR_INPUT_SOURCE="db_snapshot",
                       MOTOR_DB_SNAPSHOT=str(path), PYTHONPATH=str(PROGRAMAS))
            completed = subprocess.run(
                [sys.executable, "-c", "import equacao,motor;print(len(motor.CAT))"],
                cwd=directory, env=env, text=True, capture_output=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "1")


if __name__ == "__main__":
    unittest.main()
