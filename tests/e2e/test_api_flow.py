"""Teste de ponta a ponta pela API: cadastro, perfil, recomendações, saída e nova entrada.

Roda contra a pilha local já no ar (Neo4j com o catálogo carregado e a API):

    docker compose up -d neo4j api
    GAMECOMPASS_E2E=1 python3 tests/e2e/test_api_flow.py        # Linux/macOS
    $env:GAMECOMPASS_E2E=1; python tests/e2e/test_api_flow.py   # PowerShell

Usa só a biblioteca padrão. Sem GAMECOMPASS_E2E=1 todos os testes são ignorados, então
`unittest discover` e o CI nunca o executam por engano.

O teste cria uma conta descartável (e-mail e senha aleatórios, a senha nunca é impressa) e
a remove no final pelo contêiner do Neo4j. Se o Docker não estiver disponível, imprime a
consulta Cypher para apagar a conta à mão.

Variáveis opcionais: GAMECOMPASS_API (padrão http://127.0.0.1:8000) e
GAMECOMPASS_NEO4J_CONTAINER (padrão gamecompass-neo4j).
"""

import http.cookiejar
import json
import os
import secrets
import subprocess
import unittest
import urllib.error
import urllib.request

API = os.getenv("GAMECOMPASS_API", "http://127.0.0.1:8000").rstrip("/")
CONTAINER = os.getenv("GAMECOMPASS_NEO4J_CONTAINER", "gamecompass-neo4j")
ENABLED = os.getenv("GAMECOMPASS_E2E") == "1"
# Os navegadores enviam o Origin do site; a API só aceita escrita de origens conhecidas.
ORIGIN = "http://127.0.0.1:5173"

# Três jogos do catálogo e uma máquina real do índice de hardware.
ANCHORS = ["1091500", "292030", "1245620"]  # Cyberpunk 2077, The Witcher 3, Elden Ring
CPU = "AMD Ryzen 5 3600"
GPU = "NVIDIA GeForce RTX 3060 12GB"
DRAGONS_DOGMA_2 = "2054970"


def hardware(windows="11", gpu=GPU):
    return {"cpuId": CPU, "gpuId": gpu, "ramGb": 16, "os": "Windows", "windowsVersion": windows}


def profile(windows="11"):
    return {"anchorIds": ANCHORS, "genres": ["RPG"], "themes": ["Fantasia"], "hardware": hardware(windows)}


