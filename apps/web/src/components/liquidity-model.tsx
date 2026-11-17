"use client";

import { useEffect, useState } from "react";
import { Download, RotateCcw } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  Dataset,
  downloadJson,
  LiquidityInput,
  LiquidityResult,
  LiquidityYear,
  millionsToMoney,
  money,
  moneyToMillions,
  percentToRate,
  rateToPercent,
} from "@/lib/api";

type AnnualDraft = { year: number; cfo: string; capex: string; other: string };
export interface LiquidityDraft {
  companyId: number;
  filingId: number;
  rows: AnnualDraft[];
  opening: string;
  floor: string;
  previous: string;
  next: string;
  refinance: string;
  fee: string;
  horizon: string;
}
export function liquidityDraftFromInput(input: LiquidityInput): LiquidityDraft {
  return {
    companyId: input.company_id,
    filingId: input.filing_id,
    opening: moneyToMillions(input.available_cash_assumption),
    floor: moneyToMillions(input.minimum_cash),
    previous: rateToPercent(input.previous_rate),
    next: rateToPercent(input.new_rate),
    refinance: rateToPercent(input.refinance_fraction),
    fee: rateToPercent(input.issuance_fee_rate),
    horizon: String(input.years.length),
    rows: input.years.map((row) => ({
      year: row.year,
      cfo: moneyToMillions(row.operating_cash_flow),
      capex: moneyToMillions(row.capital_expenditure),
      other: moneyToMillions(row.other_cash_uses),
    })),
  };
}
export default function LiquidityModel({
  data,
  initialDraft,
  onDraftChange,
}: {
  data: Dataset;
  initialDraft?: LiquidityDraft;
  onDraftChange?: (draft: LiquidityDraft) => void;
}) {
  const saved =
    initialDraft?.companyId === data.company.id &&
    initialDraft.filingId === data.financials.filing.id
      ? initialDraft
      : undefined;
  const metric = (key: string) =>
    data.financials.metrics.find((m) => m.key === key)?.value;
  const amountDraft = (value: string | null | undefined) =>
    value == null ? "" : moneyToMillions(value);
  const initialRows = (): AnnualDraft[] =>
    data.maturities.buckets
      .filter((b) => b.kind === "EXACT_YEAR" && b.year_start !== null)
      .map((b, i) => ({
        year: b.year_start!,
        cfo: amountDraft(metric("operating_cash_flow")),
        capex: amountDraft(metric("capital_expenditure")),
        other:
          (data.company.ticker === "NUE" || data.company.research_profile.short_term_outside_maturities) && i === 0
            ? amountDraft(
                data.financials.facts.find(
                  (f) => f.concept === "short_term_debt",
                )?.amount,
              )
            : "0",
      }));
  const [rows, setRows] = useState(() =>
    initialRows().map(
      (row) => saved?.rows.find((item) => item.year === row.year) ?? row,
    ),
  );
  const [opening, setOpening] = useState(
    () => saved?.opening ?? amountDraft(metric("cash")),
  );
  const [floor, setFloor] = useState(saved?.floor ?? "0");
  const [previous, setPrevious] = useState(saved?.previous ?? "4");
  const [next, setNext] = useState(saved?.next ?? "6");
  const [refinance, setRefinance] = useState(saved?.refinance ?? "100");
  const [fee, setFee] = useState(saved?.fee ?? "0");
  const [horizon, setHorizon] = useState(saved?.horizon ?? "5");
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<LiquidityResult | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  function invalidate() {
    setResult(null);
    setError("");
    setBusy(true);
  }
  useEffect(() => {
    onDraftChange?.({
      companyId: data.company.id,
      filingId: data.financials.filing.id,
      rows,
      opening,
      floor,
      previous,
      next,
      refinance,
      fee,
      horizon,
    });
  }, [
    data.company.id,
    data.financials.filing.id,
    rows,
    opening,
    floor,
    previous,
    next,
    refinance,
    fee,
    horizon,
    onDraftChange,
  ]);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const payload: LiquidityInput = {
          company_id: data.company.id,
          filing_id: data.financials.filing.id,
          as_of: data.financials.filing.period_end,
          currency: "USD",
          available_cash_assumption: millionsToMoney(opening),
          minimum_cash: millionsToMoney(floor),
          previous_rate: percentToRate(previous),
          new_rate: percentToRate(next),
          refinance_fraction: percentToRate(refinance),
          issuance_fee_rate: percentToRate(fee),
          cash_flow_already_adjusted: false,
          years: rows.slice(0, Number(horizon)).map((row) => ({
            year: row.year,
            operating_cash_flow: millionsToMoney(row.cfo, true),
            capital_expenditure: millionsToMoney(row.capex),
            other_cash_uses: millionsToMoney(row.other),
          })),
        };
        const value = await api<LiquidityResult>("liquidity/calculate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        if (!controller.signal.aborted) setResult(value);
      } catch (e) {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Projection failed.");
      } finally {
        if (!controller.signal.aborted) setBusy(false);
      }
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [
    data,
    opening,
    floor,
    previous,
    next,
    refinance,
    fee,
    horizon,
    rows,
    attempt,
  ]);
  function updateYear(
    index: number,
    key: "cfo" | "capex" | "other",
    value: string,
  ) {
    invalidate();
    setRows((current) =>
      current.map((row, i) => (i === index ? { ...row, [key]: value } : row)),
    );
  }
  function reset() {
    invalidate();
    setRows(initialRows());
    setOpening(amountDraft(metric("cash")));
    setFloor("0");
    setPrevious("4");
    setNext("6");
    setRefinance("100");
    setFee("0");
    setHorizon("5");
    setAttempt((v) => v + 1);
  }
  const fields: [string, string, (value: string) => void][] = [
    ["Available opening cash (USDm)", opening, setOpening],
    ["Minimum cash floor (USDm)", floor, setFloor],
    ["Original coupon assumption (%)", previous, setPrevious],
    ["New borrowing rate (%)", next, setNext],
    ["Principal refinanced (%)", refinance, setRefinance],
    ["Issuance fee (%)", fee, setFee],
  ];
  const lines: [string, keyof LiquidityYear][] = [
    ["Opening unfunded cash balance", "opening_cash"],
    ["Add assumed operating cash flow", "operating_cash_flow_assumption"],
    ["Less assumed cash capex", "capital_expenditure_assumption"],
    ["Less other assumed cash uses", "other_cash_uses_assumption"],
    ["Less scheduled principal", "scheduled_principal"],
    ["Add assumed refinancing proceeds", "refinanced_principal"],
    ["Less assumed issuance fees", "issuance_fees"],
    ["Less cumulative cash-interest change", "cumulative_interest_change"],
    [
      "Closing unfunded cash balance",
      "closing_cash_before_uncommitted_funding",
    ],
    ["Shortfall to chosen cash floor", "shortfall_to_minimum_cash"],
  ];
  return (
    <div className="liquidity-model">
      <div className="section-intro">
        <div>
          <h2>Annual liquidity model</h2>
          <p>
            Follow cash through operating flows, maturities and assumed
            refinancing.
          </p>
        </div>
        <span className="status-pill">Hypothetical projection</span>
      </div>
      <div className="information-note">
        <p>
          Every future amount is an editable assumption. Defaults repeat FY2025
          operating cash flow and capex; an imported stress case carries its own
          values, including when you extend its horizon. This is a year-end
          funding model; it does not establish actual financing access or detect
          intra-year cash shortages.
        </p>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Financing assumptions</h2>
          <button className="text-button" onClick={reset}>
            <RotateCcw size={14} />
            Reset liquidity assumptions
          </button>
        </div>
        <div className="liquidity-controls">
          {fields.map(([label, value, setValue]) => (
            <label key={label}>
              <span>{label}</span>
              <input
                aria-label={label}
                inputMode="decimal"
                value={value}
                maxLength={32}
                onChange={(event) => {
                  invalidate();
                  setValue(event.target.value);
                }}
              />
            </label>
          ))}
          <label>
            <span>Projection horizon</span>
            <select
              aria-label="Projection horizon"
              value={horizon}
              onChange={(e) => {
                invalidate();
                setHorizon(e.target.value);
              }}
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} {n === 1 ? "year" : "years"}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="liquidity-help">
          Available opening cash is prefilled from {money(metric("cash"))}{" "}
          consolidated cash, with all of it assumed accessible. Reduce it if
          needed. Refinancing access and both rates are assumptions. A 0%
          refinancing share means the modeled principal is paid from cash.
        </p>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>Annual cash-flow assumptions</h2>
          <span className="unit-note">
            USD millions · before modeled interest changes
          </span>
        </div>
        <p className="table-scroll-hint">
          Scroll the table horizontally to see all inputs.
        </p>
        <div className="table-scroll">
          <table className="liquidity-input-table">
            <thead>
              <tr>
                <th>Year</th>
                <th>Operating cash flow</th>
                <th>Cash capex</th>
                <th>Other cash uses</th>
                <th>Source principal due</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, Number(horizon)).map((row, index) => (
                <tr key={row.year}>
                  <th>{row.year}</th>
                  {(["cfo", "capex", "other"] as const).map((key) => (
                    <td key={key}>
                      <input
                        aria-label={`${row.year} ${key === "cfo" ? "operating cash flow" : key === "capex" ? "cash capex" : "other cash uses"} (USDm)`}
                        inputMode="decimal"
                        value={row[key]}
                        maxLength={32}
                        onChange={(e) => updateYear(index, key, e.target.value)}
                      />
                    </td>
                  ))}
                  <td className="mono">
                    {money(
                      data.maturities.buckets.find(
                        (b) => b.year_start === row.year,
                      )?.amount,
                      true,
                      2,
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="liquidity-help">
          Other cash uses are explicit assumptions.{" "}
          {data.company.ticker === "NUE" || data.company.research_profile.short_term_outside_maturities
            ? "The initial 2026 amount assumes repayment of the separate FY2025 short-term borrowing balance. That payment date is assumed. "
            : data.company.ticker === "LECO"
              ? "Bank borrowings are already included in the 2026 source maturity; they are not added a second time. Other initial zeros are assumptions. "
              : "The initial zero does not assert that the company has no other obligations. "}
          Enter lease principal, dividends, buybacks, acquisitions and other
          outflows as needed. They are otherwise excluded.
        </p>
      </section>
      {error && (
        <div className="information-note" role="alert">
          {error}
        </div>
      )}
      {busy && <p role="status">Calculating annual cash balances…</p>}
      {result && (
        <>
          <div className="liquidity-summary">
            <div>
              <span>Final unfunded cash balance</span>
              <strong data-testid="liquidity-ending-cash">
                {money(result.closing_cash_before_uncommitted_funding, true, 2)}
              </strong>
            </div>
            <div>
              <span>Peak shortfall to cash floor</span>
              <strong data-testid="liquidity-peak-shortfall">
                {money(result.peak_shortfall, true, 2)}
              </strong>
            </div>
            <div>
              <span>First year below cash floor</span>
              <strong data-testid="liquidity-first-shortfall">
                {result.first_shortfall_year ?? "None in this model"}
              </strong>
            </div>
          </div>
          <section className="panel">
            <div className="panel-heading">
              <h2>Modeled year-end cash</h2>
              <span className="unit-note">USD · unfunded balance</span>
            </div>
            <div
              className="liquidity-chart"
              role="img"
              aria-label="Hypothetical year-end cash balances and chosen minimum cash floor"
            >
              <ResponsiveContainer width="100%" height={270}>
                <LineChart
                  data={result.years.map((row) => ({
                    year: String(row.year),
                    cash: Number(row.closing_cash_before_uncommitted_funding),
                  }))}
                  margin={{ top: 22, right: 24, bottom: 10, left: 16 }}
                >
                  <CartesianGrid
                    stroke="#3b4550"
                    strokeDasharray="2 4"
                    vertical={false}
                  />
                  <XAxis dataKey="year" stroke="#aebdcb" tickLine={false} />
                  <YAxis
                    stroke="#aebdcb"
                    tickFormatter={(value) => money(String(value))}
                    width={80}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value) => [
                      money(String(value), false),
                      "Unfunded cash",
                    ]}
                    contentStyle={{
                      background: "#1b2128",
                      border: "1px solid #343e49",
                      color: "#e4ebf2",
                    }}
                  />
                  <ReferenceLine
                    y={Number(result.inputs.minimum_cash)}
                    stroke="#d7b691"
                    strokeDasharray="4 4"
                  />
                  <Line
                    dataKey="cash"
                    type="linear"
                    stroke="#9cc9e9"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>Annual cash bridge</h2>
              <span className="unit-note">USD · server-calculated</span>
            </div>
            <p className="table-scroll-hint">
              Scroll the table horizontally to see all modeled years.
            </p>
            <div className="table-scroll">
              <table className="liquidity-results-table">
                <thead>
                  <tr>
                    <th>Cash-flow line</th>
                    {result.years.map((row) => (
                      <th key={row.year}>{row.year}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lines.map(([label, key]) => (
                    <tr
                      key={key}
                      className={
                        key === "closing_cash_before_uncommitted_funding" ||
                        key === "shortfall_to_minimum_cash"
                          ? "liquidity-total"
                          : ""
                      }
                    >
                      <th>{label}</th>
                      {result.years.map((row) => (
                        <td className="mono" key={row.year}>
                          {money(String(row[key]), true, 2)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="liquidity-help">
              Operating cash flow already includes historical cash interest.
              Only the modeled change is deducted. A negative change adds cash
              savings. Cash deficits remain unfunded; no automatic borrowing is
              inserted.
            </p>
          </section>
          <div className="information-note liquidity-conclusion">
            <p>{result.conclusion}</p>
            <p>
              Assumed principal refinanced over this horizon:{" "}
              {money(result.total_refinanced_principal, false)}. Principal
              outside this horizon: {money(result.excluded_principal, false)} (
              {result.excluded_bucket_labels.join(", ")}). No excluded bucket is
              allocated to a modeled year.
            </p>
          </div>
          <button
            className="secondary-button"
            onClick={() =>
              downloadJson(
                result,
                `refilens-${data.company.ticker.toLowerCase()}-liquidity.json`,
              )
            }
          >
            <Download size={14} />
            Export liquidity model JSON
          </button>
          <details className="panel liquidity-method">
            <summary>Model equations and scope</summary>
            <p>
              Closing unfunded cash = opening cash + assumed operating cash flow
              − cash capex − other cash uses − source principal + assumed
              refinancing − issuance fees − cumulative interest change.
            </p>
            <p>
              Interest change for each retiring bucket = refinanced principal ×
              new rate − original principal × assumed old rate. Changes remain
              in future periods because replacement debt is assumed to mature
              beyond the model horizon.
            </p>
            {result.warnings.map((warning) => (
              <p key={warning}>{warning}</p>
            ))}
          </details>
        </>
      )}
    </div>
  );
}
