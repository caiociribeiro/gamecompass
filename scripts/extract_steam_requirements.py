"""Separa requisitos por plataforma e nível, preservando o texto de SO."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from process_requirements import write_json_atomic
from regex_parser import clean_html


PLATFORMS = {
    "windows": ("windows", "pc_requirements"),
    "macos": ("mac", "mac_requirements"),
    "linux": ("linux", "linux_requirements"),
}
LEVELS = ("minimum", "recommended")

LEVEL_HEADING = re.compile(
    r"(?:minimum|recommended|m[ií]nimos?|recomendados?)\s*:?",
    re.IGNORECASE,
)
OS_FIELD = re.compile(
    r"(?:OS|SO|Operating\s+System|Sistema\s+Operacional)\s*\*?\s*:\s*(.*)",
    re.IGNORECASE,
)


def extract_os_text(text: str) -> str | None:
    """Extrai o campo de SO de um texto já limpo, sem interpretar versões."""
    fields = []
    for line in text.splitlines():
        match = OS_FIELD.fullmatch(line)
        if match:
            fields.append(match.group(1).strip())

    if not fields:
        return None
    if len(fields) > 1 or not fields[0]:
        raise ValueError("Campo de SO vazio ou repetido no mesmo bloco.")

    return fields[0]


def extract_snapshot(input_dir: Path) -> dict:
    """Confere a integridade da coleta antes de separar seus requisitos."""
    raw_path = input_dir / "appdetails.json"
    metadata_path = input_dir / "metadata.json"

    raw = raw_path.read_bytes()
    metadata_bytes = metadata_path.read_bytes()
    metadata = json.loads(metadata_bytes)

    required = (
        "appid", "title", "response_sha256", "source_url", "collected_at",
    )
    if not isinstance(metadata, dict) or any(
        not isinstance(metadata.get(key), str) or not metadata[key].strip()
        for key in required
    ):
        raise ValueError("Metadados da coleta inválidos.")

    appid = metadata["appid"]
    if not re.fullmatch(r"[1-9][0-9]*", appid):
        raise ValueError("AppID inválido nos metadados.")

    digest = hashlib.sha256(raw).hexdigest()
    if digest != metadata["response_sha256"]:
        raise ValueError(
            "Hash divergente: a resposta difere da coleta registrada."
        )

    payload = json.loads(raw)
    entry = payload.get(appid) if isinstance(payload, dict) else None
    if not isinstance(entry, dict) or entry.get("success") is not True:
        raise ValueError(
            "A resposta não contém uma coleta válida para esse AppID."
        )

    data = entry.get("data")
    if (
        not isinstance(data, dict)
        or str(data.get("steam_appid")) != appid
        or data.get("name") != metadata["title"]
    ):
        raise ValueError(
            "Identificação do aplicativo diverge dos metadados."
        )

    flags = data.get("platforms")
    if not isinstance(flags, dict):
        flags = {}

    platforms = {}
    issues = []

    for platform, (flag, field) in PLATFORMS.items():
        native = flags.get(flag)
        if not isinstance(native, bool):
            native = None
            issues.append(
                f"{platform}: suporte nativo não informado ou inválido."
            )

        requirements = data.get(field)
        if requirements is None or requirements == []:
            requirements = {}
        elif not isinstance(requirements, dict):
            issues.append(
                f"{platform}: formato dos requisitos inválido."
            )
            requirements = {}

        blocks = {"native_support": native}

        for level in LEVELS:
            blocks[level] = None
            html = requirements.get(level)

            if html is None or (
                isinstance(html, str) and not html.strip()
            ):
                if native is True:
                    issues.append(
                        f"{platform}.{level}: requisito ausente."
                    )
                continue

            if not isinstance(html, str):
                issues.append(
                    f"{platform}.{level}: requisito deve ser texto."
                )
                continue

            text = clean_html(html)

            if not text or all(
                LEVEL_HEADING.fullmatch(line)
                for line in text.splitlines()
            ):
                if native is True:
                    issues.append(
                        f"{platform}.{level}: requisito ausente."
                    )
                continue

            os_text = None
            try:
                os_text = extract_os_text(text)
                if os_text is None:
                    issues.append(
                        f"{platform}.{level}: campo de SO ausente."
                    )
            except ValueError as exc:
                issues.append(f"{platform}.{level}: {exc}")

            blocks[level] = {
                "html": html,
                "text": text,
                "os_text": os_text,
            }

        if native is False and any(
            blocks[level] is not None for level in LEVELS
        ):
            issues.append(
                f"{platform}: há requisitos, mas suporte nativo está falso."
            )

        platforms[platform] = blocks

    return {
        "status": "needs_review" if issues else "extracted",
        "id": appid,
        "title": data["name"],
        "platforms": platforms,
        "issues": issues,
        "source": {
            "response_path": str(raw_path),
            "metadata_path": str(metadata_path),
            "source_url": metadata["source_url"],
            "collected_at": metadata["collected_at"],
            "response_sha256": digest,
            "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        if args.output.resolve().is_relative_to(
            args.input_dir.resolve()
        ):
            raise ValueError(
                "A saída deve ficar fora da pasta da coleta original."
            )

        result = extract_snapshot(args.input_dir)
        write_json_atomic(args.output, result)

    except (OSError, ValueError, UnicodeError) as exc:
        print(f"Erro na extração Steam: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "status": result["status"],
        "id": result["id"],
        "title": result["title"],
        "native_platforms": [
            name
            for name, item in result["platforms"].items()
            if item["native_support"] is True
        ],
        "issues": result["issues"],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())