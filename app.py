"""BarberQueue - API REST do Sistema de Gerenciamento de Barbearia (Flask + SQLite)."""
import os
import sqlite3

from flask import Flask, g, jsonify, request, send_from_directory

from .database import DEFAULT_DB, agora, conectar, iniciar_banco

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


# ---------------------------------------------------------------- utilidades
def reais(centavos):
    return round(centavos / 100, 2)


def para_centavos(valor):
    """Converte um preço em reais (número ou texto '35,50') para centavos. Lança ValueError se inválido."""
    if isinstance(valor, str):
        valor = valor.replace(",", ".").strip()
    numero = float(valor)
    centavos = int(round(numero * 100))
    if centavos <= 0:
        raise ValueError("preço deve ser maior que zero")
    return centavos


def erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def create_app(caminho_db=None):
    app = Flask(__name__, static_folder=None)
    app.config["DB_PATH"] = caminho_db or os.environ.get("BARBEARIA_DB", DEFAULT_DB)
    iniciar_banco(app.config["DB_PATH"])

    # ------------------------------------------------ conexão por requisição
    def db():
        if "db" not in g:
            g.db = conectar(app.config["DB_PATH"])
        return g.db

    @app.teardown_appcontext
    def fechar_db(_exc):
        conexao = g.pop("db", None)
        if conexao is not None:
            conexao.close()

    # ------------------------------------------------------------ serializadores
    def serializar_cliente(r):
        return {"id": r["id"], "nome": r["nome"], "telefone": r["telefone"] or ""}

    def serializar_servico(r):
        return {"id": r["id"], "nome": r["nome"], "preco": reais(r["preco_centavos"])}

    def serializar_atendimento(r):
        servicos = db().execute(
            """SELECT s.id, s.nome, x.preco_centavos FROM atendimento_servicos x
               JOIN servicos s ON s.id = x.servico_id WHERE x.atendimento_id = ?""",
            (r["id"],),
        ).fetchall()
        return {
            "id": r["id"],
            "cliente_id": r["cliente_id"],
            "cliente": r["cliente_nome"],
            "status": r["status"],
            "entrada_em": r["entrada_em"],
            "inicio_em": r["inicio_em"],
            "fim_em": r["fim_em"],
            "servicos": [{"id": s["id"], "nome": s["nome"], "preco": reais(s["preco_centavos"])} for s in servicos],
            "total": reais(r["total_centavos"]),
        }

    def buscar_atendimento(atendimento_id):
        return db().execute(
            """SELECT a.*, c.nome AS cliente_nome FROM atendimentos a
               JOIN clientes c ON c.id = a.cliente_id WHERE a.id = ?""",
            (atendimento_id,),
        ).fetchone()

    # ------------------------------------------------------------------ frontend
    @app.get("/")
    def home():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:arquivo>")
    def estaticos(arquivo):
        return send_from_directory(FRONTEND_DIR, arquivo)

    # ------------------------------------------------------------------ CLIENTES (RF01, RF02)
    @app.post("/api/clientes")
    def criar_cliente():
        dados = request.get_json(silent=True) or {}
        nome = (dados.get("nome") or "").strip()
        telefone = (dados.get("telefone") or "").strip()
        if len(nome) < 2:
            return erro("Informe o nome do cliente (mínimo 2 caracteres).")
        cur = db().execute(
            "INSERT INTO clientes (nome, telefone, criado_em) VALUES (?, ?, ?)",
            (nome, telefone, agora()),
        )
        db().commit()
        novo = db().execute("SELECT * FROM clientes WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(serializar_cliente(novo)), 201

    @app.get("/api/clientes")
    def listar_clientes():
        busca = (request.args.get("q") or "").strip()
        linhas = db().execute(
            "SELECT * FROM clientes WHERE nome LIKE ? ORDER BY nome COLLATE NOCASE",
            (f"%{busca}%",),
        ).fetchall()
        return jsonify([serializar_cliente(r) for r in linhas])

    @app.delete("/api/clientes/<int:cliente_id>")
    def remover_cliente(cliente_id):
        usado = db().execute("SELECT 1 FROM atendimentos WHERE cliente_id = ? LIMIT 1", (cliente_id,)).fetchone()
        if usado:
            return erro("Cliente possui histórico de atendimentos e não pode ser removido.", 409)
        cur = db().execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        db().commit()
        if cur.rowcount == 0:
            return erro("Cliente não encontrado.", 404)
        return "", 204

    # ------------------------------------------------------------------ SERVIÇOS (RF03)
    @app.get("/api/servicos")
    def listar_servicos():
        linhas = db().execute("SELECT * FROM servicos WHERE ativo = 1 ORDER BY nome").fetchall()
        return jsonify([serializar_servico(r) for r in linhas])

    @app.post("/api/servicos")
    def criar_servico():
        dados = request.get_json(silent=True) or {}
        nome = (dados.get("nome") or "").strip()
        if len(nome) < 2:
            return erro("Informe o nome do serviço.")
        try:
            centavos = para_centavos(dados.get("preco"))
        except (ValueError, TypeError):
            return erro("Informe um preço válido (maior que zero).")
        try:
            cur = db().execute(
                "INSERT INTO servicos (nome, preco_centavos) VALUES (?, ?)", (nome, centavos)
            )
        except sqlite3.IntegrityError:
            # nome já existe: se estava removido, reativa com o novo preço
            existente = db().execute("SELECT * FROM servicos WHERE nome = ?", (nome,)).fetchone()
            if existente and not existente["ativo"]:
                db().execute("UPDATE servicos SET ativo = 1, preco_centavos = ? WHERE id = ?", (centavos, existente["id"]))
                db().commit()
                return jsonify(serializar_servico(db().execute("SELECT * FROM servicos WHERE id = ?", (existente["id"],)).fetchone())), 201
            return erro("Já existe um serviço com esse nome.", 409)
        db().commit()
        novo = db().execute("SELECT * FROM servicos WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(serializar_servico(novo)), 201

    @app.put("/api/servicos/<int:servico_id>")
    def editar_servico(servico_id):
        dados = request.get_json(silent=True) or {}
        atual = db().execute("SELECT * FROM servicos WHERE id = ? AND ativo = 1", (servico_id,)).fetchone()
        if not atual:
            return erro("Serviço não encontrado.", 404)
        nome = (dados.get("nome") or atual["nome"]).strip()
        try:
            centavos = para_centavos(dados["preco"]) if "preco" in dados else atual["preco_centavos"]
        except (ValueError, TypeError):
            return erro("Informe um preço válido (maior que zero).")
        try:
            db().execute("UPDATE servicos SET nome = ?, preco_centavos = ? WHERE id = ?", (nome, centavos, servico_id))
        except sqlite3.IntegrityError:
            return erro("Já existe um serviço com esse nome.", 409)
        db().commit()
        return jsonify(serializar_servico(db().execute("SELECT * FROM servicos WHERE id = ?", (servico_id,)).fetchone()))

    @app.delete("/api/servicos/<int:servico_id>")
    def remover_servico(servico_id):
        # Exclusão lógica: preserva o histórico dos atendimentos já realizados.
        cur = db().execute("UPDATE servicos SET ativo = 0 WHERE id = ? AND ativo = 1", (servico_id,))
        db().commit()
        if cur.rowcount == 0:
            return erro("Serviço não encontrado.", 404)
        return "", 204

    # ------------------------------------------------------------------ FILA FIFO (RF04, RF05, RF06)
    @app.get("/api/fila")
    def ver_fila():
        """Retorna quem está sendo atendido e a fila de espera na ordem de chegada (FIFO)."""
        linhas = db().execute(
            """SELECT a.*, c.nome AS cliente_nome FROM atendimentos a
               JOIN clientes c ON c.id = a.cliente_id
               WHERE a.status IN ('aguardando', 'em_atendimento')
               ORDER BY a.id ASC"""
        ).fetchall()
        itens = [serializar_atendimento(r) for r in linhas]
        em_atendimento = next((i for i in itens if i["status"] == "em_atendimento"), None)
        aguardando = [i for i in itens if i["status"] == "aguardando"]
        for posicao, item in enumerate(aguardando, start=1):
            item["posicao"] = posicao
        return jsonify({"em_atendimento": em_atendimento, "aguardando": aguardando})

    @app.post("/api/fila")
    def entrar_na_fila():
        """ENQUEUE: coloca o cliente no FINAL da fila com os serviços escolhidos."""
        dados = request.get_json(silent=True) or {}
        cliente_id = dados.get("cliente_id")
        ids = dados.get("servicos") or []
        if not isinstance(ids, list) or not ids:
            return erro("Selecione pelo menos um serviço.")
        cliente = db().execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        if not cliente:
            return erro("Cliente não encontrado.", 404)
        ja_na_fila = db().execute(
            "SELECT 1 FROM atendimentos WHERE cliente_id = ? AND status IN ('aguardando','em_atendimento')",
            (cliente_id,),
        ).fetchone()
        if ja_na_fila:
            return erro("Este cliente já está na fila.", 409)
        servicos = []
        for sid in dict.fromkeys(ids):  # remove duplicados mantendo a ordem
            s = db().execute("SELECT * FROM servicos WHERE id = ? AND ativo = 1", (sid,)).fetchone()
            if not s:
                return erro(f"Serviço {sid} não encontrado.", 404)
            servicos.append(s)
        total = sum(s["preco_centavos"] for s in servicos)
        cur = db().execute(
            "INSERT INTO atendimentos (cliente_id, status, entrada_em, total_centavos) VALUES (?, 'aguardando', ?, ?)",
            (cliente_id, agora(), total),
        )
        db().executemany(
            "INSERT INTO atendimento_servicos (atendimento_id, servico_id, preco_centavos) VALUES (?, ?, ?)",
            [(cur.lastrowid, s["id"], s["preco_centavos"]) for s in servicos],
        )
        db().commit()
        return jsonify(serializar_atendimento(buscar_atendimento(cur.lastrowid))), 201

    @app.post("/api/fila/proximo")
    def chamar_proximo():
        """DEQUEUE: chama o cliente mais antigo da fila (primeiro a entrar = primeiro a sair)."""
        if db().execute("SELECT 1 FROM atendimentos WHERE status = 'em_atendimento'").fetchone():
            return erro("Já existe um atendimento em andamento. Finalize-o antes de chamar o próximo.", 409)
        primeiro = db().execute(
            "SELECT id FROM atendimentos WHERE status = 'aguardando' ORDER BY id ASC LIMIT 1"
        ).fetchone()
        if not primeiro:
            return erro("A fila está vazia.", 404)
        db().execute(
            "UPDATE atendimentos SET status = 'em_atendimento', inicio_em = ? WHERE id = ?",
            (agora(), primeiro["id"]),
        )
        db().commit()
        return jsonify(serializar_atendimento(buscar_atendimento(primeiro["id"])))

    @app.post("/api/fila/<int:atendimento_id>/finalizar")
    def finalizar(atendimento_id):
        a = buscar_atendimento(atendimento_id)
        if not a:
            return erro("Atendimento não encontrado.", 404)
        if a["status"] != "em_atendimento":
            return erro("Só é possível finalizar um atendimento em andamento.", 409)
        db().execute(
            "UPDATE atendimentos SET status = 'concluido', fim_em = ? WHERE id = ?", (agora(), atendimento_id)
        )
        db().commit()
        return jsonify(serializar_atendimento(buscar_atendimento(atendimento_id)))

    @app.delete("/api/fila/<int:atendimento_id>")
    def cancelar(atendimento_id):
        a = buscar_atendimento(atendimento_id)
        if not a:
            return erro("Atendimento não encontrado.", 404)
        if a["status"] != "aguardando":
            return erro("Só é possível cancelar quem ainda está aguardando.", 409)
        db().execute("UPDATE atendimentos SET status = 'cancelado' WHERE id = ?", (atendimento_id,))
        db().commit()
        return "", 204

    # ------------------------------------------------------------------ RELATÓRIO (RF07)
    @app.get("/api/relatorio")
    def relatorio():
        """Resumo: clientes atendidos, serviços realizados e faturamento. Filtro opcional ?data=AAAA-MM-DD."""
        data = (request.args.get("data") or "").strip()
        filtro, params = "", []
        if data:
            filtro, params = " AND substr(a.fim_em, 1, 10) = ?", [data]
        resumo = db().execute(
            f"""SELECT COUNT(*) AS clientes, COALESCE(SUM(a.total_centavos), 0) AS total
                FROM atendimentos a WHERE a.status = 'concluido'{filtro}""",
            params,
        ).fetchone()
        por_servico = db().execute(
            f"""SELECT s.nome, COUNT(*) AS quantidade, SUM(x.preco_centavos) AS total
                FROM atendimento_servicos x
                JOIN atendimentos a ON a.id = x.atendimento_id AND a.status = 'concluido'
                JOIN servicos s ON s.id = x.servico_id
                WHERE 1=1{filtro}
                GROUP BY s.id ORDER BY quantidade DESC, s.nome""",
            params,
        ).fetchall()
        return jsonify(
            {
                "data": data or None,
                "clientes_atendidos": resumo["clientes"],
                "servicos_realizados": sum(r["quantidade"] for r in por_servico),
                "faturamento_total": reais(resumo["total"]),
                "por_servico": [
                    {"nome": r["nome"], "quantidade": r["quantidade"], "total": reais(r["total"])} for r in por_servico
                ],
            }
        )

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
