# ✂ BarberQueue — Sistema de Gerenciamento de Barbearia

Sistema web para organizar o atendimento de uma barbearia: cadastro de clientes e serviços, **fila de atendimento no modelo FIFO** (primeiro a entrar, primeiro a ser atendido), cálculo automático do valor cobrado e relatório de faturamento.

> Projeto Final da disciplina de **Engenharia de Software** — UNIMA, Centro Universitário de Maceió.

## 🎯 Problema que o software resolve

Quando o atendimento de uma barbearia é controlado de forma manual (caderno, WhatsApp, memória), surgem problemas como: **fila desorganizada** (clientes furando a vez), **perda de informações**, dificuldade em saber **quais serviços foram feitos** e **erros no cálculo dos valores** cobrados. O BarberQueue centraliza tudo isso em um sistema simples: o cliente entra no final da fila, o barbeiro chama sempre o mais antigo, o total é calculado automaticamente e o dono acompanha o faturamento.

## 👥 Integrantes da equipe

| Nome | Responsabilidade principal |
|------|----------------------------|
| [Nome do integrante 1] | [ex.: Backend / API] |
| [Nome do integrante 2] | [ex.: Frontend] |
| [Nome do integrante 3] | [ex.: Banco de dados e testes] |
| [Nome do integrante 4] | [ex.: Documentação, UML e protótipos] |

## 🛠 Tecnologias utilizadas

- **Python 3.10+** e **Flask** — backend / API REST
- **SQLite** — banco de dados (arquivo local, sem instalação)
- **HTML5, CSS3 e JavaScript puro** — frontend responsivo (sem frameworks)
- **unittest** — testes automatizados
- **Trello** — gestão do projeto · **Draw.io/Graphviz/Matplotlib** — diagramas · **GitHub** — versionamento

## ✅ Principais funcionalidades

| Código | Funcionalidade |
|--------|----------------|
| RF01 | Cadastrar clientes |
| RF02 | Consultar/buscar clientes cadastrados |
| RF03 | Cadastrar, alterar preço e remover serviços |
| RF04 | Adicionar cliente à fila escolhendo serviços (total calculado automaticamente) |
| RF05 | Chamar o próximo cliente — sempre o mais antigo (**FIFO**) |
| RF06 | Finalizar atendimento |
| RF07 | Relatório: clientes atendidos, serviços realizados e faturamento total (com filtro por data) |
| RF08 | Visualizar a fila de espera com a posição de cada cliente |
| RF09 | Cancelar cliente que ainda está aguardando |

## 🚀 Instalação e execução

Pré-requisito: [Python 3.10+](https://www.python.org/downloads/) instalado.

```bash
# 1. Clone o repositório
git clone <URL-DO-REPOSITORIO>
cd barbearia

# 2. (Recomendado) crie um ambiente virtual
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o sistema
python run.py
```

Abra no navegador: **http://127.0.0.1:5000**

O banco de dados (`barbearia.db`) é criado automaticamente na primeira execução, já com 4 serviços de exemplo (corte, barba, corte + barba, sobrancelha).

### Executar os testes automatizados

```bash
python -m unittest -v
```

## 🗂 Estrutura do projeto

```
barbearia/
├── backend/
│   ├── app.py          # API REST (Flask) e regras de negócio
│   ├── database.py     # conexão e inicialização do SQLite
│   └── schema.sql      # criação das tabelas
├── frontend/
│   ├── index.html      # interface
│   ├── style.css       # estilos (responsivo)
│   └── app.js          # lógica da interface (consome a API)
├── tests/test_api.py   # 19 testes automatizados
├── docs/
│   ├── uml/            # casos de uso, classes, atividades, sequência, modelo ER
│   ├── prototipos/     # protótipos das telas (wireframes)
│   ├── screenshots/    # capturas de tela do sistema
│   └── Relatorio_Final.pdf
├── run.py              # ponto de entrada
└── requirements.txt
```

## 🔌 Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| POST / GET | `/api/clientes` | Cadastra / lista clientes (`?q=` busca por nome) |
| DELETE | `/api/clientes/<id>` | Remove cliente (se não tiver histórico) |
| GET / POST | `/api/servicos` | Lista / cadastra serviços |
| PUT / DELETE | `/api/servicos/<id>` | Altera preço / remove (exclusão lógica) |
| GET | `/api/fila` | Atendimento atual + fila de espera em ordem FIFO |
| POST | `/api/fila` | **Enqueue** — cliente entra no final da fila |
| POST | `/api/fila/proximo` | **Dequeue** — chama o cliente mais antigo |
| POST | `/api/fila/<id>/finalizar` | Finaliza o atendimento |
| DELETE | `/api/fila/<id>` | Cancela cliente que está aguardando |
| GET | `/api/relatorio` | Resumo de faturamento (`?data=AAAA-MM-DD`) |

## 🧠 Como a fila FIFO funciona

Cada cliente que entra na fila vira um registro em `atendimentos` com status `aguardando` e um `id` crescente. Para chamar o próximo, o sistema executa:

```sql
SELECT id FROM atendimentos WHERE status = 'aguardando' ORDER BY id ASC LIMIT 1;
```

Como o `id` cresce na ordem de chegada, o menor `id` é sempre o primeiro que entrou — o comportamento exato de uma fila FIFO, **com a vantagem de persistir**: se o sistema for fechado, a fila continua no banco.

## 🖼 Capturas de tela

| Fila | Relatório |
|------|-----------|
| ![Fila](docs/screenshots/01_fila.png) | ![Relatório](docs/screenshots/04_relatorio.png) |
| ![Clientes](docs/screenshots/02_clientes.png) | ![Serviços](docs/screenshots/03_servicos.png) |

## 📋 Gestão do projeto (Trello)

🔗 **Quadro do Trello:** [COLE AQUI O LINK DO QUADRO]

Colunas utilizadas: *Backlog · A fazer · Em andamento · Em testes · Concluído*.

## 📄 Documentação

- Relatório técnico completo: [`docs/Relatorio_Final.pdf`](docs/Relatorio_Final.pdf)
- Diagramas UML: [`docs/uml/`](docs/uml/)
- Protótipos: [`docs/prototipos/`](docs/prototipos/)
