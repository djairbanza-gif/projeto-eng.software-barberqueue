"""Camada de acesso ao banco de dados (SQLite)."""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
DEFAULT_DB = os.path.join(os.path.dirname(BASE_DIR), "barbearia.db")

SERVICOS_INICIAIS = [
    ("Corte de cabelo", 3500),
    ("Barba", 2500),
    ("Corte + Barba", 5500),
    ("Sobrancelha", 1500),
]


def agora():
    """Data/hora atual em formato ISO (ex.: 2026-11-13T14:30:00)."""
    return datetime.now().isoformat(timespec="seconds")


def conectar(caminho):
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row          # permite acessar colunas pelo nome
    conn.execute("PRAGMA foreign_keys = ON")  # ativa integridade referencial
    return conn


def iniciar_banco(caminho):
    """Cria as tabelas (se não existirem) e cadastra serviços padrão na 1ª execução."""
    conn = conectar(caminho)
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    if conn.execute("SELECT COUNT(*) FROM servicos").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO servicos (nome, preco_centavos) VALUES (?, ?)", SERVICOS_INICIAIS
        )
    conn.commit()
    conn.close()
