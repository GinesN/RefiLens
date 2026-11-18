const byId = (id) => document.getElementById(id);
const controls = ["share", "rate", "decline"];
const formatter = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2, useGrouping: "always" });
const smallFormatter = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 6 });

function money(amount) {
  const millions = Number(amount) / 1_000_000;
  const format = Math.abs(millions) < 1 ? smallFormatter : formatter;
  return `${format.format(millions)} M USD`;
}

function setText(id, value) {
  byId(id).textContent = value;
}

let data;
let company;
let endYear;
let worker;
let revision = 0;
let debounceTimer;
let workerTimer;
const bridge = byId("bridge");

function showCash(result) {
  byId("result").dataset.negative = Number(result.closing) < 0;
  setText("closing-cash", money(result.closing));
  setText("result-note", Number(result.closing) < 0
    ? "Falta caja para cubrir los pagos de este escenario."
    : `${money(result.debt_from_cash)} de la deuda que vence se pagan con caja.`);
  const rows = [
    ["Caja al inicio del año", result.opening],
    ["Caja que genera el negocio", result.cash_from_operations],
    ["Inversión que se paga", company.capital_expenditure],
    ["Vencimientos que se pagan con caja", result.debt_from_cash],
    ...(Number(result.other_uses) > 0
      ? [["Pago supuesto de deuda a corto plazo", result.other_uses]]
      : []),
    ["Cambio en intereses pagados", result.interest_change],
  ];
  bridge.replaceChildren(...rows.map(([label, amount]) => {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    const value = document.createElement("dd");
    term.textContent = label;
    value.textContent = money(amount);
    row.append(term, value);
    return row;
  }));
}

function status(message, retry = false) {
  setText("model-status", message);
  byId("model-status").hidden = !message;
  byId("retry").hidden = !retry;
}

function clearWorkerTimer() {
  clearTimeout(workerTimer);
  workerTimer = undefined;
}

function stopWorker() {
  worker?.terminate();
  worker = undefined;
}

function unavailable() {
  clearWorkerTimer();
  stopWorker();
  setText("closing-cash", "—");
  setText("result-note", "");
  status("No se pudo calcular este escenario.", true);
}

function getWorker() {
  if (worker) return worker;
  worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });
  const currentWorker = worker;
  worker.onmessage = ({ data: response }) => {
    if (currentWorker !== worker || response.id !== revision) return;
    clearWorkerTimer();
    if (response.error) {
      unavailable();
      return;
    }
    status("");
    showCash(response.result);
  };
  worker.onerror = () => {
    if (currentWorker !== worker) return;
    if (workerTimer !== undefined) unavailable();
    else stopWorker();
  };
  return worker;
}

function calculate() {
  const values = Object.fromEntries(controls.map((key) => [key, byId(key).value]));
  for (const key of controls) setText(`${key}-label`, `${formatter.format(values[key])} %`);
  const id = ++revision;
  clearTimeout(debounceTimer);
  clearWorkerTimer();
  if (endYear === company.period.year + 1 && controls.every((key) => Number(values[key]) === Number(data.defaults[key]))) {
    status("");
    showCash(company.initial);
    return;
  }
  byId("result").dataset.negative = "false";
  setText("closing-cash", "—");
  setText("result-note", "");
  bridge.replaceChildren();
  status("Calculando…");
  debounceTimer = setTimeout(() => {
    try {
      getWorker().postMessage({ id, company, controls: { ...values, through: endYear } });
      workerTimer = setTimeout(unavailable, 18000);
    } catch {
      unavailable();
    }
  }, 90);
}

function renderSchedule() {
  const schedule = byId("schedule");
  const max = Math.max(1, ...company.schedule.map((entry) => Number(entry.amount)));
  const buttons = company.schedule.map((entry, index) => {
    const button = document.createElement("button");
    const column = document.createElement("span");
    const label = document.createElement("span");
    const year = entry.year ?? `${company.period.year + 6}+`;
    button.type = "button";
    button.className = entry.year === null ? "bar-button later" : "bar-button";
    button.setAttribute("aria-label", `${year}: ${money(entry.amount)}`);
    column.className = "bar";
    column.setAttribute("aria-hidden", "true");
    const relativeHeight = 100 * Number(entry.amount) / max;
    column.style.setProperty("--height", `${relativeHeight}%`);
    label.textContent = year;
    button.append(column, label);
    button.addEventListener("click", () => selectBucket(index));
    return button;
  });
  function selectBucket(index) {
    const entry = company.schedule[index];
    buttons.forEach((button, i) => button.setAttribute("aria-pressed", String(index === i)));
    if (entry.year === null) {
      setText("selected-bucket", `Desde ${company.period.year + 6} · ${money(entry.amount)} en total, sin desglose anual.`);
      return;
    }
    endYear = entry.year;
    const first = company.period.year + 1;
    const horizon = endYear === first ? String(first) : `${first}–${endYear}`;
    setText("selected-bucket", `${endYear} · ${money(entry.amount)} de principal`);
    setText("simulation-period", `Escenario ${horizon} · ${money(entry.amount)} vencen en ${endYear}`);
    setText("result-caption", `Caja estimada al final de ${endYear}`);
    calculate();
  }
  schedule.replaceChildren(...buttons);
  endYear = company.period.year + 1;
  selectBucket(0);
}

function reset() {
  for (const key of controls) byId(key).value = data.defaults[key];
  calculate();
}

function selectCompany() {
  company = data.companies.find((entry) => entry.ticker === byId("company").value);
  const { period, source } = company;
  setText("company-name", company.name);
  setText("company-ticker", company.ticker);
  setText("opening-cash", money(company.cash));
  setText("source-cfo", money(company.operating_cash_flow));
  setText("source-scope", source.scope);
  const filed = new Date(`${source.filed}T00:00:00Z`);
  const filedLabel = new Intl.DateTimeFormat("es-ES", { dateStyle: "long", timeZone: "UTC" }).format(filed);
  setText("filing-date", `Informe 10-K del ejercicio ${period.year}, publicado el ${filedLabel}. Referencia SEC ${source.accession}.`);
  byId("filing-link").href = source.url;
  for (const key of controls) byId(key).value = data.defaults[key];
  renderSchedule();
}

async function init() {
  const response = await fetch(new URL("./companies.json", import.meta.url));
  if (!response.ok) throw new Error("No se pudieron cargar los datos.");
  data = await response.json();
  byId("company").replaceChildren(...data.companies.map(
    (entry) => new Option(`${entry.name} (${entry.ticker})`, entry.ticker),
  ));
  selectCompany();
  byId("company").addEventListener("change", selectCompany);
  for (const key of controls) byId(key).addEventListener("input", calculate);
  byId("reset").addEventListener("click", reset);
  byId("retry").addEventListener("click", calculate);
  byId("workspace").hidden = false;
  if (location.hash === "#case") {
    byId("case").open = true;
    byId("case").scrollIntoView();
  }
}

init().catch(() => { byId("load-error").hidden = false; });
