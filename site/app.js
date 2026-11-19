import { drawTrajectory } from "./chart.js?v=6";
import { bindMatrix } from "./sensitivity.js?v=6";
import { bindNucorGuide } from "./nucor-guide.js?v=7";

const byId = (id) => document.getElementById(id);
const controls = ["share", "rate", "decline"];
const presetButtons = [...document.querySelectorAll("[data-preset]")];
const formatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2, useGrouping: "always" });
const smallFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 6 });

function millions(amount) {
  const value = Number(amount) / 1_000_000;
  const format = Math.abs(value) < 1 ? smallFormatter : formatter;
  return format.format(value);
}

function money(amount) {
  const negative = Number(amount) < 0;
  return `${negative ? "−" : ""}$${millions(Math.abs(Number(amount)))}m`;
}

function setText(id, value) {
  byId(id).textContent = value;
}

let data;
let company;
let endYear;
let analysis;
let nucorGuide;
let bucketButtons;
let worker;
let revision = 0;
let debounceTimer;
let workerTimer;
const bridge = byId("bridge");
const renderMatrix = bindMatrix(byId("matrix-head"), byId("matrix-body"), (share, rate) => {
  if (!analysis) return;
  byId("share").value = share;
  byId("rate").value = rate;
  calculate();
});

function matches(values, preset) {
  return controls.every((key) => Number(values[key]) === Number(preset[key]));
}

function difference(amount) {
  return Number(amount) > 0 ? `+${money(amount)}` : money(amount);
}

