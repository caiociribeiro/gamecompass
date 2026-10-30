"""Consulta pública da loja Steam com cache limitado e concorrência controlada."""

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from threading import Lock, RLock
import time
from urllib.parse import urlencode, urlsplit

import httpx

from .hardware import ROOT, requirements_block, clean_html


class SteamError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class Snapshot:
    data: dict
    source: dict


class SteamClient:
    def __init__(self, client=None, *, ttl=21_600, max_entries=128, min_interval=0.2):
        self.client = client or httpx.Client(timeout=httpx.Timeout(10, connect=5), follow_redirects=False,
            headers={"Accept": "application/json", "User-Agent": "GameCompass/0.2"})
        self.ttl, self.max_entries = ttl, max_entries
        self.min_interval = min_interval
        self.cache = OrderedDict()
        self.inflight = {}
        self.lock = RLock()
        self.rate_lock = Lock()
        self.last_request = 0.0
        self.pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="steam")

    def close(self):
        self.pool.shutdown(wait=True)
        self.client.close()

    def _fetch(self, appid: str) -> Snapshot:
        params = {"appids": appid, "cc": "br", "l": "portuguese"}
        url = "https://store.steampowered.com/api/appdetails?" + urlencode(params)
        with self.rate_lock:
            delay = self.min_interval - (time.monotonic() - self.last_request)
            if delay > 0:
                time.sleep(delay)
            self.last_request = time.monotonic()
        try:
            with self.client.stream("GET", url) as response:
                if response.status_code == 429:
                    raise SteamError("A Steam limitou as consultas. Aguarde e tente novamente.", 503)
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 10_000_000:
                        raise SteamError("A resposta da Steam ultrapassou o limite de tamanho.")
                    chunks.append(chunk)
                raw = b"".join(chunks)
            payload = json.loads(raw)
            entry = payload.get(appid) if isinstance(payload, dict) else None
            if not isinstance(entry, dict) or entry.get("success") is not True:
                raise SteamError("A Steam não disponibilizou esse AppID nesta região.", 404)
            data = entry.get("data")
            if (not isinstance(data, dict) or str(data.get("steam_appid")) != appid
                or not isinstance(data.get("name"), str) or not data["name"].strip()):
                raise SteamError("A Steam retornou identificação inválida.")
            if data.get("type") != "game":
                raise SteamError("Esse AppID não é um jogo da loja Steam.", 404)
            return Snapshot(data, {"source_url": url,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "response_sha256": hashlib.sha256(raw).hexdigest()})
        except (httpx.HTTPError, ValueError, UnicodeError) as exc:
            raise SteamError("Não foi possível consultar a loja Steam. Tente novamente.") from exc

    def _future(self, appid: str):
        if not isinstance(appid, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", appid):
            raise SteamError("AppID deve ser um inteiro positivo, sem zeros iniciais.", 422)
        with self.lock:
            entry = self.cache.get(appid)
            if entry and time.monotonic() - entry[0] < self.ttl:
                self.cache.move_to_end(appid)
                return entry[1], None
            future = self.inflight.get(appid)
            if future is None:
                if len(self.inflight) >= 32:
                    raise SteamError("Há muitas consultas em andamento. Tente novamente.", 503)
                future = self.pool.submit(self._fetch, appid)
                self.inflight[appid] = future
                future.add_done_callback(lambda done, key=appid: self._completed(key, done))
            return None, future

    def _completed(self, appid, future):
        with self.lock:
            if self.inflight.get(appid) is not future:
                return
            if future.exception() is None:
                self.cache[appid] = (time.monotonic(), future.result())
                self.cache.move_to_end(appid)
                while len(self.cache) > self.max_entries:
                    self.cache.popitem(last=False)
            if self.inflight.get(appid) is future:
                del self.inflight[appid]

    def get(self, appid: str) -> Snapshot:
        cached, future = self._future(appid)
        return cached if cached is not None else self._finish(appid, future)

    def _finish(self, appid, future):
        try:
            return future.result()
        finally:
            self._completed(appid, future)

    def get_many(self, appids: list[str]):
        pending = {appid: self._future(appid) for appid in appids}
        snapshots, issues = [], []
        for appid, (cached, future) in pending.items():
            try:
                snapshots.append(cached if cached is not None else self._finish(appid, future))
            except SteamError as exc:
                issues.append({"appid": appid, "message": str(exc)})
        return snapshots, issues


def selection() -> list[str]:
    items = json.loads((ROOT / "data/catalog/steam_appids.json").read_text(encoding="utf-8"))
    if (not isinstance(items, list) or not 1 <= len(items) <= 30
        or any(not isinstance(x, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", x) for x in items)
        or len(set(items)) != len(items)):
        raise ValueError("A seleção Steam deve conter de 1 a 30 AppIDs únicos.")
    return items


def normalize_game(snapshot: Snapshot, context: dict | None) -> dict:
    data = snapshot.data
    flags = data.get("platforms") if isinstance(data.get("platforms"), dict) else {}
    platforms = {}
    for name, flag, field in [("Windows", "windows", "pc_requirements"), ("macOS", "mac", "mac_requirements"), ("Linux", "linux", "linux_requirements")]:
        requirements = data.get(field)
        if not isinstance(requirements, dict):
            requirements = {}
        native = flags.get(flag)
        platforms[name] = {
            "native_support": native if type(native) is bool else None,
            **{level: requirements_block(requirements.get(level), context) for level in ("minimum", "recommended")},
        }

    def descriptions(field):
        rows = data.get(field)
        return sorted({r["description"].strip() for r in rows
            if isinstance(r, dict) and isinstance(r.get("description"), str) and r["description"].strip()}) if isinstance(rows, list) else []

    date = data.get("release_date") or {}
    year = re.search(r"\b(?:19|20)[0-9]{2}\b", str(date.get("date", ""))) if isinstance(date, dict) else None
    developers = data.get("developers")
    developer = ", ".join(x for x in developers if isinstance(x, str)) if isinstance(developers, list) else ""
    image = data.get("header_image")
    parsed = urlsplit(image) if isinstance(image, str) else None
    image = image if parsed and parsed.scheme == "https" and parsed.hostname and parsed.hostname.endswith((".steamstatic.com", ".steamcdn-a.akamaihd.net")) else None
    price = data.get("price_overview")
    price_text = price.get("final_formatted") if isinstance(price, dict) else None
    appid = str(data["steam_appid"])
    return {
        "id": appid, "title": data["name"], "developer": developer,
        "year": int(year[0]) if year else None,
        "genres": descriptions("genres"), "features": descriptions("categories"),
        "summary": clean_html(data.get("short_description", "")) if isinstance(data.get("short_description"), str) else "",
        "image_url": image, "store_url": f"https://store.steampowered.com/app/{appid}/",
        "price_text": "Gratuito" if data.get("is_free") is True else price_text,
        "platforms": platforms, "source": snapshot.source,
        "hardware_source": {key: context[key] for key in ("catalog_sha256", "aliases_sha256", "hardware_sha256")} if context else None,
    }
