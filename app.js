/* BarberQueue - frontend (JavaScript puro, sem frameworks). Consome a API REST em /api. */
const $ = (id) => document.getElementById(id);
const moeda = (v) => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let servicos = [];

/* ---------- comunicação com a API ---------- */
async function api(url, opcoes = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  });
  if (resp.status === 204) return null;
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.erro || "Erro inesperado.");
  return dados;
}

let tempoToast;
function aviso(msg, ehErro = false) {
  const t = $("toast");
  t.textContent = msg;
  t.className = "toast mostrar" + (ehErro ? " erro" : "");
  clearTimeout(tempoToast);
  tempoToast = setTimeout(() => (t.className = "toast"), 3200);
}
const executar = async (fn, msgOk) => {
  try { await fn(); if (msgOk) aviso(msgOk); } catch (e) { aviso(e.message, true); }
};

/* ---------- abas ---------- */
$("abas").addEventListener("click", (e) => {
  const aba = e.target.closest(".aba");
  if (!aba) return;
  document.querySelectorAll(".aba").forEach((a) => a.classList.toggle("ativa", a === aba));
  document.querySelectorAll(".painel").forEach((p) => p.classList.toggle("ativo", p.id === aba.dataset.aba));
  ({ fila: carregarFila, clientes: carregarClientes, servicos: carregarServicos, relatorio: carregarRelatorio })[aba.dataset.aba]();
});

/* ---------- FILA ---------- */
async function carregarFila() {
  const [clientes, svs, fila] = await Promise.all([api("/api/clientes"), api("/api/servicos"), api("/api/fila")]);
  servicos = svs;

  const marcados = new Set([...document.querySelectorAll("#listaServicosFila input:checked")].map((i) => i.value));
  const selecionado = $("selCliente").value;
  $("selCliente").innerHTML = clientes.length
    ? clientes.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("")
    : `<option value="">Cadastre um cliente primeiro</option>`;
  if (selecionado) $("selCliente").value = selecionado;

  $("listaServicosFila").innerHTML = svs.map((s) =>
    `<label class="check"><input type="checkbox" value="${s.id}" ${marcados.has(String(s.id)) ? "checked" : ""}> ${esc(s.nome)} <span>${moeda(s.preco)}</span></label>`
  ).join("");
  atualizarTotalPrevio();

  const em = fila.em_atendimento;
  $("boxAtendimento").innerHTML = em
    ? `<div class="atendendo">
         <div class="info"><div class="selo">● Em atendimento</div><div class="nome">${esc(em.cliente)}</div>
         <small>${em.servicos.map((s) => esc(s.nome)).join(" + ")}</small></div>
         <div class="valor"><strong style="font-size:1.5rem;color:var(--ouro)">${moeda(em.total)}</strong></div>
         <button class="btn ok" data-finalizar="${em.id}">✔ Finalizar atendimento</button>
       </div>`
    : `<div class="vazio">Nenhum atendimento em andamento. Chame o próximo da fila.</div>`;

  $("contFila").textContent = fila.aguardando.length;
  $("listaFila").innerHTML = fila.aguardando.length
    ? fila.aguardando.map((i) => `<li>
        <div class="pos">${i.posicao}</div>
        <div class="info"><strong>${esc(i.cliente)}</strong>
          <small>${i.servicos.map((s) => esc(s.nome)).join(" + ")} · chegou às ${esc(i.entrada_em.slice(11, 16))}</small></div>
        <div class="valor">${moeda(i.total)}</div>
        <button class="btn pequeno perigo" data-cancelar="${i.id}">Cancelar</button></li>`).join("")
    : `<li class="vazio" style="justify-content:center">A fila está vazia.</li>`;
}

function atualizarTotalPrevio() {
  const ids = [...document.querySelectorAll("#listaServicosFila input:checked")].map((i) => Number(i.value));
  $("totalPrevio").textContent = moeda(servicos.filter((s) => ids.includes(s.id)).reduce((t, s) => t + s.preco, 0));
}
$("listaServicosFila").addEventListener("change", atualizarTotalPrevio);

$("btnEntrar").onclick = () => executar(async () => {
  const servs = [...document.querySelectorAll("#listaServicosFila input:checked")].map((i) => Number(i.value));
  await api("/api/fila", { method: "POST", body: { cliente_id: Number($("selCliente").value), servicos: servs } });
  document.querySelectorAll("#listaServicosFila input").forEach((i) => (i.checked = false));
  await carregarFila();
}, "Cliente adicionado ao final da fila.");

