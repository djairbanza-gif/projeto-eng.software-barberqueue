# BarberQueue — Sistema de Gerenciamento de Barbearia

Sistema web para organizar o atendimento de uma barbearia: cadastro de clientes e serviços, **fila de atendimento no modelo FIFO** (primeiro a entrar, primeiro a ser atendido), cálculo automático do valor cobrado e relatório de faturamento.

> Projeto Final da disciplina de **Engenharia de Software** — UNIMA, Centro Universitário de Maceió.

## Problema que o software resolve

Quando o atendimento de uma barbearia é controlado de forma manual (caderno, WhatsApp, memória), surgem problemas como: **fila desorganizada** (clientes furando a vez), **perda de informações**, dificuldade em saber **quais serviços foram feitos** e **erros no cálculo dos valores** cobrados. O BarberQueue centraliza tudo isso em um sistema simples: o cliente entra no final da fila, o barbeiro chama sempre o mais antigo, o total é calculado automaticamente e o dono acompanha o faturamento.

## Integrantes da equipe

| Nome | Responsabilidade principal |
|------|----------------------------|
| Hyêgo Reis | Backend / API |
| Sergio Henrique | Frontend |
| Djair Bnaza | Banco de dados e testes |
| Gabriel Antônio | Documentação, UML e protótipos |

## Tecnologias utilizadas

- **Python 3.10+** e **Flask** — backend / API REST
- **SQLite** — banco de dados (arquivo local, sem instalação)
- **HTML5, CSS3 e JavaScript puro** — frontend responsivo (sem frameworks)
- **unittest** — testes automatizados
- **Trello** — gestão do projeto · **Draw.io/Graphviz/Matplotlib** — diagramas · **GitHub** — versionamento

## Principais funcionalidades

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

## Instalação e execução

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
