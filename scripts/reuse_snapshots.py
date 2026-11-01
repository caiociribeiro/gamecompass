"""Copia snapshots verificados para outro lote, mantendo seus bytes e datas."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile

from extract_steam_requirements import extract_snapshot
from game_catalog import read_selection, sha256
from process_requirements import write_json_atomic


def validate_snapshot(folder: Path, appid: str) -> None:
    extracted = extract_snapshot(folder)
    metadata = json.loads((folder / "metadata.json").read_bytes())
    if extracted["id"] != appid:
        raise ValueError("Snapshot reutilizado com identificação divergente.")
    if metadata.get("country") != "br" or metadata.get("language") != "portuguese":
        raise ValueError("Os snapshots reutilizados devem ter região BR e idioma português.")


def reuse_snapshots(source: Path, destination: Path, selection_path: Path) -> int:
    source_root, target_root = source.resolve(), destination.resolve()
    if (source_root == target_root or source_root in target_root.parents or target_root in source_root.parents):
        raise ValueError("Os lotes de origem e destino devem ser pastas separadas, sem sobreposição.")
    if not source.is_dir():
        raise ValueError("A pasta com os snapshots anteriores não foi encontrada.")
    selection = read_selection(selection_path)
    appids = [row["id"] for row in selection["games"]]
    digest = sha256(selection_path)
    manifest_path = destination / "collection.json"
    manifest = {"selection_sha256": digest, "collection_selection_sha256": digest,
        "appids": appids, "status": "collecting", "issues": []}
    if destination.exists():
        if not manifest_path.is_file():
            raise ValueError("O destino existe sem manifesto de coleta; escolha outra pasta.")
        manifest = json.loads(manifest_path.read_bytes())
        ids = manifest.get("appids") if isinstance(manifest, dict) else None
        if (not isinstance(ids, list) or any(not isinstance(value, str) for value in ids)
            or len(ids) != len(set(ids)) or set(ids) != set(appids)
            or any(not isinstance(manifest.get(key), str) or not re.fullmatch(r"[a-f0-9]{64}", manifest[key])
                   for key in ("selection_sha256", "collection_selection_sha256"))):
            raise ValueError("O manifesto do destino não corresponde a este lote de AppIDs.")
    sources = manifest.get("reuse_sources", [])
    if not isinstance(sources, list):
        raise ValueError("Histórico de reutilização inválido.")
    pending = []
    # Uma origem corrompida não deve deixar metade dos snapshots publicados.
    for appid in appids:
        target, original = destination / appid, source / appid
        if target.exists():
            validate_snapshot(target, appid)
        elif original.exists():
            validate_snapshot(original, appid)
            pending.append(appid)
    if not pending:
        return 0
    destination.mkdir(parents=True, exist_ok=True)
    write_json_atomic(manifest_path, manifest)
    for appid in pending:
        with tempfile.TemporaryDirectory(prefix=".reuse-", dir=destination) as temporary:
            folder = Path(temporary)
            for name in ("appdetails.json", "metadata.json"):
                shutil.copyfile(source / appid / name, folder / name)
                (folder / name).chmod(0o644)
            validate_snapshot(folder, appid)
            folder.chmod(0o755)
            folder.rename(destination / appid)
    sources.append({"source_dir": str(source), "appids": pending,
        "source_manifest_sha256": sha256(source / "collection.json") if (source / "collection.json").is_file() else None,
        "reused_at": datetime.now(timezone.utc).isoformat()})
    manifest["reuse_sources"] = sources
    write_json_atomic(manifest_path, manifest)
    return len(pending)
