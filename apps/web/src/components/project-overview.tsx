"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Download, FileText, ExternalLink } from "lucide-react";
import { api, CaseStudy, Company, money, multiple } from "@/lib/api";

type Destination =
  "overview" | "case-study" | "sources" | "stress" | "methodology";
export default function ProjectOverview({
  companies,
  onExplore,
}: {
  companies: Company[];
  onExplore: (destination: Destination) => void;
}) {
  const [study, setStudy] = useState<CaseStudy | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const nucor = companies.find((c) => c.ticker === "NUE");
  useEffect(() => {
    if (!nucor) return;
    const controller = new AbortController();
    api<CaseStudy>(`companies/${nucor.id}/case-study`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setStudy(value);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [nucor, attempt]);
  const report = study?.available ? study.report : null;
  const response = report?.cases.find((c) => c.id === "pause_buybacks");
  return (
    <article
      className="project-overview"
      aria-label="RefiLens project introduction"
    >
      <header className="project-intro">
        <span className="eyebrow">
          CORPORATE DEBT RESEARCH / FROM EVIDENCE TO A CASH DECISION
        </span>
        <h1>
          Profit covers interest.
          <br />
          <span>Does cash cover the plan?</span>
        </h1>
        <p>
          Follow real SEC filing evidence through debt maturities, refinancing
          assumptions and a transparent cash model. Then see which decisions
          change the funding picture.
        </p>
        <div className="project-actions">
          <button
            className="primary-button"
            onClick={() => onExplore("case-study")}
          >
            Explore the Nucor case <ArrowUpRight size={16} />
          </button>
          <button
            className="secondary-button"
            onClick={() => onExplore("overview")}
          >
            Open research workspace
          </button>
        </div>
        <p className="project-snapshot">
          Historical FY2025 filings · USD · {companies.length} approved issuers
          · Hypothetical future scenarios
        </p>
      </header>
      <section
        className="project-case-preview"
        aria-label="Featured case preview"
      >
        <div className="project-case-story">
          <span className="eyebrow">THE CASE / NUCOR · 2026–2027</span>
          <h2>A strong earnings ratio can coexist with a cash constraint.</h2>
          <p>
            Investment and cash distributions compete with debt repayments. The
            case asks what happens when operating cash weakens and less
            principal can be refinanced.
          </p>
          {report ? (
            <dl className="project-source-pair">
              <div>
                <dt>Historical earnings coverage proxy</dt>
                <dd>{multiple(report.historical_coverage_proxy)}</dd>
              </div>
              <div>
                <dt>FY2025 cash after capex</dt>
                <dd>{money(report.historical_free_cash_flow, true, 2)}</dd>
              </div>
            </dl>
          ) : (
            <p role="status">
              {error
                ? "The source-backed case is temporarily unavailable."
                : "Loading dated case evidence…"}
            </p>
          )}
          <button className="text-button" onClick={() => onExplore("sources")}>
            Inspect source definitions <ArrowUpRight size={14} />
          </button>
        </div>
        <div className="project-decision">
          <span className="eyebrow">
            ONE CONDITIONAL RESPONSE / PAUSE MODELED BUYBACKS
          </span>
          {report && response ? (
            <>
              <p>
                Pausing assumed repurchases preserves{" "}
                {money(report.cash_preserved_by_pausing_buybacks, true, 2)}{" "}
                across two years. It leaves cash positive, while the chosen
                reserve is still unmet.
              </p>
              <dl>
                <div>
                  <dt>
                    Desired reserve <small>Analyst assumption</small>
                  </dt>
                  <dd>{money(report.minimum_cash_assumption, true, 2)}</dd>
                </div>
                <div>
                  <dt>
                    Cash at end of 2027 <small>Model result</small>
                  </dt>
                  <dd>
                    {money(
                      response.projection
                        .closing_cash_before_uncommitted_funding,
                      true,
                      2,
                    )}
                  </dd>
                </div>
                <div className="decision-gap">
                  <dt>Remaining reserve gap</dt>
                  <dd data-testid="project-case-gap">
                    {money(report.remaining_cash_floor_gap, true, 2)}
                  </dd>
                </div>
              </dl>
              <p className="field-note">
                Source cutoff: 25 Feb 2026. A reserve gap is a conditional
                funding question; feasibility, later events and financing access
                need further diligence.
              </p>
            </>
          ) : error ? (
            <div role="alert">
              <p>{error}</p>
              <button
                className="text-button"
                onClick={() => {
                  setError("");
                  setAttempt((v) => v + 1);
                }}
              >
                Retry featured case
              </button>
            </div>
          ) : (
            <p>Calculating the featured case…</p>
          )}
        </div>
      </section>
      <section className="project-paths" aria-label="Three-minute walkthrough">
        <div className="project-section-heading">
          <span className="eyebrow">A THREE-MINUTE WALKTHROUGH</span>
          <h2>Read the evidence. Change a condition. Explain the result.</h2>
        </div>
        <div className="project-path-grid">
          <button onClick={() => onExplore("sources")}>
            <span className="project-step">01 / TRACE</span>
            <h3>Start with the filing</h3>
            <p>
              Check debt, cash, reporting dates and the exact principal buckets.
              Keep source rounding and missing values visible.
            </p>
            <span className="project-path-link">
              Open evidence <ArrowUpRight size={14} />
            </span>
          </button>
          <button onClick={() => onExplore("case-study")}>
            <span className="project-step">02 / FOLLOW</span>
            <h3>Work through the case</h3>
            <p>
              Compare four controlled cash paths. Open any case in the annual
              editor with the exact same inputs.
            </p>
            <span className="project-path-link">
              Open case study <ArrowUpRight size={14} />
            </span>
          </button>
          <button onClick={() => onExplore("stress")}>
            <span className="project-step">03 / CHALLENGE</span>
            <h3>Test another assumption</h3>
            <p>
              Vary cash generation, investment and refinancing. Inspect the
              sensitivity grid and export a replayable result.
            </p>
            <span className="project-path-link">
              Open stress tools <ArrowUpRight size={14} />
            </span>
          </button>
        </div>
      </section>
      <section
        className="project-downloads panel"
        aria-label="Project documents"
      >
        <div>
          <span className="eyebrow">TAKE THE EVIDENCE WITH YOU</span>
          <h2>
            A brief to share.
            <br />A case to question.
          </h2>
          <p>
            Readable PDFs, plus the original JSON, memo and method notes in one
            presentation pack.
          </p>
        </div>
        <div className="project-download-links">
          <a
            className="secondary-button"
            href="/research/RefiLens_Project_Brief.pdf"
            download
          >
            <FileText size={15} />
            Project brief · PDF
          </a>
          <a
            className="secondary-button"
            href="/research/RefiLens_Nucor_Case_Study.pdf"
            download
          >
            <FileText size={15} />
            Nucor case · PDF
          </a>
          <a
            className="text-button"
            href="/research/RefiLens_Presentation_Pack.zip"
            download
          >
            <Download size={14} />
            Download presentation pack
          </a>
        </div>
      </section>
      <section className="project-notes">
        <div>
          <span className="eyebrow">BUILT TO BE INSPECTED</span>
          <h3>Evidence and assumptions stay separate.</h3>
          <p>
            Python Decimal performs the financial calculations. The browser
            presents the results; future assumptions never become observed
            company facts.
          </p>
          <button
            className="text-button"
            onClick={() => onExplore("methodology")}
          >
            Read methods and boundaries <ArrowUpRight size={14} />
          </button>
        </div>
        <div>
          <span className="eyebrow">COVERAGE / CONTRIBUTION</span>
          <h3>A deliberately bounded research project.</h3>
          <p>
            Nucor and Steel Dynamics produce steel; Reliance distributes metals.
            Lincoln Electric supplies welding equipment and consumables; ITW is a
            diversified industrial manufacturer with a welding segment.
            Their differences remain labelled;
            independent owner accounting review remains pending.
          </p>
          <p className="field-note">
            Historical data and illustrative paths. No credit rating, default
            probability or issuer-approved forecast.
          </p>
        </div>
      </section>
      <details className="project-glossary panel">
        <summary>
          New to financial analysis? Start with these six terms.
        </summary>
        <dl>
          {[
            [
              "Cash / CFO",
              "Cash is a balance at one date. Operating cash flow (CFO) is money generated or consumed over a period.",
            ],
            [
              "Capex / FCF",
              "Capex is investment spending. Here, free cash flow (FCF) subtracts cash capex from operating cash flow; other cash uses still matter.",
            ],
            [
              "Principal / refinancing",
              "Principal is the amount repaid. Refinancing replaces some or all of it with new borrowing, whose availability is an assumption.",
            ],
            [
              "Cash floor / shortfall",
              "The floor is a reserve you choose. A shortfall measures how far the modeled cash balance falls below it.",
            ],
            [
              "M / B",
              "M means millions of dollars. B means billions: one thousand million. Source values and exports retain full units.",
            ],
            [
              "Historical / hypothetical",
              "Historical figures come from a dated filing. Future model inputs are assumptions that you can change and challenge.",
            ],
          ].map(([term, meaning]) => (
            <div key={term}>
              <dt>{term}</dt>
              <dd>{meaning}</dd>
            </div>
          ))}
        </dl>
        <a
          className="text-button"
          href="/research/Guia_RefiLens_ES.md"
          download
        >
          Guía completa en español <Download size={14} />
        </a>
      </details>
      <p className="project-local-note">
        Local research application · A localhost link works on the machine
        running RefiLens. The downloadable documents can be shared
        independently.
      </p>
      {nucor?.filing && (
        <a
          className="project-original"
          href={nucor.filing.source_url}
          target="_blank"
          rel="noreferrer"
        >
          Original Nucor FY2025 filing <ExternalLink size={12} />
        </a>
      )}
    </article>
  );
}
