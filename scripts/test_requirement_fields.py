"""Verifica formatos reais de campos, sem coletar dados ou alterar o banco."""

import unittest

from extract_steam_requirements import extract_os_text
from regex_parser import clean_html, extract_ram_gb, normalize_ram_gb


class RequirementFieldTests(unittest.TestCase):
    def test_os_labels_in_both_portuguese_variants_and_english(self):
        for label in ("OS", "SO", "Operating System", "Sistema Operacional",
                      "Sistema Operativo", "Sistema Operativo *"):
            with self.subTest(label=label):
                text = clean_html(f"<strong>{label}:</strong> Windows 10 64-bit")
                self.assertEqual(extract_os_text(text), "Windows 10 64-bit")

    def test_missing_os_is_not_inferred_from_an_additional_note(self):
        self.assertIsNone(extract_os_text("Additional Notes: Windows 10 recommended"))

    def test_empty_or_duplicate_os_stays_ambiguous(self):
        for text in ("Sistema Operativo *:", "OS: Windows 10\nSO: Windows 11"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                extract_os_text(text)

    def test_fractional_ram_rounds_up_without_float_arithmetic(self):
        for text, expected in (("2.5 GB", 3), ("2,5 GB de RAM", 3),
                               ("1.25 GB RAM", 2), ("1536 MB", 2),
                               ("8192 MB de RAM", 8), ("8GB", 8)):
            with self.subTest(text=text):
                self.assertEqual(normalize_ram_gb(text), expected)

    def test_decimal_ram_is_read_only_from_the_memory_field(self):
        html = "Graphics: GPU fixture 8GB<br>Memory: 2.5 GB RAM"
        self.assertEqual(extract_ram_gb(html), 3)
        self.assertIsNone(extract_ram_gb("Graphics: GPU fixture 8GB"))

    def test_invalid_or_ambiguous_ram_does_not_become_a_number(self):
        for text in ("0 GB", "-2 GB", "2.5.0 GB", "8/16 GB", "8,192 MB", "2x8 GB"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                normalize_ram_gb(text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
