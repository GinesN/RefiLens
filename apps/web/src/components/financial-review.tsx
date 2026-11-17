"use client";

import { useEffect, useState } from "react";
import { Download, ExternalLink } from "lucide-react";
import { api, Dataset, downloadJson, FinancialReview, money } from "@/lib/api";

export default function FinancialReviewPanel({ data }: { data: Dataset }) {
  const [review, setReview] = useState<FinancialReview | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const companyId = data.company.id;
  useEffect(() => {
    const controller = new AbortController();
    api<FinancialReview>(`companies/${companyId}/financial-review`, {
      signal: controller.signal,
    })
      .then(setReview)
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [companyId, attempt]);
  if (error)
    return (
      <div className="information-note" role="alert">
        {error}{" "}
        <button
          className="text-button"
          onClick={() => {
            setError("");
            setAttempt((v) => v + 1);
          }}
        >
          Retry financial review
        </button>
      </div>
    );
  if (!review) return <p role="status">Loading financial review…</p>;
  const fact = (ids: number[]) =>
    data.financials.facts.find((f) => ids.includes(f.id));
  return (
    <section className="panel financial-review" aria-label="Financial review">
      <div className="panel-heading">
        <h2>Financial review</h2>
        <span className="unit-note">
          Automated checks · human review pending
        </span>
      </div>
      <div className="review-content">
        <p className="field-note">
          Follow the debt-note adjustments to reported debt. The checks retain
          original dates, source rounding and cash restrictions.
        </p>
        <div className="review-grid">
          <div className="table-scroll">
            <table>
              <caption>Debt note to carrying debt · USD</caption>
              <thead>
                <tr>
                  <th>Source component</th>
                  <th>Amount</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {review.debt_bridge.map((line) => (
                  <tr key={line.label}>
                    <td>{line.label}</td>
                    <td className="mono">{money(line.amount, false)}</td>
                    <td>
                      {fact(line.fact_ids) && (
                        <a
                          className="text-button small"
                          href={fact(line.fact_ids)!.source_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Filing
                          <ExternalLink size={12} />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
                <tr>
                  <th>Reconstructed debt</th>
                  <td className="mono">
                    {money(review.reconstructed_debt, false)}
                  </td>
                  <td />
                </tr>
                <tr>
                  <th>Reported carrying debt</th>
                  <td className="mono">{money(review.carrying_debt, false)}</td>
                  <td />
                </tr>
                <tr data-testid="debt-bridge-difference">
                  <th>Difference</th>
                  <td className="mono">
                    {money(review.debt_bridge_difference, false)}
                  </td>
                  <td />
                </tr>
              </tbody>
            </table>
          </div>
          <div className="review-checks">
            {review.checks.map((check) => (
              <details
                key={check.key}
                className={`review-check review-${check.status.toLowerCase()}`}
              >
                <summary>
                  <span>{check.label}</span>
                  <strong>
                    {check.status === "PASS"
                      ? "Agrees"
                      : check.status === "EXPLAINED"
                        ? "Scope / rounding"
                        : check.status === "FAIL"
                          ? "Investigate"
                          : "Unavailable"}
                  </strong>
                </summary>
                <p>{check.detail}</p>
                {check.difference !== null && (
                  <p className="mono">
                    Difference: {money(check.difference, false)}
                  </p>
                )}
              </details>
            ))}
          </div>
        </div>
        <dl className="review-scope">
          <div>
            <dt>Debt-note principal, excluding leases</dt>
            <dd>{money(review.note_principal, false)}</dd>
          </div>
          <div>
            <dt>Sum of disclosed principal buckets</dt>
            <dd>{money(review.scheduled_principal, false)}</dd>
          </div>
          <div>
            <dt>Schedule minus note principal</dt>
            <dd>{money(review.maturity_difference, false)}</dd>
          </div>
          <div>
            <dt>Cash-flow closing cash minus eligible cash</dt>
            <dd>{money(review.cash_flow_cash_difference, false)}</dd>
          </div>
        </dl>
        {review.maturity_difference !== null &&
          Number(review.maturity_difference) !== 0 && (
            <p className="field-note">
              The source narrative uses rounded millions and billions. The
              displayed precision permits a combined rounding bound of{" "}
              {money(review.maturity_rounding_bound, false)}. The difference
              remains visible and is never assigned to a year.
            </p>
          )}
        <div className="review-actions">
          <button
            className="secondary-button"
            onClick={() =>
              downloadJson(
                review,
                `refilens-${data.company.ticker.toLowerCase()}-financial-review.json`,
              )
            }
          >
            <Download size={14} />
            Export financial review JSON
          </button>
          <a
            className="secondary-button"
            href="/research/financial-review.xlsx"
            download
          >
            <Download size={14} />
            Download financial review Excel
          </a>
        </div>
        {review.notes.map((note) => (
          <p className="field-note" key={note}>
            {note}
          </p>
        ))}
      </div>
    </section>
  );
}
