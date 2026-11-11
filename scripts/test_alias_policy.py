"""Política dos aliases revisados, verificada nos arquivos reais do catálogo.

Regra: o alias liga um nome publicado pela Steam a um modelo do catálogo, e
nunca adivinha a variante de memória. Um alias sem VRAM só pode apontar para um
modelo que tenha uma única variante no catálogo. Nomes ambíguos, genéricos ou
com erro de grafia na fonte continuam pendentes.

Executar: python scripts/test_alias_policy.py   (sem acesso ao Neo4j)
"""

import json
from pathlib import Path
import re
import unittest

from hardware_catalog import ROOT, read_catalog
from hardware_matcher import match_alternatives, normalize_name, read_aliases

CATALOG_PATH = ROOT / "data/catalog/hardware_manual_v1.csv"
ALIASES_PATH = ROOT / "data/catalog/hardware_aliases.json"
VRAM = re.compile(r"\s+\d+(?:\.\d+)?\s*(?:GB|MB)$", re.IGNORECASE)
HAS_VRAM = re.compile(r"\d\s*(?:GB|MB)\b", re.IGNORECASE)


class AliasPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = read_catalog(CATALOG_PATH, catalog_format="manual")
        cls.catalog = {(row["component_type"], normalize_name(row["name"])): row for row in rows}
        cls.aliases = read_aliases(ALIASES_PATH, cls.catalog)
        cls.rows = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))

    def resolve(self, text, kind="GPU"):
        return match_alternatives(text, kind, self.catalog, self.aliases, catalog_format="manual")

    def variants(self, kind, canonical):
        base = normalize_name(VRAM.sub("", canonical))
        return [name for (k, name) in self.catalog
                if k == kind and (name == base or (name.startswith(base) and VRAM.fullmatch(name[len(base):])))]

    def test_alias_without_memory_points_to_a_model_with_one_catalog_variant(self):
        violations = []
        for row in self.rows:
            if HAS_VRAM.search(row["alias"]) or not VRAM.search(row["canonical_name"]):
                continue
            found = self.variants(row["component_type"], row["canonical_name"])
            if len(found) != 1:
                violations.append((row["alias"], row["canonical_name"], found))
        self.assertEqual(violations, [])

    def test_reviewed_steam_names_resolve_to_the_single_catalog_model(self):
        expected = {
            "NVIDIA GeForce GTX 1650": "NVIDIA GeForce GTX 1650 4GB",
            "AMD Radeon™ RX 590": "AMD Radeon RX 590 8GB",
            "AMD RX VEGA 56": "AMD Radeon RX Vega 56 8GB",
            "AMD RX 470": "AMD Radeon RX 470 4GB",
            "AMD Radeon RX 570": "AMD Radeon RX 570 4GB",
            "GeForce GTX 950": "NVIDIA GeForce GTX 950 2GB",
            "NVIDIA® GeForce® GTX 760": "NVIDIA GeForce GTX 760 2GB",
            "nVidia 770": "NVIDIA GeForce GTX 770 2GB",
            "GTX 680": "NVIDIA GeForce GTX 680 2GB",
            "NVIDIA® GeForce® GTX 560": "NVIDIA GeForce GTX 560 1GB",
            "nVidia 450": "NVIDIA GeForce GTS 450",
            "Geforce 9600 GT": "NVIDIA GeForce 9600 GT 512MB",
            "Radeon R7 360": "AMD Radeon R7 360 2GB",
            "AMD Radeon HD 7870": "AMD Radeon HD 7870 2GB",
            "AMD R9 290X": "AMD Radeon R9 290X 4GB",
            "AMD R7 260x": "AMD Radeon R7 260X 2GB",
        }
        for steam_name, canonical in expected.items():
            with self.subTest(steam_name):
                alternative = self.resolve(steam_name)["alternatives"][0]
                self.assertEqual((alternative["status"], alternative["name"]), ("matched", canonical))
                self.assertEqual(alternative["score_status"], "classified")

    def test_names_from_the_120_game_batch_resolve_to_the_single_catalog_model(self):
        expected = {
            ("AMD Ryzen 1600x", "CPU"): "AMD Ryzen 5 1600X",
            ("Intel Core i5 3470 a 3.2 GHZ (4 CPUs)", "CPU"): "Intel Core i5-3470",
            ("Intel® iCore™ i5-3570K", "CPU"): "Intel Core i5-3570K",
            ("AMD Radeon RX 5500 XT 8GB", "GPU"): "AMD Radeon RX 5500 XT 8GB",
            ("AMD RX 5600-XT", "GPU"): "AMD Radeon RX 5600 XT 6GB",
            ("Radeon RX 6700 XT", "GPU"): "AMD Radeon RX 6700 XT 12GB",
            ("Intel Arc A750", "GPU"): "Intel Arc A750 8GB",
            ("Core i5 8600", "CPU"): "Intel Core i5-8600",
            ("Intel Core i5 8600K", "CPU"): "Intel Core i5-8600K",
            ("Intel i3-8100", "CPU"): "Intel Core i3-8100",
            ("Core i5 11600K", "CPU"): "Intel Core i5-11600K",
            ("AMD® Ryzen™ 5 2400G", "CPU"): "AMD Ryzen 5 2400G",
            ("AMD: Phenom II X4 955 - 4 Core, 3.2 GHz", "CPU"): "AMD Phenom II X4 955",
            ("RX Vega 64", "GPU"): "AMD Radeon RX Vega 64 8GB",
            ("Intel Arc A310", "GPU"): "Intel Arc A310 4GB",
            ("AMD R7 250x", "GPU"): "AMD Radeon R7 250X 1GB",
            ("AMD Radeon R9 285 (2 GB of VRAM, Shader Model 5.0)", "GPU"): "AMD Radeon R9 285 2GB",
            ("AMD® ATI Radeon™ HD 5870 (1GB VRAM)", "GPU"): "AMD Radeon HD 5870",
            ("AMD FX4300", "CPU"): "AMD FX-4300",
            ("NVidia 650TI", "GPU"): "NVIDIA GeForce GTX 650 Ti 2GB",
            ("AMD RX 5500XT 4GB", "GPU"): "AMD Radeon RX 5500 XT 4GB",
            ("nVidia GeForce 9600GT", "GPU"): "NVIDIA GeForce 9600 GT 512MB",
            ("AMD X8 FX-8350 a 4 GHZ (8 CPUs)", "CPU"): "AMD FX-8350",
            ("AMD HD7750", "GPU"): "AMD Radeon HD 7750 1GB",
            ("AMD Radeon RX 6600XT", "GPU"): "AMD Radeon RX 6600 XT 8GB",
            ("NVIDIA GTX650Ti", "GPU"): "NVIDIA GeForce GTX 650 Ti 2GB",
            ("AMD Radeon RX 480 (4 GB of VRAM, Shader Model 5.1)", "GPU"): "AMD Radeon RX 480 4GB",
            ("GeForce 970", "GPU"): "NVIDIA GeForce GTX 970",
            ("NVIDIA GeForce 760", "GPU"): "NVIDIA GeForce GTX 760 2GB",
            ("Geforce RTX 2070", "GPU"): "NVIDIA GeForce RTX 2070 8GB",
            ("NVIDIA GeForce RTX 2070 Super", "GPU"): "NVIDIA GeForce RTX 2070 SUPER 8GB",
            ("NVIDIA GeForce GTX 1050 Ti", "GPU"): "NVIDIA GeForce GTX 1050 Ti 4GB",
        }
        for (steam_name, kind), canonical in expected.items():
            with self.subTest(steam_name):
                alternative = self.resolve(steam_name, kind)["alternatives"][0]
                self.assertEqual((alternative["status"], alternative["name"]), ("matched", canonical))
                self.assertEqual(alternative["score_status"], "classified")

    def test_ambiguous_generic_and_misspelled_names_stay_pending(self):
        for steam_name, kind in [
            ("Arc A770", "GPU"),            # 8GB ou 16GB: o alias adivinharia a variante
            ("AMD Radeon RX 480", "GPU"),   # 4GB ou 8GB
            ("AMD Radeon RX 550", "GPU"),   # 2GB ou 4GB
            ("GeForce RTX 2060", "GPU"),    # a versão de 12GB tem outra configuração de chip
            ("AMD Radeon RX 5500 XT", "GPU"),  # 4GB ou 8GB, com classes diferentes
            ("NVIDIA GeForce RTX 2060", "GPU"),
            ("NVIDIA GeForce GTX 1060", "GPU"),  # 3GB ou 6GB
            ("AMD GPU Radeon RX 580", "GPU"),    # 4GB ou 8GB
            ("ATI Radeon R9 series", "GPU"),
            ("other shader model 4.0", "GPU"),
            ("Nvidia GeForce 2xx-Series", "GPU"),
            ("Qualcomm Adreno X1", "GPU"),
            ("Snapdragon X Elite", "CPU"),
            ("Intel Core 2 Duo", "CPU"),
            ("Intel Core i3-8350", "CPU"),   # a fonte omite o K; não corrigimos por conta própria
            ("Intel Core i3-9350F", "CPU"),  # modelo inexistente no catálogo
        ]:
            with self.subTest(steam_name):
                alternative = self.resolve(steam_name, kind)["alternatives"][0]
                self.assertEqual(alternative["status"], "not_found")
                self.assertIsNone(alternative["performance_score"])


if __name__ == "__main__":
    unittest.main()
