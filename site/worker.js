import { loadPyodide } from "./runtime/pyodide.mjs";

async function initialize() {
  const py = await loadPyodide({ indexURL: new URL("runtime/", self.location).href });
  await Promise.all(["model.py", "liquidity.py"].map(async (name) => {
    const response = await fetch(new URL(`${name}?v=3`, self.location));
    if (!response.ok) throw new Error(`Missing calculation source: ${name}`);
    py.FS.writeFile(name, await response.text());
  }));
  const simulate = py.runPython(`
import json
from model import analyze

def calculate(payload):
    company, controls = json.loads(payload)
    return json.dumps(analyze(company, **controls))

calculate
`);
  return simulate;
}

let ready;
self.onmessage = async ({ data: { id, company, controls } }) => {
  try {
    ready ??= initialize();
    const calculate = await ready;
    const result = JSON.parse(calculate(JSON.stringify([company, controls])));
    self.postMessage({ id, result });
  } catch {
    self.postMessage({ id, error: true });
  }
};
