"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Download, ExternalLink } from "lucide-react";
import {
  api,
  CaseStudy,
  Dataset,
  downloadJson,
  LiquidityInput,
  LiquidityYear,
  money,
  multiple,
  rateToPercent,
  ResearchCase,
} from "@/lib/api";

export default function CaseStudyPanel({
  data,
  onOpenAnnual,
  onSources,
  onOpenNucor,
}: {
  data: Dataset;
  onOpenAnnual: (
    input: LiquidityInput,
    other: { year: number; amount: string }[],
  ) => void;
  onSources: () => void;
  onOpenNucor: () => void;
}) {
  const [study, setStudy] = useState<CaseStudy | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [selectedId, setSelectedId] =
    useState<ResearchCase["id"]>("pause_buybacks");
  useEffect(() => {
    const controller = new AbortController();
    api<CaseStudy>(`companies/${data.company.id}/case-study`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (value.filing.id !== data.financials.filing.id)
          throw new Error("The case source changed. Reload the company.");
        if (!controller.signal.aborted) setStudy(value);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [data.company.id, data.financials.filing.id, attempt]);
  if (error)
    return (
      <div className="panel empty-state" role="alert">
        <h2>Case study unavailable</h2>
        <p>{error}</p>
        <button
          className="secondary-button"
          onClick={() => {
            setError("");
            setAttempt((v) => v + 1);
          }}
        >
          Retry case study
        </button>
      </div>
    );
  if (!study)
    return (
      <p role="status">
        Loading the dated case, evidence and reproducible cash models…
      </p>
    );
  if (!study.available || !study.report)
    return (
      <section className="panel empty-state">
        <h2>A focused Nucor case</h2>
        <p>{study.reason}</p>
        <button className="primary-button" onClick={onOpenNucor}>
          Open Nucor case study <ArrowUpRight size={14} />
        </button>
      </section>
    );
  const report = study.report;
  const selected = report.cases.find((c) => c.id === selectedId)!;
  const response = report.cases.find((c) => c.id === "pause_buybacks")!;
  const lines: [string, keyof LiquidityYear][] = [
    ["Opening unfunded cash", "opening_cash"],
    ["Add assumed operating cash flow", "operating_cash_flow_assumption"],
    ["Less assumed cash capex", "capital_expenditure_assumption"],
    ["Less other assumed cash uses", "other_cash_uses_assumption"],
    ["Less source principal", "scheduled_principal"],
    ["Add assumed refinancing", "refinanced_principal"],
    ["Less assumed issuance fees", "issuance_fees"],
    ["Less cumulative interest change", "cumulative_interest_change"],
    [
      "Closing cash before uncommitted funding",
      "closing_cash_before_uncommitted_funding",
    ],
    ["Shortfall to chosen cash floor", "shortfall_to_minimum_cash"],
  ];
  function downloadMemo() {
    const url = URL.createObjectURL(
      new Blob([report!.memo_markdown], {
        type: "text/markdown;charset=utf-8",
      }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "RefiLens-Nucor-FY2025-case-study.md";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <article className="case-study" aria-label="Nucor financial case study">
      <header className="case-heading">
        <span className="eyebrow">
          A DATED CAPITAL-ALLOCATION CASE · 2026–2027
        </span>
        <h2>{report.title}</h2>
        <p>{report.question}</p>
        <p className="field-note">
          Opening balance: 31 Dec 2025 · Information cutoff: 25 Feb 2026 ·
          Conditional planning exercise · Human review pending
        </p>
      </header>
      <div className="case-facts" aria-label="Historical source facts">
        <div>
          <span>FY2025 cash after capex</span>
          <strong>{money(report.historical_free_cash_flow, true, 2)}</strong>
          <small>Operating cash flow less cash PP&amp;E purchases</small>
        </div>
        <div>
          <span>FY2025 coverage proxy</span>
          <strong>{multiple(report.historical_coverage_proxy)}</strong>
          <small>Analytical EBIT proxy / reported gross interest</small>
        </div>
        <div>
          <span>Principal due 2026–2027</span>
          <strong>{money(report.near_term_principal, true, 2)}</strong>
          <small>Only those two exact source buckets</small>
        </div>
      </div>
      <section className="case-answer">
        <span className="eyebrow">THE ANSWER, WITH ITS CONDITIONS</span>
        <h3>
          Pausing buybacks helps. It does not fully restore the chosen cash
          reserve.
        </h3>
        <p>
          A buyback means spending cash to repurchase the company’s own shares.
          In this model, pausing those purchases in both years preserves{" "}
          <strong>
            {money(report.cash_preserved_by_pausing_buybacks, true, 2)}
          </strong>
          . Ending cash then stays positive at{" "}
          <strong data-testid="case-response-cash">
            {money(
              response.projection.closing_cash_before_uncommitted_funding,
              true,
              2,
            )}
          </strong>
          , but remains below the assumed{" "}
          {money(report.minimum_cash_assumption, true, 2)} reserve.
        </p>
        <div className="case-answer-numbers">
          <div>
            <span>Remaining cash-floor gap</span>
            <strong data-testid="case-residual-gap">
              {money(report.remaining_cash_floor_gap, true, 2)}
            </strong>
          </div>
          <div>
            <span>Extra cash improvement needed each year</span>
            <strong data-testid="case-annual-improvement">
              {money(
                report.minimum_additional_annual_cash_improvement,
                true,
                2,
              )}
            </strong>
          </div>
        </div>
        <p className="field-note">
          The additional improvement must occur in BOTH 2026 and 2027, with all
          other assumptions fixed. This is a mathematical requirement; spending
          flexibility, operating improvements or new funding are not assumed
          available. No cash gap is automatically financed.
        </p>
      </section>
      <section className="panel case-cases">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">1 / COMPARE CONTROLLED CHANGES</span>
            <h3>From reported cash generation to a funding question</h3>
          </div>
        </div>
        <p className="case-note">
          The operating stress repeats the observed{" "}
          {money(report.observed_cfo_deterioration, true, 2)} CFO deterioration
          once and holds that lower level. It is a historical-magnitude
          sensitivity, with no assigned probability. Each row is calculated
          independently.
        </p>
        <p className="table-scroll-hint">
          Swipe the table sideways to see the outcomes and review buttons.
        </p>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Case-study comparison"
        >
          <table>
            <thead>
              <tr>
                <th>Assumption set</th>
                <th>End-2027 cash</th>
                <th>Peak shortfall to reserve</th>
                <th>First shortfall</th>
                <th>Inspect</th>
              </tr>
            </thead>
            <tbody>
              {report.cases.map((c) => (
                <tr
                  key={c.id}
                  className={c.id === selectedId ? "case-selected" : ""}
                >
                  <th>{c.label}</th>
                  <td>
                    {money(
                      c.projection.closing_cash_before_uncommitted_funding,
                      true,
                      2,
                    )}
                  </td>
                  <td>{money(c.projection.peak_shortfall, true, 2)}</td>
                  <td>
                    {c.projection.first_shortfall_year ?? "None in horizon"}
                  </td>
                  <td>
                    <button
                      className="text-button"
                      aria-label={`Review ${c.label}`}
                      aria-pressed={c.id === selectedId}
                      onClick={() => setSelectedId(c.id)}
                    >
                      Review <ArrowUpRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel case-working">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">2 / FOLLOW THE CASH</span>
            <h3>{selected.label}</h3>
          </div>
          <span className="status-pill">Hypothetical inputs and results</span>
        </div>
        <p className="case-note" data-testid="case-rationale">
          {selected.rationale}
        </p>
        <dl className="case-selected-inputs">
          <div>
            <dt>New coupon assumption</dt>
            <dd>{rateToPercent(selected.inputs.new_rate)}%</dd>
          </div>
          <div>
            <dt>Principal refinanced</dt>
            <dd>{rateToPercent(selected.inputs.refinance_fraction)}%</dd>
          </div>
          <div>
            <dt>Issuance fee</dt>
            <dd>{rateToPercent(selected.inputs.issuance_fee_rate)}%</dd>
          </div>
          <div>
            <dt>Annual share buybacks</dt>
            <dd>{money(selected.annual_buybacks_assumption, true, 2)}</dd>
          </div>
        </dl>
        <p className="table-scroll-hint">
          Swipe the cash bridge sideways to see both years.
        </p>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Selected case annual cash bridge"
        >
          <table>
            <caption>
              USD · B = billions · M = millions · Cash-flow inputs are before
              modeled interest changes
            </caption>
            <thead>
              <tr>
                <th>Cash bridge</th>
                {selected.projection.years.map((y) => (
                  <th key={y.year}>{y.year}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lines.map(([label, key]) => (
                <tr key={key}>
                  <th>{label}</th>
                  {selected.projection.years.map((y) => (
                    <td key={y.year}>{money(String(y[key]), true, 2)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="case-actions">
          <button
            className="primary-button"
            onClick={() =>
              onOpenAnnual(
                selected.inputs,
                selected.inputs.years.map((y) => ({
                  year: y.year,
                  amount: y.other_cash_uses,
                })),
              )
            }
          >
            Open selected case in annual model <ArrowUpRight size={14} />
          </button>
        </div>
      </section>
      <section className="panel case-reading">
        <span className="eyebrow">3 / DEFEND THE CONCLUSION</span>
        <h3>Why the interest ratio does not answer the cash question</h3>
        <p>
          Profit and interest coverage describe earnings relative to an expense.
          They do not deduct every cash investment, distribution or principal
          repayment. Here, cash generation was already below cash capex in
          FY2025. Future spending choices and refinancing access therefore
          matter alongside the rate.
        </p>
        <p>
          The response case removes only buybacks. It keeps common dividends,
          distributions to noncontrolling interests and share-based compensation
          tax payments. The remaining reserve gap makes the next question
          concrete: which additional cash improvements are feasible, and at what
          cost?
        </p>
        <p className="field-note">
          The separately reported revolving facility is disclosed in the
          evidence below. Its capacity is never added to cash or treated as
          proof that a future gap can be funded.
        </p>
      </section>
      <details className="panel case-details">
        <summary>Read every modeling assumption</summary>
        <ul>
          {report.assumptions.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </details>
      <details className="panel case-details">
        <summary>
          Source appendix: historical amounts, management estimate and facility
          capacity
        </summary>
        <p className="case-note">
          Source types stay separate. A management estimate is not an actual
          cash-flow statement amount, and facility capacity is not cash. Amounts
          retain full USD precision in the JSON export.
        </p>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Case-study source appendix"
        >
          <table>
            <thead>
              <tr>
                <th>Source reference</th>
                <th>Amount</th>
                <th>Period end</th>
                <th>Evidence kind</th>
                <th>Original evidence</th>
              </tr>
            </thead>
            <tbody>
              {study.evidence.map((row) => (
                <tr key={row.key}>
                  <th>{row.label}</th>
                  <td>{money(row.amount, true, 2)}</td>
                  <td>{row.period_end}</td>
                  <td>
                    {row.kind === "HISTORICAL_REPORTED"
                      ? "Historical · cross-checked"
                      : row.kind === "MANAGEMENT_ESTIMATE"
                        ? "Management estimate · source-extracted"
                        : "Disclosed capacity · source-extracted"}
                  </td>
                  <td>
                    <a
                      className="text-button"
                      href={`${row.source_url}${row.source_ref.startsWith("#") ? row.source_ref : ""}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Filing <ExternalLink size={13} />
                    </a>
                    <small>{row.source_ref}</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="case-note">
          Accession {study.filing.accession} ·{" "}
          {money(study.excluded_principal, false)} principal excluded:{" "}
          {study.excluded_bucket_labels.join(", ")}. No later bucket is
          allocated to 2026 or 2027.
        </p>
      </details>
      <details className="panel case-details">
        <summary>Limits and next diligence</summary>
        <ul>
          {report.limitations.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </details>
      <div className="case-actions">
        <a
          className="secondary-button"
          href="/research/RefiLens_Nucor_Case_Study.pdf"
          download
        >
          <Download size={14} />
          Download case PDF
        </a>
        <button className="secondary-button" onClick={downloadMemo}>
          <Download size={14} />
          Download case memo
        </button>
        <button
          className="secondary-button"
          onClick={() =>
            downloadJson(study, "RefiLens-Nucor-FY2025-case-study.json")
          }
        >
          <Download size={14} />
          Export case JSON
        </button>
        <button className="text-button" onClick={onSources}>
          Inspect source review <ArrowUpRight size={14} />
        </button>
      </div>
      <p className="case-footnote">
        Historical FY2025 filing exercise · Later filings and events are not
        incorporated · No default probability, rating, investment recommendation
        or human-review claim
      </p>
    </article>
  );
}
