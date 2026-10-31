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

from .hardware import requirements_block, clean_html


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

    def _request_json(self, url: str):
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
            if not isinstance(payload, dict):
                raise SteamError("A Steam retornou uma resposta inválida.")
            source = {"source_url": url,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "response_sha256": hashlib.sha256(raw).hexdigest()}
            return payload, source
        except (httpx.HTTPError, ValueError, UnicodeError) as exc:
            raise SteamError("Não foi possível consultar a loja Steam. Tente novamente.") from exc

    def _fetch(self, appid: str) -> Snapshot:
        params = {"appids": appid, "cc": "br", "l": "portuguese"}
        url = "https://store.steampowered.com/api/appdetails?" + urlencode(params)
        payload, source = self._request_json(url)
        entry = payload.get(appid)
        if not isinstance(entry, dict) or entry.get("success") is not True:
            raise SteamError("A Steam não disponibilizou esse jogo nesta região.", 404)
        data = entry.get("data")
        if (not isinstance(data, dict) or str(data.get("steam_appid")) != appid
            or not isinstance(data.get("name"), str) or not data["name"].strip()):
            raise SteamError("A Steam retornou identificação inválida.")
        if data.get("type") != "game":
            raise SteamError("Esse resultado não é um jogo base da loja Steam.", 404)
        return Snapshot(data, source)

    def _fetch_search(self, query: str) -> dict:
        url = "https://store.steampowered.com/api/storesearch/?" + urlencode({
            "term": query, "l": "portuguese", "cc": "br"})
        payload, source = self._request_json(url)
        rows = payload.get("items")
        if not isinstance(rows, list):
            raise SteamError("A Steam retornou uma busca inválida.")
        items, seen = [], set()
        for row in rows:
            if not isinstance(row, dict) or row.get("type") != "app" or row.get("streamingvideo") is True:
                continue
            identifier = row.get("id")
            appid = str(identifier) if type(identifier) in (int, str) else ""
            name = row.get("name")
            if (not re.fullmatch(r"[1-9][0-9]{0,9}", appid) or not isinstance(name, str)
                or not name.strip() or appid in seen):
                continue
            items.append({"id": appid, "title": name.strip()})
            seen.add(appid)
            if len(items) == 20:
                break
        return {"items": items, "source": source}

    def search(self, query: str) -> dict:
        if not isinstance(query, str):
            raise SteamError("Informe o nome do jogo.", 422)
        query = " ".join(query.split())
        if not 2 <= len(query) <= 100:
            raise SteamError("Digite de 2 a 100 caracteres para pesquisar.", 422)
        key = "search:" + query.casefold()
        cached, future = self._cached_future(key, lambda: self._fetch_search(query))
        return cached if cached is not None else self._finish(key, future)

    def _fetch_featured(self) -> dict:
        url = "https://store.steampowered.com/api/featuredcategories/?" + urlencode({"l": "portuguese", "cc": "br"})
        payload, source = self._request_json(url)
        section = payload.get("top_sellers")
        if not isinstance(section, dict) or not isinstance(section.get("items"), list):
            raise SteamError("A Steam não disponibilizou candidatos nesta consulta.")
        appids = []
        for item in section["items"]:
            if not isinstance(item, dict) or type(item.get("type")) is not int or item["type"] != 0:
                continue
            identifier = item.get("id")
            appid = str(identifier) if type(identifier) in (int, str) else ""
            if re.fullmatch(r"[1-9][0-9]{0,9}", appid) and appid not in appids:
                appids.append(appid)
            if len(appids) == 12:
                break
        return {"appids": appids, "source": source}

    def featured(self) -> dict:
        cached, future = self._cached_future("featured", self._fetch_featured)
        return cached if cached is not None else self._finish("featured", future)

    def _future(self, appid: str):
        if not isinstance(appid, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", appid):
            raise SteamError("Identificador de jogo inválido.", 422)
        return self._cached_future(appid, lambda: self._fetch(appid))

    def _cached_future(self, key, loader):
        with self.lock:
            entry = self.cache.get(key)
            if entry and time.monotonic() - entry[0] < self.ttl:
                self.cache.move_to_end(key)
                return entry[1], None
            future = self.inflight.get(key)
            if future is None:
                if len(self.inflight) >= 32:
                    raise SteamError("Há muitas consultas em andamento. Tente novamente.", 503)
                future = self.pool.submit(loader)
                self.inflight[key] = future
                future.add_done_callback(lambda done: self._completed(key, done))
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


def game_preview(snapshot: Snapshot) -> dict:
    """Identidade e capa reais, sem processar requisitos ou consultar hardware."""
    data = snapshot.data
    image = data.get("header_image")
    parsed = urlsplit(image) if isinstance(image, str) else None
    image = image if parsed and parsed.scheme == "https" and parsed.hostname and parsed.hostname.endswith((".steamstatic.com", ".steamcdn-a.akamaihd.net")) else None
    appid = str(data["steam_appid"])
    return {"id": appid, "title": data["name"], "image_url": image,
            "store_url": f"https://store.steampowered.com/app/{appid}/"}


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
    price = data.get("price_overview")
    price_text = price.get("final_formatted") if isinstance(price, dict) else None
    return {
        **game_preview(snapshot), "developer": developer,
        "year": int(year[0]) if year else None,
        "genres": descriptions("genres"), "themes": [], "themes_status": "pending",
        "summary": clean_html(data.get("short_description", "")) if isinstance(data.get("short_description"), str) else "",
        "price_text": "Gratuito" if data.get("is_free") is True else price_text,
        "platforms": platforms, "source": snapshot.source,
        "hardware_source": {key: context[key] for key in ("catalog_sha256", "aliases_sha256", "hardware_sha256")} if context else None,
    }
