"""Mede o tempo de resposta e o comportamento sob carga da API do GameCompass (RNF10).

Só biblioteca padrão. Cria uma conta descartável, preenche o perfil, mede e apaga a conta
do Neo4j no fim (via `docker exec gamecompass-neo4j`).

1. Tempo de resposta: N chamadas em sequência a cada endpoint usado pelo frontend.
   - Endpoints servidos pelo Neo4j: N chamadas (padrão 50).
   - Endpoints que consultam a Steam ao vivo (busca, sugestões de âncora): poucas chamadas
     (padrão 5), para não sobrecarregar um serviço de terceiros. O tempo deles depende da Steam.
2. Carga: clientes simultâneos (padrão 1, 5, 10 e 20) chamando POST /api/recommendations
   pelo tempo fixado (padrão 15 s por nível), cada um com conexão HTTP persistente.

Uso:
  python3 backend/perf/measure_api.py [--base http://127.0.0.1:8000] [--out resultado.json]
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import platform
import secrets
import statistics
import subprocess
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

ORIGIN = "http://127.0.0.1:5173"  # a API só aceita escrita vinda do frontend
ANCHORS = ["1091500", "292030", "1245620"]  # Cyberpunk 2077, The Witcher 3, ELDEN RING
HARDWARE = {"cpuId": "AMD Ryzen 5 3600", "gpuId": "NVIDIA GeForce RTX 3060 12GB", "ramGb": 16,
            "os": "Windows", "windowsVersion": "11"}
PROFILE = {"anchorIds": ANCHORS, "genres": ["RPG"], "themes": ["Fantasia"], "hardware": HARDWARE}


class Client:
    """Uma conexão HTTP persistente com o cookie de sessão."""

    def __init__(self, base: str, cookie: str | None = None):
        parts = urlsplit(base)
        self.conn = http.client.HTTPConnection(parts.hostname, parts.port or 80, timeout=60)
        self.cookie = cookie

    def call(self, method: str, path: str, body: dict | None = None, retry: bool = True) -> tuple[int, float, bytes]:
        headers = {"Accept": "application/json", "Origin": ORIGIN}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if self.cookie:
            headers["Cookie"] = self.cookie
        start = time.perf_counter()
        try:
            self.conn.request(method, path, body=data, headers=headers)
            response = self.conn.getresponse()
            payload = response.read()
        except (http.client.HTTPException, OSError):
            # O uvicorn fecha conexões paradas há mais de 5 s; reabre e repete uma vez, sem contar a falha.
            self.conn.close()
            if retry:
                return self.call(method, path, body, retry=False)
            return 0, (time.perf_counter() - start) * 1000, b""
        elapsed = (time.perf_counter() - start) * 1000
        cookie = response.getheader("Set-Cookie")
        if cookie:
            self.cookie = cookie.split(";", 1)[0]
        return response.status, elapsed, payload


def cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as handle:
            return next(line.split(":", 1)[1].strip() for line in handle if line.startswith("model name"))
    except (OSError, StopIteration):
        return platform.processor() or platform.machine()


def summary(times: list[float]) -> dict:
    ordered = sorted(times)
    pick = lambda q: ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]
    return {"n": len(ordered), "min_ms": round(ordered[0], 1), "p50_ms": round(pick(0.50), 1),
            "p95_ms": round(pick(0.95), 1), "p99_ms": round(pick(0.99), 1), "max_ms": round(ordered[-1], 1),
            "mean_ms": round(statistics.fmean(ordered), 1)}


def latency(client: Client, method: str, path: str, body: dict | None, n: int, warmup: int = 3) -> dict:
    # A primeira chamada fica registrada à parte: nas rotas da Steam é a que vai à rede (as seguintes usam o cache da API).
    first_status, first_ms, _ = client.call(method, path, body)
    for _ in range(warmup - 1):
        client.call(method, path, body)
    times, errors = [], 0
    for _ in range(n):
        status, ms, _ = client.call(method, path, body)
        if 200 <= status < 300:
            times.append(ms)
        else:
            errors += 1
    return {"method": method, "path": path, "first_call_ms": round(first_ms, 1), "first_call_status": first_status,
            **summary(times), "errors": errors}


def docker_cpu() -> dict:
    """Uso de CPU e memória dos contêineres naquele instante (docker stats, 100% = um núcleo)."""
    try:
        out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.CPUPerc}} {{.MemUsage}}",
                              "gamecompass-api", "gamecompass-neo4j"], capture_output=True, text=True, timeout=30).stdout
        return {line.split()[0]: {"cpu": line.split()[1], "mem": line.split()[2]} for line in out.splitlines() if line.strip()}
    except (subprocess.SubprocessError, OSError, IndexError):
        return {}


def load(base: str, cookie: str, users: int, seconds: float) -> dict:
    deadline = time.perf_counter() + seconds
    times: list[float] = []
    errors = [0]
    lock = threading.Lock()

    def worker():
        client = Client(base, cookie)
        client.call("POST", "/api/recommendations", PROFILE)  # aquece a conexão, fora da conta
        local, failed = [], 0
        while time.perf_counter() < deadline:
            status, ms, _ = client.call("POST", "/api/recommendations", PROFILE)
            if status == 200:
                local.append(ms)
            else:
                failed += 1
        with lock:
            times.extend(local)
            errors[0] += failed

    threads = [threading.Thread(target=worker) for _ in range(users)]
    started = time.perf_counter()
    for thread in threads:
        thread.start()
    time.sleep(seconds / 2)
    sample = docker_cpu()  # amostra no meio do nível, com a carga já estabilizada
    for thread in threads:
        thread.join()
    wall = time.perf_counter() - started
    return {"users": users, "seconds": round(wall, 1), "ok": len(times), "errors": errors[0],
            "throughput_rps": round(len(times) / wall, 2), **summary(times), "docker_stats_mid": sample}


def delete_user(email: str) -> None:
    query = f'MATCH (u:User {{email: "{email}"}}) OPTIONAL MATCH (u)-[:HAS_SESSION]->(s:Session) DETACH DELETE u, s'
    command = f'cypher-shell -u "${{NEO4J_AUTH%%/*}}" -p "${{NEO4J_AUTH#*/}}" \'{query}\''
    try:
        subprocess.run(["docker", "exec", "gamecompass-neo4j", "sh", "-c", command], check=True,
                       capture_output=True, timeout=60)
    except (subprocess.SubprocessError, OSError):
        print("Não foi possível apagar a conta de medição. Rode no Neo4j:", query)


def container_info() -> dict:
    try:
        out = subprocess.run(["docker", "inspect", "gamecompass-api", "--format",
                              "{{.Config.Image}} {{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}"],
                             capture_output=True, text=True, timeout=20).stdout.split()
        return {"image": out[0], "cpu_limit": out[1] if out[1] != "0" else "sem limite",
                "memory_limit": out[2] if out[2] != "0" else "sem limite"}
    except (subprocess.SubprocessError, OSError, IndexError):
        return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--n", type=int, default=50, help="chamadas por endpoint do Neo4j")
    parser.add_argument("--n-steam", type=int, default=5, help="chamadas por endpoint que consulta a Steam")
    parser.add_argument("--users", default="1,5,10,20", help="níveis de clientes simultâneos")
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--out")
    parser.add_argument("--label", default="uvicorn, 1 processo (Dockerfile padrão)", help="descrição do servidor medido")
    parser.add_argument("--skip-latency", action="store_true", help="mede só a carga")
    args = parser.parse_args()

    email = f"medida-api-{secrets.token_hex(5)}@exemplo.test"
    client = Client(args.base)
    status, _, _ = client.call("POST", "/api/auth/register",
                               {"name": "Medição API", "email": email, "password": secrets.token_urlsafe(18)})
    if status != 201:
        raise SystemExit(f"Cadastro da conta de medição falhou (HTTP {status}).")
    try:
        status, _, _ = client.call("PATCH", "/api/me/profile", {k: v for k, v in PROFILE.items()})
        if status != 200:
            raise SystemExit(f"Perfil da conta de medição não foi salvo (HTTP {status}).")
        anonymous = Client(args.base)
        game = "1245620"
        endpoints = [
            ("Neo4j", client, "GET", "/health/neo4j", None),
            ("Neo4j", client, "GET", "/api/auth/me", None),
            ("Neo4j", client, "GET", "/api/hardware", None),
            ("Neo4j", client, "GET", f"/api/games?appids={','.join(ANCHORS)}", None),
            ("Neo4j", client, "GET", f"/api/games/{game}", None),
            ("Neo4j", client, "GET", "/api/me/interactions", None),
            ("Neo4j", client, "PATCH", "/api/me/profile", {"genres": ["RPG"]}),
            ("Neo4j", client, "POST", "/api/recommendations", PROFILE),
            ("Neo4j", anonymous, "POST", "/api/recommendations", PROFILE),
            ("Neo4j", client, "POST", f"/api/games/{game}/comparison", PROFILE),
            ("Steam", client, "GET", "/api/games/search?q=elden", None),
            ("Steam", client, "GET", "/api/games/anchors", None),
        ]
        results = []
        for source, who, method, path, body in ([] if args.skip_latency else endpoints):
            n = args.n if source == "Neo4j" else args.n_steam
            row = {"source": source, "session": "anônima" if who is anonymous else "logada",
                   **latency(who, method, path, body, n, warmup=3 if source == "Neo4j" else 1)}
            results.append(row)
            print(f"{source:5} {row['session']:7} {method:5} {path[:48]:48} 1ª {row['first_call_ms']:7.1f}  p50 {row['p50_ms']:7.1f}  "
                  f"p95 {row['p95_ms']:7.1f}  max {row['max_ms']:7.1f} ms  erros {row['errors']}")
        loads = []
        for users in [int(value) for value in args.users.split(",")]:
            row = load(args.base, client.cookie, users, args.seconds)
            loads.append(row)
            print(f"carga {users:3} clientes: {row['throughput_rps']:6.2f} req/s  p50 {row['p50_ms']:7.1f}  "
                  f"p95 {row['p95_ms']:7.1f}  max {row['max_ms']:7.1f} ms  ok {row['ok']}  erros {row['errors']}  {row['docker_stats_mid']}")
    finally:
        delete_user(email)

    report = {
        "measured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "base": args.base,
        "environment": {"client": f"Python {platform.python_version()}", "os": f"{platform.system()} {platform.release()}",
                        "cpu": cpu_model(), "cores": os.cpu_count(),
                        "api_server": args.label, "container": container_info(),
                        "note": "cliente, API e Neo4j na mesma máquina"},
        "latency": results,
        "load": {"endpoint": "POST /api/recommendations (sessão logada, perfil completo)",
                 "seconds_per_level": args.seconds, "levels": loads},
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")


if __name__ == "__main__":
    main()
