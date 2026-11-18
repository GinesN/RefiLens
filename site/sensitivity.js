const number = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1, useGrouping: "always" });

const levels = {
  meets: "alcanza la reserva",
  below: "por debajo de la reserva",
  negative: "caja negativa",
};

export function bindMatrix(head, body, apply) {
  const buttons = new Map();

  function create(matrix) {
    const shares = [...new Set(matrix.map((cell) => cell.share))];
    const rates = [...new Set(matrix.map((cell) => cell.rate))];
    const columns = document.createElement("tr");
    for (const title of ["Interés", ...shares.map((share) => `${share} %`)]) {
      const header = document.createElement("th");
      header.scope = "col";
      header.textContent = title;
      columns.append(header);
    }
    head.append(columns);
    for (const rate of rates) {
      const row = document.createElement("tr");
      const header = document.createElement("th");
      header.scope = "row";
      header.textContent = `${rate} %`;
      row.append(header);
      for (const share of shares) {
        const cell = document.createElement("td");
        const button = document.createElement("button");
        button.type = "button";
        button.addEventListener("click", () => apply(share, rate));
        buttons.set(`${share}:${rate}`, button);
        cell.append(button);
        row.append(cell);
      }
      body.append(row);
    }
  }

  return function render(matrix, index, share, rate) {
    if (!buttons.size) create(matrix);
    for (const cell of matrix) {
      const button = buttons.get(`${cell.share}:${cell.rate}`);
      const { lowest, status } = cell.years[index];
      const displayed = number.format(Number(lowest) / 1_000_000);
      const label = `${cell.share} % refinanciado al ${cell.rate} %. Caja mínima: ${displayed} millones de dólares, ${levels[status]}.`;
      button.dataset.level = status;
      button.textContent = displayed;
      button.title = label;
      button.setAttribute("aria-label", label);
      button.setAttribute("aria-pressed", String(cell.share === share && cell.rate === rate));
    }
  };
}