@unittest.skipUnless(ENABLED, "Defina GAMECOMPASS_E2E=1 com a pilha local no ar para executar.")
class ApiFlowTests(unittest.TestCase):
    email = ""
    password = ""
    opener = None

    @classmethod
    def setUpClass(cls):
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        try:
            status, _ = cls.call("GET", "/health")
        except OSError as exc:
            raise unittest.SkipTest(f"API indisponível em {API}: {exc}") from exc
        if status != 200:
            raise unittest.SkipTest(f"API em {API} respondeu {status} em /health.")
        cls.email = f"e2e-{secrets.token_hex(5)}@exemplo.test"
        cls.password = secrets.token_urlsafe(24)

    @classmethod
    def tearDownClass(cls):
        if not cls.email:
            return
        query = f'MATCH (u:User {{email: "{cls.email}"}}) OPTIONAL MATCH (u)-[:HAS_SESSION]->(s:Session) DETACH DELETE u, s'
        script = f'cypher-shell -u "${{NEO4J_AUTH%%/*}}" -p "${{NEO4J_AUTH#*/}}" \'{query}\''
        try:
            subprocess.run(["docker", "exec", CONTAINER, "sh", "-c", script], check=True, capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            print(f"\nNão foi possível apagar a conta de teste. Rode no Neo4j Browser:\n  {query}")

    @classmethod
    def call(cls, method, path, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(API + path, data=data, method=method)
        request.add_header("Origin", ORIGIN)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            request.add_header(key, value)
        try:
            with cls.opener.open(request, timeout=30) as response:
                return response.status, json.loads(response.read() or b"null")
        except urllib.error.HTTPError as error:
            raw = error.read()
            error.close()
            try:
                return error.code, json.loads(raw or b"null")
            except ValueError:
                return error.code, raw.decode(errors="replace")

    # Os passos dependem uns dos outros; o prefixo numérico fixa a ordem de execução.

    def test_01_catalogo_carregado_no_neo4j(self):
        status, games = self.call("GET", "/api/games?appids=" + ",".join(ANCHORS))
        self.assertEqual(status, 200)
        self.assertEqual(len(games["items"]), 3)
        self.assertEqual(games["source"], "neo4j", "O catálogo de jogos não está carregado no Neo4j.")
        status, catalog = self.call("GET", "/api/hardware")
        self.assertEqual(status, 200)
        names = {part["id"] for kind in ("CPU", "GPU") for part in catalog[kind]}
        self.assertIn(CPU, names)
        self.assertIn(GPU, names)

    def test_02_cadastro_abre_sessao_com_perfil_vazio(self):
        status, account = self.call("POST", "/api/auth/register",
                                    {"name": "Teste E2E", "email": self.email, "password": self.password})
        self.assertEqual(status, 201)
        self.assertEqual(account["email"], self.email)
        status, me = self.call("GET", "/api/auth/me")
        self.assertEqual(status, 200)
        self.assertEqual((me["genres"], me["themes"], me["anchorIds"], me["hardware"]), ([], [], [], None))
        self.assertNotIn("password", json.dumps(me).lower())

    def test_03_mesmo_email_nao_cadastra_duas_vezes(self):
        status, body = self.call("POST", "/api/auth/register",
                                 {"name": "Outro", "email": self.email, "password": self.password})
        self.assertEqual(status, 409, body)

    def test_04_perfil_e_gravado_no_servidor(self):
        status, _ = self.call("PATCH", "/api/me/profile", profile())
        self.assertEqual(status, 200)
        status, me = self.call("GET", "/api/auth/me")
        self.assertEqual(status, 200)
        self.assertEqual(me["genres"], ["RPG"])
        self.assertEqual(me["themes"], ["Fantasia"])
        self.assertEqual(me["anchorIds"], ANCHORS)
        self.assertEqual(me["hardware"]["gpuId"], GPU)

    def test_05_recomendacoes_respeitam_as_regras_do_motor(self):
        status, result = self.call("POST", "/api/recommendations", profile())
        self.assertEqual(status, 200, result)
        calculation = result["calculation"]
        self.assertEqual(calculation["engine_version"], "rules_v1")
        self.assertTrue(calculation["hardware_sha256"])
        groups = {name: result[name] for name in ("items", "pending", "excluded")}
        self.assertGreater(sum(len(group) for group in groups.values()), 0, "Nenhuma recomendação para um perfil completo.")
        listed = [match["game"]["id"] for group in groups.values() for match in group]
        self.assertFalse(set(listed) & set(ANCHORS), "Os jogos âncora não podem aparecer como recomendação.")
        self.assertEqual(len(listed), len(set(listed)), "Um jogo apareceu em mais de um grupo.")
        for group in groups.values():
            for match in group:
                self.assertGreaterEqual(match["affinity"], calculation["minimum_affinity"])
        for match in groups["items"]:
            self.assertEqual(match["compatibility"], "compatible")
        for match in groups["excluded"]:
            self.assertEqual(match["compatibility"], "incompatible")

    def test_06_regressao_dragons_dogma_2_com_rtx_3060_12gb(self):
        # A RX 6600 XT (alternativa do requisito recomendado) está na classe 300, a mesma da RTX 3060 12GB.
        status, body = self.call("POST", f"/api/games/{DRAGONS_DOGMA_2}/comparison", profile("11"))
        self.assertEqual(status, 200, body)
        match = body["match"]
        self.assertEqual(match["compatibility"], "compatible")
        self.assertEqual(match["meets"], "recommended")

    def test_07_dragons_dogma_2_exige_windows_11(self):
        status, body = self.call("POST", f"/api/games/{DRAGONS_DOGMA_2}/comparison", profile("10"))
        self.assertEqual(status, 200, body)
        match = body["match"]
        self.assertEqual(match["compatibility"], "incompatible")
        os_check = next(check for check in match["checks"] if check["label"] == "Sistema operacional")
        self.assertIs(os_check["ok"], False)

    def test_08_perfil_incompleto_e_rejeitado_antes_do_calculo(self):
        incomplete = {**profile(), "anchorIds": ANCHORS[:2]}
        status, _ = self.call("POST", "/api/recommendations", incomplete)
        self.assertEqual(status, 422)

    def test_09_sair_encerra_a_sessao(self):
        status, _ = self.call("POST", "/api/auth/logout", {})
        self.assertEqual(status, 200)
        status, _ = self.call("GET", "/api/auth/me")
        self.assertEqual(status, 401)

    def test_10_senha_errada_nao_entra(self):
        status, _ = self.call("POST", "/api/auth/login", {"email": self.email, "password": self.password + "x"})
        self.assertEqual(status, 401)

    def test_11_nova_entrada_encontra_o_perfil_salvo(self):
        status, _ = self.call("POST", "/api/auth/login", {"email": self.email, "password": self.password})
        self.assertEqual(status, 200)
        status, me = self.call("GET", "/api/auth/me")
        self.assertEqual(status, 200)
        self.assertEqual(me["anchorIds"], ANCHORS)
        self.assertEqual(me["hardware"]["cpuId"], CPU)


if __name__ == "__main__":
    unittest.main(verbosity=2)
