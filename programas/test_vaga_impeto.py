# -*- coding: utf-8 -*-
import unittest

from vaga_impeto import (ESTADO_DESCONHECIDA, ESTADO_LIVRE,
                         ESTADO_SEM_VAGA, normaliza_vaga, pode_testar_impeto)


class RegraDaVagaTest(unittest.TestCase):
    def test_salah_sem_vaga_nao_abre_candidato(self):
        card = {"id": "105880691466019", "sl": [0, 1],
                "vaga_estado": "confirmada_sem_vaga", "vaga": [None, None, None]}
        self.assertEqual(normaliza_vaga(card), ESTADO_SEM_VAGA)
        self.assertEqual(card["sl"], [0, 0])
        self.assertFalse(pode_testar_impeto(card))

    def test_vaga_marcada_pela_fonte_continua_elegivel(self):
        card = {"vaga": ["NATIVO", "VAGA", None], "sl": [0, 0]}
        self.assertEqual(normaliza_vaga(card), ESTADO_LIVRE)
        self.assertEqual(card["sl"], [0, 1])
        self.assertTrue(pode_testar_impeto(card))

    def test_resposta_nao_confirmada_falha_fechada(self):
        card = {"boostId": 0, "boostId2": 0, "sl": [0, 1],
                "vaga": [None, None, None]}
        self.assertEqual(normaliza_vaga(card), ESTADO_DESCONHECIDA)
        self.assertEqual(card["sl"], [0, 0])
        self.assertFalse(pode_testar_impeto(card))

    def test_sl_antigo_sozinho_nao_e_prova(self):
        card = {"sl": [0, 1]}
        self.assertEqual(normaliza_vaga(card), ESTADO_DESCONHECIDA)
        self.assertFalse(pode_testar_impeto(card))


if __name__ == "__main__":
    unittest.main()
