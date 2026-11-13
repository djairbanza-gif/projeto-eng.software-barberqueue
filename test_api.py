"""Testes automatizados da API (rodam com: python -m unittest -v)."""
import os
import tempfile
import unittest

from backend.app import create_app


class BaseTeste(unittest.TestCase):
    def setUp(self):
        # Cada teste usa um banco temporário limpo
        self.arquivo = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.arquivo.close()
        self.app = create_app(self.arquivo.name)
        self.c = self.app.test_client()

    def tearDown(self):
        os.unlink(self.arquivo.name)

    # atalhos
    def cliente(self, nome="João", tel="82999990000"):
        return self.c.post("/api/clientes", json={"nome": nome, "telefone": tel}).get_json()

    def servicos(self):
        return {s["nome"]: s for s in self.c.get("/api/servicos").get_json()}

    def entrar(self, cliente, *nomes):
        sv = self.servicos()
        return self.c.post("/api/fila", json={"cliente_id": cliente["id"], "servicos": [sv[n]["id"] for n in nomes]})


class TestClientes(BaseTeste):
    def test_ct01_cadastrar_e_listar_cliente(self):
        r = self.c.post("/api/clientes", json={"nome": "Carlos Silva", "telefone": "82988887777"})
        self.assertEqual(r.status_code, 201)
        nomes = [c["nome"] for c in self.c.get("/api/clientes").get_json()]
        self.assertIn("Carlos Silva", nomes)

    def test_ct02_rejeita_cliente_sem_nome(self):
        r = self.c.post("/api/clientes", json={"nome": " ", "telefone": "1"})
        self.assertEqual(r.status_code, 400)

    def test_busca_cliente_por_nome(self):
        self.cliente("Ana"); self.cliente("Bruno")
        res = self.c.get("/api/clientes?q=bru").get_json()
        self.assertEqual([c["nome"] for c in res], ["Bruno"])


class TestServicos(BaseTeste):
    def test_ct03_cadastrar_servico_com_preco(self):
        r = self.c.post("/api/servicos", json={"nome": "Pigmentação", "preco": "40,50"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["preco"], 40.5)

    def test_ct04_rejeita_preco_invalido(self):
        for preco in (0, -5, "abc", None):
            r = self.c.post("/api/servicos", json={"nome": "X Teste", "preco": preco})
            self.assertEqual(r.status_code, 400, preco)

    def test_servico_duplicado(self):
        r = self.c.post("/api/servicos", json={"nome": "Barba", "preco": 10})
        self.assertEqual(r.status_code, 409)

    def test_editar_e_remover_servico(self):
        sid = self.servicos()["Barba"]["id"]
        r = self.c.put(f"/api/servicos/{sid}", json={"preco": 30})
        self.assertEqual(r.get_json()["preco"], 30.0)
        self.assertEqual(self.c.delete(f"/api/servicos/{sid}").status_code, 204)
        self.assertNotIn("Barba", self.servicos())


class TestFilaFIFO(BaseTeste):
    def test_ct05_ordem_fifo(self):
        """Primeiro a entrar deve ser o primeiro a ser atendido."""
        a, b, c = self.cliente("Ana"), self.cliente("Bruno"), self.cliente("Caio")
        for cli in (a, b, c):
            self.assertEqual(self.entrar(cli, "Barba").status_code, 201)
        ordem = []
        for _ in range(3):
            atendido = self.c.post("/api/fila/proximo").get_json()
            ordem.append(atendido["cliente"])
            self.c.post(f"/api/fila/{atendido['id']}/finalizar")
        self.assertEqual(ordem, ["Ana", "Bruno", "Caio"])

    def test_posicoes_da_fila(self):
        for n in ("Ana", "Bruno"):
            self.entrar(self.cliente(n), "Barba")
        fila = self.c.get("/api/fila").get_json()
        self.assertEqual([(i["cliente"], i["posicao"]) for i in fila["aguardando"]], [("Ana", 1), ("Bruno", 2)])

    def test_ct06_total_calculado_corretamente(self):
        cli = self.cliente()
        r = self.entrar(cli, "Corte de cabelo", "Barba").get_json()
        self.assertEqual(r["total"], 60.0)  # 35,00 + 25,00

    def test_cliente_nao_entra_duas_vezes(self):
        cli = self.cliente()
        self.entrar(cli, "Barba")
        self.assertEqual(self.entrar(cli, "Barba").status_code, 409)

    def test_exige_ao_menos_um_servico(self):
        cli = self.cliente()
        r = self.c.post("/api/fila", json={"cliente_id": cli["id"], "servicos": []})
        self.assertEqual(r.status_code, 400)

    def test_fila_vazia_ao_chamar_proximo(self):
        self.assertEqual(self.c.post("/api/fila/proximo").status_code, 404)

    def test_nao_chama_proximo_com_atendimento_em_andamento(self):
        self.entrar(self.cliente("Ana"), "Barba"); self.entrar(self.cliente("Bruno"), "Barba")
        self.c.post("/api/fila/proximo")
        self.assertEqual(self.c.post("/api/fila/proximo").status_code, 409)

    def test_cancelar_quem_aguarda(self):
        a = self.entrar(self.cliente("Ana"), "Barba").get_json()
        self.assertEqual(self.c.delete(f"/api/fila/{a['id']}").status_code, 204)
        self.assertEqual(self.c.get("/api/fila").get_json()["aguardando"], [])

    def test_preco_historico_nao_muda_apos_reajuste(self):
        """O total já registrado deve ser preservado se o preço do serviço mudar depois."""
        sv = self.servicos()["Barba"]
        a = self.entrar(self.cliente(), "Barba").get_json()
        self.c.put(f"/api/servicos/{sv['id']}", json={"preco": 99})
        fila = self.c.get("/api/fila").get_json()
        self.assertEqual(fila["aguardando"][0]["total"], a["total"])


class TestRelatorio(BaseTeste):
    def test_ct07_relatorio_de_faturamento(self):
        for nome, servs in (("Ana", ("Corte de cabelo",)), ("Bruno", ("Corte de cabelo", "Barba"))):
            self.entrar(self.cliente(nome), *servs)
            at = self.c.post("/api/fila/proximo").get_json()
            self.c.post(f"/api/fila/{at['id']}/finalizar")
        self.entrar(self.cliente("Caio"), "Sobrancelha")  # continua na fila: não conta
        rel = self.c.get("/api/relatorio").get_json()
        self.assertEqual(rel["clientes_atendidos"], 2)
        self.assertEqual(rel["servicos_realizados"], 3)
        self.assertEqual(rel["faturamento_total"], 95.0)  # 35 + (35 + 25)

    def test_relatorio_vazio(self):
        rel = self.c.get("/api/relatorio").get_json()
        self.assertEqual((rel["clientes_atendidos"], rel["faturamento_total"]), (0, 0))

    def test_cliente_com_historico_nao_pode_ser_removido(self):
        cli = self.cliente(); self.entrar(cli, "Barba")
        self.assertEqual(self.c.delete(f"/api/clientes/{cli['id']}").status_code, 409)


if __name__ == "__main__":
    unittest.main()
