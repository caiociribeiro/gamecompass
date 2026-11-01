"""Coleta um AppID da loja Steam e preserva a resposta em uma nova pasta."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_app(appid: str, *, language: str = "english") -> tuple[bytes, dict]:
    """Valida a resposta, mantendo seus bytes originais para auditoria."""
    if not re.fullmatch(r"[1-9][0-9]*", appid):
        raise ValueError(
            "appid deve ser um inteiro positivo, sem zeros iniciais."
        )

    if language not in ("english", "portuguese"):
        raise ValueError("Idioma inválido para a coleta.")
    url = "https://store.steampowered.com/api/appdetails?" + urlencode({
        "appids": appid,
        "cc": "br",
        "l": language,
    })
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "GameCompass/0.1",
    })

    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"Steam retornou HTTP {response.status}.")
        raw = response.read(10_000_001)

    if len(raw) > 10_000_000:
        raise ValueError("A resposta ultrapassou o limite de 10 MB.")

    payload = json.loads(raw)
    entry = payload.get(appid) if isinstance(payload, dict) else None
    if not isinstance(entry, dict) or entry.get("success") is not True:
        raise ValueError(
            f"Steam não retornou dados para o AppID {appid}."
        )

    data = entry.get("data")
    if (
        not isinstance(data, dict)
        or str(data.get("steam_appid")) != appid
        or not isinstance(data.get("name"), str)
        or not data["name"].strip()
    ):
        raise ValueError(
            "A resposta não contém identificação válida do aplicativo."
        )

    requirements = data.get("pc_requirements")
    if not isinstance(requirements, dict):
        requirements = {}

    metadata = {
        "appid": appid,
        "title": data["name"],
        "source_url": url,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "country": "br",
        "language": language,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "requirements_available": {
            level: (
                isinstance(requirements.get(level), str)
                and bool(requirements[level].strip())
            )
            for level in ("minimum", "recommended")
        },
    }
    return raw, metadata


def save_snapshot(output_dir: Path, raw: bytes, metadata: dict) -> None:
    """Publica os dois arquivos juntos, preservando coletas anteriores."""
    if output_dir.exists():
        raise ValueError(
            "A pasta de saída já existe; escolha outra para a nova coleta."
        )

    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".steam-", dir=output_dir.parent
    ) as directory:
        temporary = Path(directory)
        response_path = temporary / "appdetails.json"
        metadata_path = temporary / "metadata.json"

        response_path.write_bytes(raw)
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        response_path.chmod(0o644)
        metadata_path.chmod(0o644)
        temporary.chmod(0o755)
        temporary.rename(output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appid", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        if args.output_dir.exists():
            raise ValueError(
                "A pasta de saída já existe; escolha outra para a nova coleta."
            )

        raw, metadata = fetch_app(args.appid)
        save_snapshot(args.output_dir, raw, metadata)

    except (OSError, ValueError, UnicodeError, URLError) as exc:
        print(f"Erro na coleta Steam: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "status": "ok",
        "output_dir": str(args.output_dir),
        **metadata,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
