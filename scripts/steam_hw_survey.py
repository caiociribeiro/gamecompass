"""Coleta a participação das placas de vídeo na Steam Hardware & Software Survey.

Lê a tabela "ALL VIDEO CARDS" (último mês publicado) e guarda só os modelos que existem
no catálogo manual de hardware. A Steam informa o modelo sem a VRAM ("RTX 3060"), então
todas as variantes do catálogo ("RTX 3060 12GB", "RTX 3060 8GB") recebem a mesma fatia.
A pesquisa não publica modelos de processador, por isso não há equivalente para CPUs.

Uso:
  python scripts/steam_hw_survey.py               # baixa a página da Steam
  python scripts/steam_hw_survey.py pagina.html   # usa um HTML já salvo
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://store.steampowered.com/hwsurvey/videocard/"
CATALOG = ROOT / "data/catalog/hardware_manual_v1.csv"
OUTPUT = ROOT / "frontend/src/data/steamGpuSurvey.json"
ROW = re.compile(r"<span>([^<]+)</span></div></div>.*?substats_col_month_last_pct\"><strong>([\d.]+)%", re.S)
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def base_model(name: str) -> str:
    """Tira a VRAM do fim do nome do catálogo: "NVIDIA GeForce RTX 3060 12GB" -> "... RTX 3060"."""
    return re.sub(r"\s+\d+\s?GB$", "", name)


def parse(page: str) -> tuple[str, list[tuple[str, float]]]:
    month = re.search(rf"(?:{MONTHS}) 20\d\d", page)
    start = page.find("ALL VIDEO CARDS")
    if not month or start < 0:
        raise SystemExit("Página da Steam sem o mês da pesquisa ou sem a tabela ALL VIDEO CARDS.")
    end = page.find(">Other<", start)  # a tabela termina na linha "Other"
    rows = [(html.unescape(name).strip(), float(pct)) for name, pct in ROW.findall(page[start:end])]
    if not rows:
        raise SystemExit("Nenhuma linha encontrada na tabela ALL VIDEO CARDS.")
    return month.group(0), rows


def main() -> None:
    if len(sys.argv) > 1:
        page = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    else:
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "GameCompass-TCC"})
        page = urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "replace")
    month, rows = parse(page)
    with CATALOG.open(encoding="utf-8") as handle:
        gpus = [row["name"] for row in csv.DictReader(handle) if row["component_type"] == "GPU"]
    by_model: dict[str, list[str]] = {}
    for gpu in gpus:
        by_model.setdefault(norm(base_model(gpu)), []).append(gpu)
    items = [
        {"steam_name": name, "share_pct": pct, "catalog_names": sorted(by_model[norm(name)])}
        for name, pct in rows if norm(name) in by_model
    ]
    OUTPUT.write_text(json.dumps({
        "source": "Steam Hardware & Software Survey — ALL VIDEO CARDS",
        "source_url": SOURCE_URL,
        "survey_month": month,
        "collected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "note": "Participação do último mês publicado. Modelos sem correspondência no catálogo manual ficam de fora.",
        "items": items,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{month}: {len(rows)} modelos na Steam, {len(items)} no catálogo -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
