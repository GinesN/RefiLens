const TICKER = "NUE";
const YEAR = 2027;
const RESERVE = "300";
const HASH = "#nucor-walkthrough";

export function bindNucorGuide({ company, presets, money, apply, readScenario }) {
  const byId = (id) => document.getElementById(id);
  const guide = byId("nucor-walkthrough");
  const start = byId("start-nucor-guide");
  const back = byId("guide-back");
  const next = byId("guide-next");
  const reapply = byId("guide-reapply");
  const heading = byId("guide-title");
  const status = byId("guide-status");
  const metrics = byId("guide-metrics");
  const takeaway = byId("guide-takeaway");
  const due = (year) => money(company.schedule.find((bucket) => bucket.year === year).amount);
  const steps = [
    {
      label: "Starting point",
      title: "What does Nucor have to cover?",
      explanation: `Nucor finished FY2025 with ${money(company.cash)} in cash. Its filing shows ${due(2026)} of scheduled principal due in 2026 and ${due(2027)} in 2027. Start by assuming it can replace all of that debt at 6%.`,
      values: presets.reference,
      metric: ["Headroom above the reserve", (row) => money(row.reserve_headroom)],
      next: "Raise the borrowing rate",
    },
    {
      label: "Higher rates",
      title: "What if lenders charge 9%?",
      explanation: "Keep operations and the amount refinanced the same. With only the rate changing, the drop in year-end cash comes entirely from higher interest across the two years.",
      values: presets.costly,
      metric: ["Extra interest through 2027", (row) => money(-Number(row.interest_effect))],
      next: "Test combined stress",
    },
    {
      label: "Combined stress",
      title: "Positive cash can still fall short",
      explanation: "Now assume operations generate 20% less cash each year and lenders refinance only half the debt at 10%. Nucor pays the rest out of cash. Compare the lowest year-end balance with the chosen $300m reserve.",
      values: presets.stress,
      metric: ["Shortfall against the reserve", (row) => money(row.reserve_gap)],
      takeaway: (row) => `Weaker operations drain ${money(-Number(row.operations_effect))} over two years versus the reference.`,
      next: "Test a bigger refinance",
    },
    {
      label: "Financing response",
      title: "How much debt would need refinancing?",
      explanation: "Keep the 10% rate and weaker operations. Test refinancing 80% of maturing debt, then compare it with the smallest whole percentage that preserves $300m at both year-ends. The model assumes lenders provide that funding.",
      values: presets.response,
      metric: ["Minimum refinancing share", (row) => row.minimum_share === null ? "Unreachable" : `${row.minimum_share}%`],
      takeaway: (row) => Number(row.reserve_headroom) >= 0
        ? `At 80%, cash clears the reserve by ${money(row.reserve_headroom)} at its lowest year-end.`
        : `At 80%, the largest year-end shortfall is ${money(row.reserve_gap)}.`,
      next: "Try your own scenario",
    },
  ];
  const indicators = steps.map(({ label }) => {
    const item = document.createElement("li");
    item.textContent = label;
    return item;
  });
  byId("guide-progress").replaceChildren(...indicators);
  let index = 0;

  function refresh() {
    if (guide.hidden) return;
    const { ticker, year, reserve, values, result, failed } = readScenario();
    const step = steps[index];
    const matches = ticker === TICKER && year === YEAR && /^\d+$/.test(reserve) && Number(reserve) === Number(RESERVE)
      && Object.keys(step.values).every((key) => Number(values[key]) === Number(step.values[key]));
    reapply.hidden = matches;
    metrics.hidden = !matches || !result;
    status.hidden = !metrics.hidden;
    takeaway.hidden = metrics.hidden || !step.takeaway;
    if (metrics.hidden) {
      metrics.replaceChildren();
      status.textContent = !matches ? "The simulator is on a different scenario."
        : failed ? "Calculation failed. Use Retry calculation in the simulator."
        : "Calculating year-end cash…";
      return;
    }
    const [label, value] = step.metric;
    metrics.replaceChildren(...[
      ["Cash at 2027 year-end", money(result.closing)],
      [label, value(result)],
    ].map(([term, amount]) => {
      const item = document.createElement("div");
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = term;
      dd.textContent = amount;
      item.append(dt, dd);
      return item;
    }));
    if (step.takeaway) takeaway.textContent = step.takeaway(result);
  }

  function showStep(stepIndex) {
    index = stepIndex;
    const step = steps[index];
    indicators.forEach((item, i) => {
      if (i === index) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    });
    heading.textContent = step.title;
    byId("guide-explanation").textContent = step.explanation;
    const { share, rate, decline } = step.values;
    byId("guide-settings").textContent = `${share}% refinanced · ${rate}% new rate · ${decline}% drop in operating cash · $300m reserve`;
    back.disabled = index === 0;
    next.textContent = step.next;
    byId("guide-peer-link").hidden = index !== steps.length - 1;
    apply(TICKER, YEAR, RESERVE, step.values);
    heading.focus({ preventScroll: true });
    guide.scrollIntoView({ block: "start" });
  }

  function open() {
    guide.hidden = false;
    start.setAttribute("aria-expanded", "true");
    if (location.hash !== HASH) history.replaceState(null, "", HASH);
    showStep(0);
  }

  function close(focus) {
    guide.hidden = true;
    start.setAttribute("aria-expanded", "false");
    if (location.hash === HASH) history.replaceState(null, "", location.pathname + location.search);
    focus.focus();
  }

  start.hidden = false;
  start.addEventListener("click", open);
  window.addEventListener("hashchange", () => {
    if (location.hash === HASH && guide.hidden) open();
  });
  byId("guide-close").addEventListener("click", () => close(start));
  back.addEventListener("click", () => showStep(index - 1));
  next.addEventListener("click", () => {
    if (index === steps.length - 1) close(byId("sim-title"));
    else showStep(index + 1);
  });
  reapply.addEventListener("click", () => showStep(index));
  return { open, refresh };
}
