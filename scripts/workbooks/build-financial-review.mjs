import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const outputDir = path.join(root, "outputs/coverage-expansion-20261116");
const report = JSON.parse(await fs.readFile(path.join(outputDir, "review.json"), "utf8"));
const wb = Workbook.create();
const sheets = new Map(report.issuers.map(issuer => [issuer.ticker, wb.worksheets.add(issuer.ticker)]));
const sources = wb.worksheets.add("Sources");
const rows = [];
const cells = new Map();
const sourceKey = (ticker, concept) => `${ticker}:${concept}`;
const moneyFormat = '#,##0.000;(#,##0.000);"—"';
const number = value => Number(value) / 1_000_000;
const expected = { NUE: [7121, 4861, -188, 4], STLD: [4211.163, 3441.285, 501.509, 0], RS: [1420.9, 1204.3, 502.5, 0], LECO: [1294.008, 985.219, 534.199, -0.004], ITW: [8969, 8118, 2707, 0] };

function halfPrecision(raw, scale) {
  const decimals = String(raw).includes(".") ? String(raw).split(".")[1].length : 0;
  return 10 ** (scale - decimals) / 2 / 1_000_000;
}
for (const issuer of report.issuers) {
  for (const fact of issuer.facts) {
    const row = rows.length + 2;
    cells.set(sourceKey(issuer.ticker, fact.concept), row);
    rows.push([issuer.ticker, fact.concept, number(fact.amount), new Date(`${fact.end}T00:00:00Z`),
      halfPrecision(fact.original_value, fact.original_scale), issuer.review.filing.accession,
      fact.validation_state, "", fact.source_url, fact.source_ref]);
  }
  for (const bucket of issuer.maturities) {
    const row = rows.length + 2;
    cells.set(sourceKey(issuer.ticker, `maturity_${bucket.label}`), row);
    let half = 0;
    if (issuer.ticker === "NUE") {
      const entry = [...bucket.excerpt.matchAll(/\$\s*([\d,.]+)\s+(million|billion)\s+(?:in\s+(\d{4})|thereafter)/g)]
        .find(match => (match[3] || "Thereafter") === bucket.label);
      if (!entry) throw new Error("Missing original narrative precision");
      half = halfPrecision(entry[1], entry[2] === "million" ? 6 : 9);
    } else if (issuer.ticker === "LECO") {
      half = halfPrecision("0", 3);
    }
    rows.push([issuer.ticker, `maturity_${bucket.label}`, number(bucket.amount), new Date(`${bucket.as_of}T00:00:00Z`),
      half, issuer.review.filing.accession, bucket.validation_state, "", bucket.source_url, bucket.source_ref]);
  }
}
sources.getRange("A1:J1").values = [["Issuer", "Source concept", "USD millions", "Period end", "Half rounding unit", "Accession", "Validation", "", "SEC source URL", "Original reference"]];
sources.getRange(`A2:J${rows.length + 1}`).values = rows;
sources.showGridLines = false;
sources.tabColor = "#E7D8C2";
sources.getRange(`A1:J${rows.length + 1}`).format.font = { name: "Arial", size: 10, color: "#172331" };
sources.getRange("A1:G1").format = { fill: "#243B50", font: { bold: true, color: "#FFFFFF" }, rowHeight: 30, wrapText: true };
sources.getRange("I1:J1").format = { fill: "#243B50", font: { bold: true, color: "#FFFFFF" }, rowHeight: 30 };
sources.getRange(`C2:C${rows.length+1}`).setNumberFormat(moneyFormat);
sources.getRange(`E2:E${rows.length+1}`).setNumberFormat('0.000000; (0.000000);"—"');
sources.getRange(`D2:D${rows.length+1}`).setNumberFormat("dd-mmm-yy");
for (const [column, width] of Object.entries({ A: 10, B: 42, C: 19, D: 16, E: 20, F: 31, G: 25, H: 3, I: 110, J: 110 })) sources.getRange(`${column}1:${column}${rows.length+1}`).format.columnWidth = width;
sources.freezePanes.freezeRows(1);
sources.freezePanes.freezeColumns(2);

