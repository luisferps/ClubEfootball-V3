import ast
import hashlib
import unittest
from pathlib import Path


PROGRAMAS = Path(__file__).resolve().parents[1] / "programas"
EXPECTED = {
    "equacao.py": {
        "_mult": "9c3f6e80204c80c4ac645fddd80b2d8292edca7bf20292538706f54e7d6bf90a",
        "_multv": "d09be79e23ca9f3f79fb05568901b8b510fbe7af044479ea36c80cb0d3c9232c",
        "aplica_buff": "263ebffc65e9d247a5ae5f9c7f697b4c7b23789cfcbc0a3a22186cd6055edfc7",
        "base_barras": "a6c77855afe5b0fcd95c181dd2b4fea33007b4d565b17af15fd45320d6f60a61",
        "buff_de": "fa505b90ff45aa0ceb165b3e27331103d60effd4ec3d0db6763098623119d407",
        "mult_de": "341d070addc310bfde84f2e50d33657f532c877f30f70a762bd831cb85a0609b",
        "nivel_max_barra": "84107012ac7a9fa66231f959d912b40654fdd5d346fe4b1af3ce7ea9193ca0a0",
    },
    "motor.py": {
        "Card": "64499094ec9e3dd98e6ce90d25cfe0de975c89f90afb0ec0cc7e9d2e0bbf01bf",
        "build_completo": "bc62ef654403ab318bce8a8bc25cd2a74c8839fa48feb9da15bca063732f5f25",
        "build_completo2": "b55b75879edc822d1f3c9fddd57ea783e494e27db23eb2520d1b857161bb927b",
        "expand": "78ef34e4c4106f5a2c833838ca10ac14ea17a67efcd711073bc98b381472f4f0",
    },
    "motor_bonus.py": {
        "bonus_do_corpo": "d012f2ce8c4cb0084a226dc73ca2440a613bb4afb3a2e0cab5319b0a00de5a2e",
        "bonus_do_estilo": "d2024aa3c5ad781689ea53e856442a7b5d97b0ab9ea8b58416fdb640920f159e",
        "bonus_do_estilo_ia": "10343b61db2b81f410c84a95c5f6080fe15aa7b762e1ba576e2d85bed37bdf92",
        "bonus_do_pe_ruim": "99fc3fdbfd482d00201533c4300363ed0a208a397f7fff023a0daa72cef5c7e0",
        "nota_da_medida": "b8e039b5b7a2b2e1e3a9c34434ca5dc86ff4bbf52c26dbfcfd4d4853473d7609",
    },
}


class FormulaGuardTests(unittest.TestCase):
    def test_calculation_ast_is_unchanged(self):
        for filename, expected in EXPECTED.items():
            tree = ast.parse((PROGRAMAS / filename).read_text(encoding="utf-8"))
            found = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in expected:
                    found[node.name] = hashlib.sha256(
                        ast.dump(node, include_attributes=False).encode()).hexdigest()
            self.assertEqual(found, expected, filename)


if __name__ == "__main__":
    unittest.main()

