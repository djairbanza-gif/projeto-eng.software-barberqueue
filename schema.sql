-- Esquema do banco de dados - BarberQueue (SQLite)
-- Valores monetários são guardados em CENTAVOS (inteiro) para evitar erros de arredondamento.

CREATE TABLE IF NOT EXISTS clientes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    telefone    TEXT,
    criado_em   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS servicos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL UNIQUE,
    preco_centavos  INTEGER NOT NULL CHECK (preco_centavos > 0),
    ativo           INTEGER NOT NULL DEFAULT 1      -- 1 = ativo, 0 = removido (exclusão lógica)
);

-- Cada linha é um "ticket" da fila. A ordem FIFO é dada pelo id (ordem de chegada).
CREATE TABLE IF NOT EXISTS atendimentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id),
    status          TEXT    NOT NULL
                    CHECK (status IN ('aguardando','em_atendimento','concluido','cancelado')),
    entrada_em      TEXT    NOT NULL,
    inicio_em       TEXT,
    fim_em          TEXT,
    total_centavos  INTEGER NOT NULL DEFAULT 0
);

-- Serviços escolhidos em cada atendimento (guarda o preço no momento da entrada na fila).
CREATE TABLE IF NOT EXISTS atendimento_servicos (
    atendimento_id  INTEGER NOT NULL REFERENCES atendimentos(id) ON DELETE CASCADE,
    servico_id      INTEGER NOT NULL REFERENCES servicos(id),
    preco_centavos  INTEGER NOT NULL,
    PRIMARY KEY (atendimento_id, servico_id)
);

CREATE INDEX IF NOT EXISTS idx_atend_status ON atendimentos(status, id);