function showCash(result) {
  byId("result").dataset.negative = Number(result.closing) < 0;
  setText("closing-cash", money(result.closing));
  let note = `${difference(result.delta)} vs. the reference case.`;
  if (Number(result.delta) === 0) note = "Cash matches the reference case.";
  if (Number(result.closing) < 0) note = "This scenario has a funding shortfall.";
  setText("result-note", note);
  const rows = [
    ["Opening cash", result.opening],
    ["Operating cash flow", result.cash_from_operations],
    ["Capital spending", company.capital_expenditure],
    ["Maturing principal paid from cash", result.debt_from_cash],
    ...(Number(result.other_uses) > 0
      ? [["Assumed short-term debt repayment", result.other_uses]]
      : []),
    ["Change in cash interest", result.interest_change],
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

function redraw() {
  if (analysis) drawTrajectory(byId("cash-chart"), company.cash, analysis.years, endYear, analysis.reserve);
}

function showLimits(result, yearIndex) {
  const rate = Number(byId("rate").value);
  const share = Number(byId("share").value);
  const decline = Number(byId("decline").value);
  const target = Number(analysis.reserve);
  const first = company.period.year + 1;
  const period = endYear === first ? String(first) : `${first}–${endYear}`;
  byId("limits-data").hidden = false;
  byId("limites").dataset.loading = "false";
  byId("limits-status").hidden = true;
  setText("matrix-period", `${company.name} · ${period} · Operating cash flow down ${decline}%`);
  renderMatrix(analysis.matrix, yearIndex, share, rate);
  const minimum = result.minimum_share;
  const apply = byId("apply-minimum");
  apply.hidden = minimum === null || minimum === share;
  setText("minimum-share", minimum === null ? "Unreachable" : `${minimum}%`);
  const conditions = `at ${formatter.format(rate)}% through ${endYear}`;
  let note = `To keep ${money(target)} at every year-end ${conditions}.`;
  if (minimum === null) note = `Even 100% refinancing ${conditions} falls short of the ${money(target)} reserve.`;
  if (minimum === 0) note = `With zero refinancing, the lowest year-end cash through ${endYear} is ${money(result.cash_without_refinancing)}, enough to cover the ${money(target)} reserve.`;
  setText("minimum-note", note);
  setText("reserve-lowest", money(result.lowest));
  setText("reserve-headroom", difference(result.reserve_headroom));
  byId("reserve-headroom").dataset.loss = Number(result.reserve_headroom) < 0;
  byId("reserve-result").hidden = target === 0;
  if (target > 0) {
    setText("reserve-result", Number(result.reserve_gap) > 0
      ? `The largest shortfall against the reserve is ${money(result.reserve_gap)}.`
      : `Cash meets the ${money(target)} reserve at every year-end.`);
  }
}

function showSelectedYear() {
  if (!analysis) return;
  const index = analysis.years.findIndex((row) => row.year === endYear);
  const result = analysis.years[index];
  showCash(result);
  showLimits(result, index);
  byId("cash-years").querySelectorAll("button").forEach((button) => {
    button.setAttribute("aria-pressed", String(Number(button.textContent) === endYear));
  });
  const first = company.period.year + 1;
  setText("driver-period", endYear === first ? `Impact in ${first}` : `Cumulative impact, ${first}–${endYear}`);
  for (const key of ["operations", "principal", "interest", "total"]) {
    const amount = key === "total" ? result.delta : result[`${key}_effect`];
    const element = byId(`${key}-effect`);
    element.textContent = difference(amount);
    element.dataset.sign = Number(amount) < 0 ? "loss" : Number(amount) > 0 ? "gain" : "flat";
  }
  setText("baseline-cash", `Reference case year-end cash: ${money(result.reference)}.`);
  redraw();
  nucorGuide?.refresh();
}

function showProjection(result) {
  analysis = result;
  const rows = result.years;
  byId("comparison-data").hidden = false;
  byId("comparison-status").hidden = true;
  byId("comparison").dataset.loading = "false";
  const openingYear = document.createElement("span");
  openingYear.textContent = company.period.year;
  const years = rows.map(({ year }) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = year;
    button.addEventListener("click", () => chooseBucket(company.schedule.findIndex((entry) => entry.year === year)));
    return button;
  });
  byId("cash-years").replaceChildren(openingYear, ...years);
  const withReserve = Number(result.reserve) > 0;
  const firstGap = rows.find((row) => Number(row.reserve_gap) > 0);
  byId("reserve-key").hidden = !withReserve;
  byId("first-gap").hidden = !firstGap;
  if (firstGap) setText("first-gap", withReserve
    ? `First year-end below the reserve: ${firstGap.year}.`
    : `Cash first turns negative in ${firstGap.year}.`);
  byId("cash-table-body").replaceChildren(...rows.map(({ year, reference, closing }) => {
    const tr = document.createElement("tr");
    const title = document.createElement("th");
    title.scope = "row";
    title.textContent = year;
    tr.append(title);
    for (const amount of [reference, closing]) {
      const td = document.createElement("td");
      td.textContent = millions(amount);
      tr.append(td);
    }
    return tr;
  }));
  showSelectedYear();
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
  setText("comparison-status", "The comparison could not be calculated.");
  setText("limits-status", "The refinancing limits could not be calculated.");
  status("The scenario could not be calculated.", true);
  nucorGuide?.refresh();
}

function getWorker() {
  if (worker) return worker;
  worker = new Worker(new URL("./worker.js?v=5", import.meta.url), { type: "module" });
  const currentWorker = worker;
  worker.onmessage = ({ data: response }) => {
    if (currentWorker !== worker || response.id !== revision) return;
    clearWorkerTimer();
    if (response.error) {
      unavailable();
      return;
    }
    status("");
    showProjection(response.result);
  };
  worker.onerror = () => {
    if (currentWorker !== worker) return;
    if (workerTimer !== undefined) unavailable();
    else stopWorker();
  };
  return worker;
}

function controlValues() {
  return Object.fromEntries(controls.map((key) => [key, byId(key).value]));
}

function calculate() {
  const values = controlValues();
  for (const key of controls) setText(`${key}-label`, `${formatter.format(values[key])}%`);
  for (const button of presetButtons) {
    button.setAttribute("aria-pressed", String(matches(values, data.presets[button.dataset.preset])));
  }
  const id = ++revision;
  clearTimeout(debounceTimer);
  clearWorkerTimer();
  const reserve = byId("reserve").value;
  const validReserve = /^\d+$/.test(reserve) && Number(reserve) <= 10000;
  byId("reserve-error").hidden = validReserve;
  byId("reserve").setAttribute("aria-invalid", String(!validReserve));
  if (validReserve && Number(reserve) === 0 && matches(values, data.defaults)) {
    status("");
    showProjection(company.initial);
    return;
  }
  analysis = undefined;
  byId("result").dataset.negative = "false";
  setText("closing-cash", "—");
  setText("result-note", "");
  byId("reserve-result").hidden = true;
  bridge.replaceChildren();
  byId("comparison").dataset.loading = "true";
  setText("comparison-status", "Updating the comparison…");
  byId("comparison-status").hidden = false;
  byId("limites").dataset.loading = "true";
  byId("limits-status").hidden = false;
  if (!validReserve) {
    setText("comparison-status", "Enter a valid cash reserve.");
    setText("limits-status", "Enter a valid cash reserve.");
    status("Enter a valid cash reserve.");
    nucorGuide?.refresh();
    return;
  }
  setText("limits-status", "Calculating combinations…");
  status("Calculating…");
  nucorGuide?.refresh();
  debounceTimer = setTimeout(() => {
    try {
      getWorker().postMessage({ id, company, controls: { ...values, reserve: String(Number(reserve)) } });
      workerTimer = setTimeout(unavailable, 18000);
    } catch {
      unavailable();
    }
  }, 90);
}

function chooseBucket(index) {
  const entry = company.schedule[index];
  bucketButtons.forEach((button, i) => button.setAttribute("aria-pressed", String(index === i)));
  if (entry.year === null) {
    setText("selected-bucket", `${company.period.year + 6} and later · ${money(entry.amount)} in total, with no annual breakdown.`);
    return;
  }
  endYear = entry.year;
  const first = company.period.year + 1;
  const horizon = endYear === first ? String(first) : `${first}–${endYear}`;
  setText("selected-bucket", `${endYear} · ${money(entry.amount)} in principal`);
  setText("simulation-period", `${horizon} scenario · ${money(entry.amount)} due in ${endYear}`);
  setText("result-caption", `Projected cash at ${endYear} year-end`);
  if (analysis) showSelectedYear();
  else nucorGuide?.refresh();
}

function renderSchedule() {
  const schedule = byId("schedule");
  const max = Math.max(1, ...company.schedule.map((entry) => Number(entry.amount)));
  bucketButtons = company.schedule.map((entry, index) => {
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
    button.addEventListener("click", () => chooseBucket(index));
    return button;
  });
  schedule.replaceChildren(...bucketButtons);
  chooseBucket(0);
}

function loadControls(values) {
  for (const key of controls) byId(key).value = values[key];
  calculate();
}

function selectCompany() {
  analysis = undefined;
  byId("reserve").value = "0";
  company = data.companies.find((entry) => entry.ticker === byId("company").value);
  const { period, source } = company;
  setText("company-name", company.name);
  setText("company-ticker", company.ticker);
  setText("opening-cash", money(company.cash));
  setText("source-cfo", money(company.operating_cash_flow));
  setText("source-scope", source.scope);
  const filed = new Date(`${source.filed}T00:00:00Z`);
  const filedLabel = new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" }).format(filed);
  setText("filing-date", `FY${period.year} Form 10-K, filed ${filedLabel}. SEC accession ${source.accession}.`);
  byId("filing-link").href = source.url;
  renderSchedule();
  loadControls(data.defaults);
}

function applyGuideScenario(ticker, year, reserve, values) {
  if (company.ticker !== ticker) {
    byId("company").value = ticker;
    selectCompany();
  }
  analysis = undefined;
  for (const key of controls) byId(key).value = values[key];
  byId("reserve").value = reserve;
  chooseBucket(company.schedule.findIndex((bucket) => bucket.year === year));
  calculate();
}

async function init() {
  const response = await fetch(new URL("./companies.json?v=6", import.meta.url));
  if (!response.ok) throw new Error("The company data could not be loaded.");
  data = await response.json();
  byId("company").replaceChildren(...data.companies.map(
    (entry) => new Option(`${entry.name} (${entry.ticker})`, entry.ticker),
  ));
  selectCompany();
  byId("company").addEventListener("change", selectCompany);
  for (const key of controls) byId(key).addEventListener("input", calculate);
  byId("reset").addEventListener("click", () => {
    byId("reserve").value = "0";
    loadControls(data.defaults);
  });
  byId("reserve").addEventListener("input", calculate);
  byId("apply-minimum").addEventListener("click", () => {
    if (!analysis) return;
    const row = analysis.years.find((result) => result.year === endYear);
    byId("share").value = row.minimum_share;
    calculate();
  });
  byId("retry").addEventListener("click", calculate);
  for (const button of presetButtons) {
    button.addEventListener("click", () => loadControls(data.presets[button.dataset.preset]));
  }
  byId("workspace").hidden = false;
  nucorGuide = bindNucorGuide({
    company: data.companies.find((entry) => entry.ticker === "NUE"),
    presets: data.presets,
    money,
    apply: applyGuideScenario,
    readScenario: () => ({
      ticker: company.ticker,
      year: endYear,
      reserve: byId("reserve").value,
      values: controlValues(),
      result: analysis?.years.find((row) => row.year === endYear),
      failed: !byId("retry").hidden,
    }),
  });
  new ResizeObserver(redraw).observe(byId("cash-chart"));
  if (location.hash === "#nucor-walkthrough") nucorGuide.open();
  if (location.hash === "#case") {
    byId("case").open = true;
    byId("case").scrollIntoView();
  }
  if (location.hash === "#limites") byId("limites").scrollIntoView();
}

init().catch(() => { byId("load-error").hidden = false; });