for (const issuer of report.issuers) {
  const { ticker } = issuer;
  const sheet = sheets.get(ticker);
  sheet.showGridLines = false;
  sheet.tabColor = "#243B50";
  sheet.getRange("A2:D49").format.font = { name: "Arial", size: 10, color: "#172331" };
  sheet.getRange("A2:A49").format.columnWidth = 49;
  sheet.getRange("B2:B49").format.columnWidth = 22;
  sheet.getRange("C2:C49").format.columnWidth = 3;
  sheet.getRange("D2:D49").format.columnWidth = 69;
  sheet.getRange("A2:D49").format.rowHeight = 21;
  sheet.getRange("B6:B44").setNumberFormat(moneyFormat);
  sheet.getRange("A2").values = [[`RefiLens financial review: ${ticker}`]];
  sheet.getRange("A2").format.font = { name: "Arial", size: 14, bold: true, color: "#172331" };
  sheet.getRange("A3").values = [["FY2025. USD millions. Automated review."]];
  sheet.getRange("D3").values = [["Human accounting review remains pending."]];
  sheet.getRange("A3:D3").format.font.italic = true;
  const labels = {
    5: "Debt reconciliation", 6: "Debt-note total before adjustments", 7: "Less premium on debt exchange", 8: "Less issuance costs / discounts",
    9: "Add separately reported short-term debt", 10: "Reconstructed carrying debt", 11: "Current debt carrying amount", 12: "Noncurrent debt carrying amount",
    13: "Balance-sheet debt", 14: "Debt bridge difference", 16: "Cash and net debt", 17: "Eligible cash and equivalents", 18: "Cash-flow statement closing cash",
    19: "Closing cash-flow cash less eligible cash", 20: "Net debt", 22: "Annual cash generation", 23: "Operating cash flow", 24: "Cash purchases of PP&E",
    25: "Free cash flow", 27: "Disclosed principal maturities", 28: "2026", 29: "2027", 30: "2028", 31: "2029", 32: "2030", 33: "Thereafter",
    34: "Sum of source principal buckets", 35: "Finance leases in debt-note total", 36: "Debt-note principal excluding leases",
    37: "Schedule minus debt-note principal", 38: "Combined source rounding bound", 40: "Hypothetical annual interest sensitivity",
    41: "Selected principal", 42: "Previous annual rate (assumed)", 43: "New annual rate (assumed)", 44: "Incremental annual interest",
    46: "Your independent review", 47: "Reviewer", 48: "Review date", 49: "Review comments",
  };
  for (const [row, label] of Object.entries(labels)) sheet.getRange(`A${row}`).values = [[label]];
  for (const row of [5,16,22,27,40,46]) {
    sheet.getRange(`A${row}:B${row}`).format = { fill: "#E7EEF4", font: { bold: true, color: "#243B50" }, rowHeight: 25 };
  }
  function source(row, key) {
    const sourceRow = cells.get(sourceKey(ticker, key));
    if (!sourceRow) throw new Error(`Missing workbook source: ${ticker} ${key}`);
    sheet.getRange(`B${row}`).formulas = [[`=IF(ISNUMBER('Sources'!C${sourceRow}),'Sources'!C${sourceRow},"n.a.")`]];
    sheet.getRange(`B${row}`).format.font.color = "#167044";
  }
  function formula(row, text) { sheet.getRange(`B${row}`).formulas = [[text]]; }
  function difference(row, a, b) { formula(row, `=IF(COUNT(B${a},B${b})=2,B${a}-B${b},"n.a.")`); }
  source(6, "review_debt_gross");
  if (ticker !== "ITW") source(8, "review_debt_costs");
  if (ticker === "NUE") {
    source(7, "review_debt_premium"); source(9, "short_term_debt"); source(35, "finance_lease_liability");
    formula(10, '=IF(COUNT(B6:B9)=4,B6-B7-B8+B9,"n.a.")');
    formula(13, '=IF(COUNT(B9,B11:B12)=3,SUM(B11:B12)+B9,"n.a.")');
    difference(36, 6, 35);
  } else if (ticker === "LECO") {
    source(7, "review_debt_swap_adjustment"); source(9, "short_term_debt");
    sheet.getRange("A7").values = [["Add interest-rate swap adjustment"]];
    sheet.getRange("A9").values = [["Add disclosed short-term borrowing subtotal"]];
    sheet.getRange("A24").values = [["Cash capital expenditure (productive assets)"]];
    sheet.getRange("B35").values = [["n.a."]];
    formula(10, '=IF(COUNT(B6:B9)=4,B6+B7-B8+B9,"n.a.")');
    formula(13, '=IF(COUNT(B9,B12)=2,B9+B12,"n.a.")');
    formula(36, '=IF(COUNT(B6,B9,B11)=3,B6+B9-B11,"n.a.")');
    sheet.getRange("D11").values = [["Explicit zero current long-term debt; short-term subtotal already includes it."]];
    sheet.getRange("D9").values = [["Bank borrowings already appear in the 2026 maturity bucket."]];
  } else if (ticker === "ITW") {
    source(9, "short_term_debt");
    for (const row of [7,8,35]) sheet.getRange(`B${row}`).values = [["n.a."]];
    sheet.getRange("A6").values = [["Long-term debt note subtotal (incl. current)"]];
    sheet.getRange("A9").values = [["Add separately disclosed commercial paper"]];
    formula(10, '=IF(COUNT(B6,B9)=2,B6+B9,"n.a.")');
    formula(13, '=IF(COUNT(B9,B11:B12)=3,SUM(B11:B12)+B9,"n.a.")');
    formula(36, '=IF(ISNUMBER(B6),B6,"n.a.")');
    sheet.getRange("D9").values = [["Outside the long-term maturity table; repayment timing is assumed."]];
  } else {
    for (const row of [7,9,35]) sheet.getRange(`B${row}`).values = [["n.a."]];
    formula(10, '=IF(COUNT(B6,B8)=2,B6-B8,"n.a.")');
    formula(13, '=IF(COUNT(B11:B12)=2,SUM(B11:B12),"n.a.")');
    formula(36, '=IF(ISNUMBER(B6),B6,"n.a.")');
    sheet.getRange("D9").values = [["No absent borrowing is assumed to equal zero."]];
  }
  source(11,"current_debt"); source(12,"noncurrent_debt"); difference(14,10,13);
  source(17,"cash"); source(18,"cash_flow_closing_cash"); difference(19,18,17); difference(20,13,17);
  source(23,"operating_cash_flow"); source(24,"capital_expenditure"); difference(25,23,24);
  for (const [i,label] of ["2026","2027","2028","2029","2030","Thereafter"].entries()) source(28+i,`maturity_${label}`);
  formula(34, '=IF(COUNT(B28:B33)=6,SUM(B28:B33),"n.a.")'); difference(37,34,36);
  if (ticker === "NUE" || ticker === "LECO") {
    const roundingCells = [...["2026","2027","2028","2029","2030","Thereafter"].map(label => `maturity_${label}`), "review_debt_gross", ticker === "NUE" ? "finance_lease_liability" : "short_term_debt"]
      .map(key => `'Sources'!E${cells.get(sourceKey(ticker,key))}`);
    formula(38, `=SUM(${roundingCells.join(",")})`);
    sheet.getRange("B38").format.font.color = "#167044";
    sheet.getRange("D6").values = [[ticker === "NUE" ? "Includes finance leases before source adjustments." : "Long-term borrowing subtotal before swap adjustment and costs."]];
    sheet.getRange("D7").values = [[ticker === "NUE" ? "Sign follows the filing's 'Less premium' row." : "Sign follows the filing's 'Plus interest rate swap adjustment' row."]];
    sheet.getRange("D37").values = [[ticker === "NUE" ? "4.000 remains visible. Never allocated to a maturity year." : "(0.004) is at the displayed precision bound; kept unallocated."]];
    sheet.getRange("D38").values = [["Derived from the displayed precision of source amounts."]];
  } else {
    sheet.getRange("B38").values = [[0]];
    sheet.getRange("D38").values = [["The maturity table must equal its disclosed total."]];
  }
  formula(41, ticker === "RS" ? "=B30" : "=B29");
  sheet.getRange("B42:B43").values = [[0.04],[0.06]];
  sheet.getRange("B42:B43").setNumberFormat("0.00%");
  sheet.getRange("B42:B43").format = { fill: "#FFF1CC", font: { color: "#1456AB" } };
  sheet.getRange("A42:B43").format.font.italic = true;
  sheet.getRange("B42:B43").dataValidation = { rule: { type: "decimal", operator: "between", formula1: 0, formula2: 1 } };
  formula(44, '=IF(COUNT(B41:B43)=3,B41*(B43-B42),"n.a.")');
  if (ticker === "LECO") sheet.getRange("B44").setNumberFormat('#,##0.000000;(#,##0.000000);"—"');
  sheet.getRange("D42").values = [["Blue / amber cells are editable user assumptions."]];
  sheet.getRange("D47").values = [["Fill these fields only after personally opening the sources."]];
  sheet.getRange("B47:B49").format.fill = "#FFF1CC";
  sheet.getRange("B48").setNumberFormat("dd-mmm-yy");
  sheet.getRange("D14").values = [["Reconciles at the filing's displayed precision."]];
  sheet.getRange("D19").values = [[ticker === "STLD" ? "Restricted cash is excluded from eligible cash." : "Cash-flow and balance-sheet closing cash agree."]];
  sheet.getRange("D25").values = [["Acquisitions and distributions excluded. Not a forecast."]];
  sheet.getRange("D33").values = [["Thereafter stays unallocated across individual years."]];
  for (const row of [10,13,14,20,25,34,36,37,44]) {
    sheet.getRange(`A${row}:B${row}`).format.font.bold = true;
    sheet.getRange(`A${row}:B${row}`).format.borders = { top: { style: "thin", color: "#BCCBD7" } };
  }
  sheet.getRange("B14").setNumberFormat("0.00;(0.00);0.00");
  sheet.getRange("B14").conditionalFormats.add("cellIs", { operator:"notEqual", formula:0, format:{ fill:"#FCE3DE",font:{color:"#A72E24",bold:true} } });
  sheet.getRange("A6:A49").format.wrapText = false;
  sheet.getRange("B6:B49").format.horizontalAlignment = "right";
  sheet.freezePanes.freezeRows(5);
}
wb.recalculate();
for (const [ticker, sheet] of sheets) {
  for (const [index, row] of [13,20,25,37].entries()) {
    const actual = sheet.getRange(`B${row}`).values[0][0];
    if (typeof actual !== "number" || Math.abs(actual - expected[ticker][index]) > 1e-8) throw new Error(`Workbook value mismatch ${ticker} B${row}: ${actual}`);
  }
}
for (const ticker of ["LECO", "ITW"]) {
  const target = sheets.get(ticker);
  const cell = sources.getRange(`C${cells.get(`${ticker}:cash`)}`);
  const original = cell.values[0][0];
  cell.values = [[null]]; wb.recalculate();
  if (target.getRange("B20").values[0][0] !== "n.a.") throw new Error(`${ticker}: missing cash became zero`);
  cell.values = [[0]]; wb.recalculate();
  if (Math.abs(target.getRange("B20").values[0][0] - expected[ticker][0]) > 1e-8) throw new Error(`${ticker}: explicit zero lost`);
  cell.values = [[original]];
}
const swap = sources.getRange(`C${cells.get("LECO:review_debt_swap_adjustment")}`);
const originalSwap = swap.values[0][0]; swap.values = [[originalSwap + 1]]; wb.recalculate();
if (Math.abs(sheets.get("LECO").getRange("B14").values[0][0] - 1) > 1e-8) throw new Error("Swap edit did not change debt bridge");
swap.values = [[originalSwap]];
const nue=sheets.get("NUE");
nue.getRange("B42").values = [[0.05]];
wb.recalculate();
if (Math.abs(nue.getRange("B44").values[0][0]-5.32)>1e-8) throw new Error("Rate edit did not recalculate");
nue.getRange("B42").values = [[0.04]];
const cashCell=sources.getRange(`C${cells.get("NUE:cash")}`);
const oldCash=cashCell.values[0][0]; cashCell.values=[[null]];
wb.recalculate();
if(nue.getRange("B20").values[0][0]!=="n.a.") throw new Error("Blank cash became zero");
cashCell.values=[[0]];
wb.recalculate();
if(nue.getRange("B20").values[0][0]!==7121) throw new Error("Explicit zero cash was lost");
cashCell.values=[[oldCash]];
wb.recalculate();
console.log((await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:30},summary:"Formula error scan"})).ndjson);
console.log((await wb.inspect({kind:"table",range:"NUE!A10:B14",include:"values,formulas",tableMaxRows:5,tableMaxCols:2})).ndjson);
for (const [ticker] of sheets) {
  const preview=await wb.render({sheetName:ticker,range:"A1:D49",scale:1.5,format:"png"});
  await fs.writeFile(path.join(outputDir,`${ticker.toLowerCase()}-review.png`),new Uint8Array(await preview.arrayBuffer()));
}
const preview=await wb.render({sheetName:"Sources",range:"A58:G96",scale:1.5,format:"png"});
await fs.writeFile(path.join(outputDir,"sources-preview.png"),new Uint8Array(await preview.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(outputDir,"RefiLens_Financial_Review.xlsx"));
await fs.mkdir(path.join(root,"apps/web/public/research"),{recursive:true});
await fs.copyFile(path.join(outputDir,"RefiLens_Financial_Review.xlsx"),path.join(root,"apps/web/public/research/financial-review.xlsx"));
console.log("Saved one financial review workbook; 5 issuer sheets and original source evidence. Human review fields remain blank.");
