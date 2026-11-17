"use client";
import { useEffect, useState } from "react";
import { ArrowUpRight, Download, Info } from "lucide-react";
import {
  api,
  dateLabel,
  downloadJson,
  money,
  PeerComparisonData,
} from "@/lib/api";

export default function PeerComparison({
  onSelect,
}: {
  onSelect: (id: number) => void;
}) {
  const [data, setData] = useState<PeerComparisonData | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    api<PeerComparisonData>("peer-comparison", { signal: controller.signal })
      .then(setData)
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [attempt]);
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">COMPLETE-DATA COHORT</span>
        <h1>Peer comparison</h1>
        <p>
          Compare funding exposures across steel, metalworking and industrial manufacturing.
        </p>
      </div>
      {error && (
        <div className="information-note" role="alert">
          <p>{error}</p>
          <button
            className="text-button"
            onClick={() => {
              setError("");
              setAttempt((v) => v + 1);
            }}
          >
            Retry
          </button>
        </div>
      )}
      {!data && !error && (
        <div className="panel empty-state" role="status">
          Loading source-backed company comparisons…
        </div>
      )}
      {data && (
        <>
          <div className="peer-summary">
            <div>
              <span>Eligible companies</span>
              <strong>{data.rows.length}</strong>
            </div>
            <div>
              <span>Common reporting date</span>
              <strong>{dateLabel(data.period_end)}</strong>
            </div>
            <div>
              <span>Reporting currency</span>
              <strong>{data.currency}</strong>
            </div>
          </div>
          <button
            className="secondary-button peer-export"
            onClick={() =>
              downloadJson(data, "refilens-fy2025-comparison.json")
            }
          >
            <Download size={14} />
            Export comparison JSON
          </button>
          {!data.enabled && (
            <div className="information-note">
              At least three complete approved company snapshots are required to
              enable this comparison.
            </div>
          )}
          <div className="information-note">
            <Info size={16} />
            <p>{data.debt_definition}</p>
          </div>
          <section className="panel peer-panel">
            <div className="panel-heading">
              <h2>Debt, cash & refinancing exposure</h2>
              <span className="unit-note">USD · historical FY2025</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Company / business</th>
                    <th>Debt excl. finance leases</th>
                    <th>Cash & equivalents</th>
                    <th>Net debt excl. finance leases</th>
                    <th>Gross annual interest</th>
                    <th>Principal due 2026–27</th>
                    <th>Core source checks</th>
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row) => {
                    const value = (key: string) =>
                      row.metrics.find((m) => m.key === key)?.value;
                    return (
                      <tr key={row.company.id}>
                        <td>
                          <button
                            className="text-button"
                            aria-label={`Open ${row.company.ticker}`}
                            onClick={() => onSelect(row.company.id)}
                          >
                            {row.company.ticker}
                            <ArrowUpRight size={13} />
                          </button>
                          <span className="table-subtext">
                            {row.company.research_profile?.business_model}
                          </span>
                          <span className="table-subtext">
                            {row.company.filing?.acquisition_mode === "LIVE_SEC"
                              ? "SEC import"
                              : "Offline filing snapshot"}
                          </span>
                        </td>
                        <td className="mono">
                          {money(value("debt_ex_finance_leases"))}
                        </td>
                        <td className="mono">{money(value("cash"))}</td>
                        <td className="mono">
                          {money(value("net_debt_ex_finance_leases"))}
                        </td>
                        <td className="mono">
                          {money(value("interest_expense"), true, 2)}
                        </td>
                        <td className="mono">
                          {money(row.principal_2026_2027, true, 2)}
                        </td>
                        <td>
                          {row.core_facts_checked} / {row.expected_core_facts}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
          <section className="panel peer-panel">
            <div className="panel-heading">
              <h2>Revenue & cash generation</h2>
              <span className="unit-note">Same annual periods · USD</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Annual revenue</th>
                    <th>Free cash flow</th>
                    <th>Full disclosed principal schedule</th>
                    <th>Actual filing</th>
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row) => (
                    <tr key={row.company.id}>
                      <td>{row.company.ticker}</td>
                      <td className="mono">
                        {money(
                          row.metrics.find((m) => m.key === "revenue")?.value,
                        )}
                      </td>
                      <td className="mono">
                        {money(
                          row.metrics.find((m) => m.key === "free_cash_flow")
                            ?.value,
                        )}
                      </td>
                      <td className="mono">
                        {money(row.total_scheduled_principal)}
                      </td>
                      <td>
                        <a
                          className="text-button small"
                          href={row.company.filing?.source_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {row.company.filing?.form} · filed{" "}
                          {row.company.filing?.filed_at}
                          <ArrowUpRight size={12} />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <div className="comparison-notes">
            {data.notes.map((note) => (
              <p key={note}>{note}</p>
            ))}
          </div>
        </>
      )}
    </>
  );
}
