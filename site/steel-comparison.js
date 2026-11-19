const takeaways = {
  reference: "Nucor starts with nearly three times the cash. By 2027, Steel Dynamics edges ahead because its operating cash covers investment and leaves cash to build its balance.",
  costly: "Higher borrowing rates leave less cash at both companies. Nucor loses more cash to the same rate increase because it refinances more principal over the two years.",
  stress: "The starting cash lead reverses. After capital spending, weaker operations consume cash at Nucor while Steel Dynamics still generates a surplus. Steel Dynamics also has less scheduled principal due.",
  response: "Both companies clear the reserve when they refinance 80%. The extra borrowing helps Nucor cross the threshold, with less room to absorb another shock.",
};

export function bindSteelComparison({ comparison, money, millions }) {
  const section = document.getElementById("steel-comparison");
  const settings = section.querySelector("#peer-settings");
  const results = section.querySelector("#peer-results");
  const takeaway = section.querySelector("#peer-takeaway");
  const bridge = section.querySelector("#peer-bridge");
  const buttons = [...section.querySelectorAll("[data-peer-scenario]")];
  const reserve = money(comparison.reserve);

  function renderIssuer(company) {
    const article = document.createElement("article");
    article.className = "peer-issuer";
    article.setAttribute("aria-label", company.name);
    const heading = document.createElement("h3");
    heading.textContent = company.name;
    const ticker = document.createElement("span");
    ticker.className = "ticker";
    ticker.textContent = company.ticker;
    heading.append(" ", ticker);

    const metrics = document.createElement("dl");
    const minimum = company.minimum_share === null ? "Unreachable" : `${company.minimum_share}%`;
    const headroom = Number(company.reserve_headroom);
    const headroomLabel = headroom < 0 ? `Below reserve by ${money(-headroom)}`
      : headroom > 0 ? `${money(headroom)} above reserve` : "Exactly at the reserve";
    const lines = [
      ["2027 year-end cash", money(company.closing)],
      ["At the lowest year-end", headroomLabel],
      ["Opening cash · FY2025", money(company.opening)],
      ["Operating cash after investment · 2026–27", money(company.after_capex)],
      ["Minimum refinancing share", minimum],
    ];
    for (const [index, [label, value]] of lines.entries()) {
      const line = document.createElement("div");
      const term = document.createElement("dt");
      const amount = document.createElement("dd");
      term.textContent = label;
      amount.textContent = value;
      if (index === 1) amount.dataset.below = String(headroom < 0);
      line.append(term, amount);
      metrics.append(line);
    }
    article.append(heading, metrics);
    return article;
  }

  function render(key) {
    const { controls: { share, rate, decline }, companies } = comparison.scenarios[key];
    buttons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.peerScenario === key));
    });
    settings.textContent = `${share}% refinanced · ${rate}% new rate · ${decline}% drop in operating cash · ${reserve} reserve`;
    results.replaceChildren(...companies.map(renderIssuer));
    takeaway.textContent = takeaways[key];
    const rows = [
      ["FY2025 closing cash", "opening"],
      ["Operating cash after capital spending", "after_capex"],
      ["Scheduled principal due (before refinancing)", "principal_due"],
      ["Scheduled principal paid from cash", "cash_principal"],
      ["Assumed short-term debt repayment", "other_uses"],
      ["Cash impact of interest change", "interest"],
      ["2027 year-end cash", "closing"],
    ];
    bridge.replaceChildren(...rows.map(([label, field]) => {
      const row = document.createElement("tr");
      const heading = document.createElement("th");
      heading.scope = "row";
      heading.textContent = label;
      row.append(heading, ...companies.map((company) => {
        const cell = document.createElement("td");
        cell.textContent = millions(company[field]);
        return cell;
      }));
      return row;
    }));
  }

  for (const button of buttons) {
    button.addEventListener("click", () => render(button.dataset.peerScenario));
  }
  render("stress");
  section.hidden = false;
  return section;
}
