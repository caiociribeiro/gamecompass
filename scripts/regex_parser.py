"""Limpa um bloco de requisitos (mínimos OU recomendados) e extrai a RAM.

Aceita valores inteiros ou decimais em MB/GB, com 1024 MB por GB.
"""

import argparse
from fractions import Fraction
from html.parser import HTMLParser
import json
from math import ceil
import re
import sys


RAM_VALUE = re.compile(
    r"([0-9]+(?:[.,][0-9]{1,2})?)\s*(MB|GB)(?:\s+(?:(?:de|of)\s+)?RAM)?"
    r"(?:\s+DDR[2-5](?:[- ]?\d{3,5})?)?",
    re.IGNORECASE,
)

RAM_FIELD = re.compile(
    r"(?:mem[oó]ria|memory|ram)\s*:\s*(.*)",
    re.IGNORECASE,
)

HARDWARE_FIELDS = {
    "CPU": re.compile(
        r"(?:processador|processor|cpu)\s*:\s*(.*)",
        re.IGNORECASE,
    ),
    "GPU": re.compile(
        r"(?:placa\s+de\s+v[ií]deo|placa\s+gr[aá]fica|gr[aá]ficos|"
        r"graphics(?:\s+card)?|video\s+card|gpu)\s*:\s*(.*)",
        re.IGNORECASE,
    ),
}


class _RequirementHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden = True
        elif not self.hidden and tag in {"br", "li", "p", "div", "ul", "ol"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = False
        elif not self.hidden and tag in {"li", "p", "div", "ul", "ol"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def clean_html(html: str) -> str:
    """Retira as tags e preserva a separação dos campos em linhas."""
    parser = _RequirementHTMLParser()
    parser.feed(html)
    parser.close()

    lines = (
        " ".join(line.split())
        for line in "".join(parser.parts).splitlines()
    )
    return "\n".join(line for line in lines if line)


def normalize_ram_gb(value: str) -> int:
    """Converte MB/GB para GB inteiros, arredondando frações para cima."""
    match = RAM_VALUE.fullmatch(value.strip())

    if match is None:
        raise ValueError(
            "RAM inválida: use um valor em MB ou GB, "
            "por exemplo 8192 MB, 8 GB RAM ou 2.5 GB."
        )

    amount = Fraction(match.group(1).replace(",", "."))

    if amount <= 0:
        raise ValueError("A quantidade de RAM deve ser maior que zero.")

    if match.group(2).upper() == "MB":
        return ceil(amount / 1024)

    return ceil(amount)


def legacy_inline_fields(text: str) -> dict[str, str]:
    """Lê fichas antigas com cabeçalho, CPU e RAM explícita separados por vírgulas.

    Não procura capacidades soltas: VRAM e armazenamento não são RAM.
    Blocos com dois níveis devem ser separados antes da extração.
    """
    heading = re.compile(r"^(?:minimum|recommended|m[ií]nimos?|recomendados?)\s*:\s*(.+)$", re.I)
    entries = [heading.fullmatch(line.strip()) for line in text.splitlines()]
    entries = [match for match in entries if match]
    if len(entries) > 1:
        raise ValueError("Forneça mínimos e recomendados separadamente.")
    if not entries:
        return {}
    parts = [part.strip() for part in entries[0][1].split(",")]
    if not re.match(r"(?:processador|processor)\b", parts[0], re.I):
        return {}
    fields = {"CPU": parts[0]}
    for part in parts[1:]:
        kind = None
        if re.fullmatch(r"[0-9]+(?:[.,][0-9]+)?\s*(?:MB|GB)\s+(?:(?:de|of)\s+)?RAM", part, re.I):
            kind = "RAM"
        elif re.match(r"(?:placa\s+gr[aá]fica|graphics\s+card|video\s+card)\b", part, re.I):
            kind = "GPU"
        elif re.match(r"Windows[®™]?\s", part, re.I):
            kind = "OS"
        if kind:
            if kind in fields:
                raise ValueError(f"Campo {kind} repetido na ficha antiga.")
            fields[kind] = part
    return fields if "RAM" in fields else {}


def extract_ram_gb(html: str) -> int | None:
    """Lê somente o campo de RAM. Ausência retorna None; formato ambíguo gera erro."""
    fields = []

    for line in clean_html(html).splitlines():
        match = RAM_FIELD.fullmatch(line)
        if match:
            fields.append(match.group(1))

    if not fields:
        value = legacy_inline_fields(clean_html(html)).get("RAM")
        return normalize_ram_gb(value) if value else None

    if len(fields) > 1:
        raise ValueError(
            "Há vários campos de RAM: "
            "forneça mínimos e recomendados separadamente."
        )

    return normalize_ram_gb(fields[0])


def extract_hardware_text(html: str, component_type: str) -> str | None:
    """Extrai um campo de CPU/GPU, preservando alternativas e variantes."""
    component_type = component_type.strip().upper()
    if component_type not in HARDWARE_FIELDS:
        raise ValueError("component_type deve ser CPU ou GPU.")

    pattern = HARDWARE_FIELDS[component_type]
    fields = []

    for line in clean_html(html).splitlines():
        match = pattern.fullmatch(line)
        if match:
            fields.append(match.group(1).strip())

    if not fields:
        return legacy_inline_fields(clean_html(html)).get(component_type)

    if len(fields) > 1:
        raise ValueError(
            f"Há vários campos de {component_type}: "
            "forneça mínimos e recomendados separadamente."
        )

    if not fields[0]:
        raise ValueError(
            f"O campo de {component_type} foi encontrado, mas está vazio."
        )

    return fields[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--text",
        required=True,
        help="Um bloco de requisitos em HTML ou texto.",
    )
    args = parser.parse_args(argv)

    try:
        result = {
            "text": clean_html(args.text),
            "ram_gb": extract_ram_gb(args.text),
            "cpu_text": extract_hardware_text(args.text, "CPU"),
            "gpu_text": extract_hardware_text(args.text, "GPU"),
        }
    except ValueError as exc:
        print(f"Erro nos requisitos: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