$("btnProximo").onclick = () => executar(async () => { await api("/api/fila/proximo", { method: "POST" }); await carregarFila(); }, "Próximo cliente chamado!");

$("fila").addEventListener("click", (e) => {
  const fin = e.target.dataset.finalizar, can = e.target.dataset.cancelar;
  if (fin) executar(async () => { await api(`/api/fila/${fin}/finalizar`, { method: "POST" }); await carregarFila(); }, "Atendimento finalizado.");
  if (can && confirm("Cancelar este cliente da fila?")) executar(async () => { await api(`/api/fila/${can}`, { method: "DELETE" }); await carregarFila(); }, "Cliente removido da fila.");
});

/* ---------- CLIENTES ---------- */
async function carregarClientes() {
  const lista = await api("/api/clientes?q=" + encodeURIComponent($("cliBusca").value));
  $("tabClientes").innerHTML = lista.length
    ? lista.map((c) => `<tr><td>${esc(c.nome)}</td><td>${esc(c.telefone) || "—"}</td>
        <td class="acoes"><button class="btn pequeno perigo" data-rmcli="${c.id}">Remover</button></td></tr>`).join("")
    : `<tr><td colspan="3" class="vazio">Nenhum cliente encontrado.</td></tr>`;
}
$("btnCliente").onclick = () => executar(async () => {
  await api("/api/clientes", { method: "POST", body: { nome: $("cliNome").value, telefone: $("cliTel").value } });
  $("cliNome").value = ""; $("cliTel").value = "";
  await carregarClientes();
}, "Cliente cadastrado!");
$("cliBusca").addEventListener("input", carregarClientes);
$("tabClientes").addEventListener("click", (e) => {
  const id = e.target.dataset.rmcli;
  if (id && confirm("Remover este cliente?")) executar(async () => { await api(`/api/clientes/${id}`, { method: "DELETE" }); await carregarClientes(); }, "Cliente removido.");
});

/* ---------- SERVIÇOS ---------- */
async function carregarServicos() {
  servicos = await api("/api/servicos");
  $("tabServicos").innerHTML = servicos.map((s) => `<tr><td>${esc(s.nome)}</td><td>${moeda(s.preco)}</td>
    <td class="acoes"><button class="btn pequeno" data-edsv="${s.id}">Alterar preço</button>
    <button class="btn pequeno perigo" data-rmsv="${s.id}">Remover</button></td></tr>`).join("");
}
$("btnServico").onclick = () => executar(async () => {
  await api("/api/servicos", { method: "POST", body: { nome: $("svNome").value, preco: $("svPreco").value } });
  $("svNome").value = ""; $("svPreco").value = "";
  await carregarServicos();
}, "Serviço cadastrado!");
$("tabServicos").addEventListener("click", (e) => {
  const ed = e.target.dataset.edsv, rm = e.target.dataset.rmsv;
  if (ed) {
    const novo = prompt("Novo preço (R$):");
    if (novo !== null) executar(async () => { await api(`/api/servicos/${ed}`, { method: "PUT", body: { preco: novo } }); await carregarServicos(); }, "Preço atualizado.");
  }
  if (rm && confirm("Remover este serviço? (o histórico é preservado)")) executar(async () => { await api(`/api/servicos/${rm}`, { method: "DELETE" }); await carregarServicos(); }, "Serviço removido.");
});

/* ---------- RELATÓRIO ---------- */
async function carregarRelatorio() {
  const r = await api("/api/relatorio" + ($("relData").value ? "?data=" + $("relData").value : ""));
  $("mClientes").textContent = r.clientes_atendidos;
  $("mServicos").textContent = r.servicos_realizados;
  $("mTotal").textContent = moeda(r.faturamento_total);
  $("tabRelatorio").innerHTML = r.por_servico.length
    ? r.por_servico.map((s) => `<tr><td>${esc(s.nome)}</td><td>${s.quantidade}</td><td>${moeda(s.total)}</td></tr>`).join("")
    : `<tr><td colspan="3" class="vazio">Nenhum atendimento concluído no período.</td></tr>`;
}
$("relData").addEventListener("change", () => executar(carregarRelatorio));
$("btnHoje").onclick = () => { $("relData").value = new Date().toLocaleDateString("sv-SE"); executar(carregarRelatorio); };
$("btnTodos").onclick = () => { $("relData").value = ""; executar(carregarRelatorio); };

executar(carregarFila);
