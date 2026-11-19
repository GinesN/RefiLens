// Render dollar amounts already calculated by the Python model.
const tickFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

export function drawTrajectory(canvas, opening, rows, endYear, reserve) {
  const { width, height } = canvas.getBoundingClientRect();
  if (width < 1 || height < 1) return;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * pixelRatio);
  canvas.height = Math.round(height * pixelRatio);
  const context = canvas.getContext("2d");
  if (!context) return;
  context.scale(pixelRatio, pixelRatio);
  const palette = getComputedStyle(canvas);
  const color = (name) => palette.getPropertyValue(name).trim();

  const reference = [opening, ...rows.map((row) => row.reference)].map((value) => Number(value) / 1e6);
  const scenario = [opening, ...rows.map((row) => row.closing)].map((value) => Number(value) / 1e6);
  const min = Math.min(0, ...reference, ...scenario);
  const reserveMillions = Number(reserve) / 1e6;
  const max = Math.max(reserveMillions, ...reference, ...scenario);
  const spacing = Math.max((max - min) / 4, 0.01);
  const unit = 10 ** Math.floor(Math.log10(spacing));
  const step = [1, 2, 5, 10].find((factor) => factor * unit >= spacing) * unit;
  const lower = Math.floor(min / step) * step;
  const upper = Math.max(Math.ceil(max / step) * step, lower + step);
  const left = 55;
  const right = width - 10;
  const top = 14;
  const bottom = height - 8;
  const x = (index) => left + (index + 0.5) * (right - left) / scenario.length;
  const y = (value) => bottom - (value - lower) * (bottom - top) / (upper - lower);

  context.font = "12px system-ui, sans-serif";
  context.textAlign = "right";
  context.textBaseline = "middle";
  for (let tick = 0; tick <= Math.round((upper - lower) / step); tick++) {
    const value = lower + tick * step;
    const zero = Math.abs(value) < step / 100;
    const heightAt = y(value);
    context.strokeStyle = zero ? color("--chart-zero") : color("--chart-grid");
    context.beginPath();
    context.moveTo(left, heightAt);
    context.lineTo(right, heightAt);
    context.stroke();
    context.fillStyle = color("--muted");
    context.fillText(tickFormat.format(zero ? 0 : value), left - 7, heightAt);
  }

  if (reserveMillions > 0) {
    context.strokeStyle = color("--chart-reserve");
    context.setLineDash([8, 4]);
    context.beginPath();
    context.moveTo(left, y(reserveMillions));
    context.lineTo(right, y(reserveMillions));
    context.stroke();
  }

  const selected = rows.findIndex((row) => row.year === endYear) + 1;
  context.strokeStyle = color("--chart-marker");
  context.setLineDash([3, 4]);
  context.beginPath();
  context.moveTo(x(selected), top);
  context.lineTo(x(selected), bottom);
  context.stroke();

  function plot(values, color, dash) {
    context.strokeStyle = color;
    context.fillStyle = color;
    context.lineWidth = 2.5;
    context.lineJoin = "round";
    context.setLineDash(dash);
    context.beginPath();
    values.forEach((value, i) => {
      if (i === 0) context.moveTo(x(i), y(value));
      else context.lineTo(x(i), y(value));
    });
    context.stroke();
    values.forEach((value, i) => {
      context.beginPath();
      context.arc(x(i), y(value), i === selected ? 5 : 2.5, 0, 2 * Math.PI);
      context.fill();
    });
  }

  plot(reference, color("--chart-reference"), [5, 4]);
  plot(scenario, color("--chart-scenario"), []);
}
