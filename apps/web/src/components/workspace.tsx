"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BookOpen,
  ChartNoAxesColumnIncreasing,
  Check,
  CheckCheck,
  CircleHelp,
  Database,
  ExternalLink,
  FileCheck2,
  FileText,
  Menu,
  Printer,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import {
  api,
  Brief,
  Bucket,
  Company,
  Dataset,
  dateLabel,
  Financials,
  LiquidityInput,
  Maturities,
  Metric,
  money,
  moneyToMillions,
  multiple,
  Quality,
  ScenarioInput,
  title,
} from "@/lib/api";
import MetricCard from "./metric-card";
import MaturityChart from "./maturity-chart";
import ScenarioLab from "./scenario-lab";
import PeerComparison from "./peer-comparison";
import FinancialReviewPanel from "./financial-review";
import LiquidityModel, {
  LiquidityDraft,
  liquidityDraftFromInput,
} from "./liquidity-model";
import StressScenarios from "./stress-scenarios";
import CaseStudyPanel from "./case-study";
import ProjectOverview from "./project-overview";
import { StressDraft } from "@/lib/stress";

type View =
  | "project"
  | "overview"
  | "profile"
  | "maturities"
  | "scenarios"
  | "liquidity"
  | "stress"
  | "case-study"
  | "sources"
  | "brief"
  | "universe"
  | "peers"
  | "methodology";
type Evidence = { metric?: Metric; bucket?: Bucket } | null;
const nav = [
  { key: "project", label: "Project introduction" },
  { key: "overview", label: "Company overview" },
  { key: "maturities", label: "Debt maturities" },
  { key: "stress", label: "Scenario analysis" },
  { key: "peers", label: "Peer comparison" },
  { key: "case-study", label: "Case study" },
  { key: "brief", label: "Research brief" },
  { key: "sources", label: "Data quality & sources" },
  { key: "universe", label: "Research universe" },
] as const;

export default function Workspace() {
  const [data, setData] = useState<Dataset | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number>();
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [view, setView] = useState<View>("project");
  const [search, setSearch] = useState("");
  const [mobileNav, setMobileNav] = useState(false);
  const [evidence, setEvidence] = useState<Evidence>(null);
  const [scenarioDraft, setScenarioDraft] = useState<ScenarioInput>();
  const [stressDraft, setStressDraft] = useState<StressDraft>();
  const [liquidityDraft, setLiquidityDraft] = useState<LiquidityDraft>();
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    api<Company[]>("companies", { signal: controller.signal })
      .then((list) => {
        setCompanies(list);
        if (!list.length)
          throw new Error(
            "No approved company snapshot is loaded. Run the import command in README.",
          );
        const ticker = new URL(window.location.href).searchParams.get(
          "company",
        );
        const selected =
          list.find((c) => c.ticker === ticker) ||
          list.find((c) => c.ticker === "NUE") ||
          list[0];
        setSelectedCompanyId(selected.id);
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      });
    return () => controller.abort();
  }, [attempt]);

  useEffect(() => {
    if (selectedCompanyId === undefined) return;
    const company = companies.find((c) => c.id === selectedCompanyId);
    if (!company) return;
    const controller = new AbortController();
    Promise.all([
      api<Financials>(`companies/${company.id}/financials`, {
        signal: controller.signal,
      }),
      api<Maturities>(`companies/${company.id}/debt-maturities`, {
        signal: controller.signal,
      }),
      api<Quality>(`companies/${company.id}/data-quality`, {
        signal: controller.signal,
      }),
      api<Brief>(`companies/${company.id}/research-brief`, {
        signal: controller.signal,
      }),
    ])
      .then(([financials, maturities, quality, brief]) => {
        if (!controller.signal.aborted)
          setData({ company, financials, maturities, quality, brief });
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      });
    return () => controller.abort();
  }, [selectedCompanyId, companies]);

  function selectCompany(id: number, openOverview = false, destination?: View) {
    const company = companies.find((c) => c.id === id);
    if (!company) return;
    dialog.current?.close();
    setEvidence(null);
    setScenarioDraft(undefined);
    setStressDraft(undefined);
    setLiquidityDraft(undefined);
    setError("");
    if (id !== selectedCompanyId) {
      setData(null);
      setSelectedCompanyId(id);
    }
    const url = new URL(window.location.href);
    url.searchParams.set("company", company.ticker);
    const next = destination ?? (openOverview ? "overview" : view);
    url.hash = next;
    if (url.href !== window.location.href)
      window.history.pushState(null, "", url.pathname + url.search + url.hash);
    setView(next);
    setMobileNav(false);
    document.getElementById("main-content")?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  useEffect(() => {
    if (!companies.length) return;
    function syncLocation() {
      const url = new URL(window.location.href);
      const hash = url.hash.slice(1) as View;
      const valid = [
        ...nav.map((n) => n.key),
        "profile",
        "methodology",
        "scenarios",
        "liquidity",
      ];
      const next = valid.includes(hash) ? hash : "project";
      const target =
        companies.find((c) => c.ticker === url.searchParams.get("company")) ??
        companies.find((c) => c.ticker === "NUE") ??
        companies[0];
      if (target.id !== selectedCompanyId) {
        dialog.current?.close();
        setEvidence(null);
        setScenarioDraft(undefined);
        setStressDraft(undefined);
        setLiquidityDraft(undefined);
        setData(null);
        setSelectedCompanyId(target.id);
      }
      setView(next);
      setMobileNav(false);
    }
    const timer = setTimeout(syncLocation, 0);
    window.addEventListener("popstate", syncLocation);
    window.addEventListener("hashchange", syncLocation);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("popstate", syncLocation);
      window.removeEventListener("hashchange", syncLocation);
    };
  }, [companies, selectedCompanyId]);

  useEffect(() => {
    if (evidence && dialog.current && !dialog.current.open)
      dialog.current.showModal();
  }, [evidence]);

  function navigate(next: View) {
    setView(next);
    setMobileNav(false);
    const target = `${window.location.pathname}${window.location.search}#${next}`;
    if (window.location.hash !== `#${next}`)
      window.history.pushState(null, "", target);
    document.getElementById("main-content")?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function closeEvidence() {
    dialog.current?.close();
    setEvidence(null);
  }
  const filing = data?.financials.filing;
  const live = filing?.acquisition_mode === "LIVE_SEC";
  const inScenarioTools =
    view === "stress" || view === "liquidity" || view === "scenarios";
  const sectionLabel: Record<View, string> = {
    project: "Project introduction",
    overview: "Company overview",
    profile: "Financial details",
    maturities: "Debt maturities",
    scenarios: "Scenario analysis",
    liquidity: "Scenario analysis",
    stress: "Scenario analysis",
    "case-study": "Financial case study",
    sources: "Sources & review",
    brief: "Research brief",
    universe: "Companies",
    peers: "Peer comparison",
    methodology: "Methodology",
  };
  function openAnnualCase(
    input: LiquidityInput,
    otherCashUses: { year: number; amount: string }[],
  ) {
    const draft = liquidityDraftFromInput(input);
    const first = draft.rows[0];
    if (!first || !data) return;
    // A case applies flat CFO/capex assumptions to each supported future year.
    // Preserve those assumptions when the user later extends a shorter horizon.
    draft.rows = data.maturities.buckets
      .filter(
        (bucket) =>
          bucket.kind === "EXACT_YEAR" &&
          bucket.year_start !== null &&
          bucket.year_start >= first.year &&
          bucket.year_start < first.year + 5,
      )
      .map((bucket) => {
        const year = bucket.year_start!;
        const existing = draft.rows.find((row) => row.year === year);
        const other = otherCashUses.find((row) => row.year === year);
        return (
          existing ?? {
            year,
            cfo: first.cfo,
            capex: first.capex,
            other: other ? moneyToMillions(other.amount) : "",
          }
        );
      })
      .sort((a, b) => a.year - b.year);
    setLiquidityDraft(draft);
    navigate("liquidity");
  }
  const metricByKey = (key: string) =>
    data!.financials.metrics.find((m) => m.key === key)!;
  const companyName = data?.company.name
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
  const sourceFacts = evidence?.metric
    ? data?.financials.facts.filter((f) =>
        evidence.metric!.fact_ids.includes(f.id),
      ) || []
    : [];

  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          const content = document.getElementById("main-content");
          content?.focus({ preventScroll: true });
          content?.scrollIntoView();
        }}
      >
        Skip to research content
      </a>
      <aside
        className={`sidebar workbench-sidebar ${mobileNav ? "mobile-open" : ""}`}
        id="research-sidebar"
      >
        <button
          className="workbench-brand"
          onClick={() => navigate("project")}
          aria-label="RefiLens project introduction"
        >
          Refi<span>Lens</span>
        </button>
        <p className="workbench-subtitle">
          Corporate Debt &amp;
          <br />
          Refinancing Intelligence
        </p>
        <nav aria-label="Main navigation" className="workbench-nav">
          {nav.map((item) => (
            <button
              key={item.key}
              aria-label={item.label}
              aria-current={
                view === item.key ||
                (item.key === "stress" && inScenarioTools) ||
                (item.key === "overview" && view === "profile")
                  ? "page"
                  : undefined
              }
              onClick={() => navigate(item.key)}
              className={
                view === item.key ||
                (item.key === "stress" && inScenarioTools) ||
                (item.key === "overview" && view === "profile")
                  ? "wb-nav-button active"
                  : "wb-nav-button"
              }
            >
              {item.key === "overview"
                ? "Overview"
                : item.key === "universe"
                  ? "Companies"
                  : item.key === "sources"
                    ? "Filings & evidence"
                    : item.label}
              {item.key === "peers" && companies.length < 3 && (
                <small>Later</small>
              )}
            </button>
          ))}
        </nav>
        <div className="workbench-sidebar-bottom">
          <span className="eyebrow">RESEARCH COVERAGE</span>
          <p>
            {companies.length} issuer{companies.length === 1 ? "" : "s"} · USD
            reporting
          </p>
          <button
            onClick={() => navigate("methodology")}
            aria-label="Methodology & assumptions"
          >
            <BookOpen size={14} />
            Methodology
          </button>
          <span className="sidebar-research-note">
            Historical evidence.
            <br />
            Hypothetical scenarios.
          </span>
        </div>
      </aside>
      {mobileNav && (
        <button
          className="nav-backdrop"
          onClick={() => setMobileNav(false)}
          aria-label="Close navigation"
        />
      )}
      <div className="main-shell">
        <header className="workbench-topbar">
          <button
            className="mobile-menu icon-button"
            onClick={() => setMobileNav(!mobileNav)}
            aria-label="Toggle navigation"
            aria-controls="research-sidebar"
            aria-expanded={mobileNav}
          >
            <Menu size={20} />
          </button>
          {view === "project" ? (
            <div className="project-masthead">
              <strong>RefiLens / Research project</strong>
              <span>Filing evidence · Transparent cash models</span>
            </div>
          ) : (
            <>
              <div className="workbench-company">
                <span>Company</span>
                <select
                  className="company-selector"
                  aria-label="Selected company"
                  value={selectedCompanyId || ""}
                  onChange={(e) => selectCompany(Number(e.target.value))}
                >
                  {!companies.length && (
                    <option value="">Loading companies…</option>
                  )}
                  {companies.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name
                        .toLowerCase()
                        .replace(/\b\w/g, (c) => c.toUpperCase())}{" "}
                      ({company.ticker})
                    </option>
                  ))}
                </select>
              </div>
              <div className="workbench-report">
                <span>
                  Annual filing{" "}
                  <strong>{filing ? `FY${filing.fiscal_year}` : "—"}</strong>
                </span>
                <span>
                  Period end{" "}
                  <strong>{filing ? dateLabel(filing.period_end) : "—"}</strong>
                </span>
              </div>
              <a
                className="workbench-filing-link"
                href={filing?.source_url}
                target="_blank"
                rel="noreferrer"
                aria-label="Open original annual filing"
              >
                {filing?.form || "Filing"}
                <ExternalLink size={13} />
              </a>
            </>
          )}
        </header>
        <main id="main-content" tabIndex={-1} className="main-content">
          {!data && !error && (
            <div className="loading-state" role="status">
              <div className="skeleton skeleton-title" />
              <p>Loading filing evidence from the research API…</p>
              <div className="skeleton-grid">
                {[1, 2, 3, 4].map((i) => (
                  <div className="skeleton" key={i} />
                ))}
              </div>
            </div>
          )}
          {error && (
            <div className="panel empty-state" role="alert">
              <Database size={32} />
              <h1>Research data unavailable</h1>
              <p>{error}</p>
              <p>
                Open the RefiLens launcher on this computer, keep it running,
                then retry the connection.
              </p>
              <button
                className="primary-button"
                onClick={() => {
                  setError("");
                  setData(null);
                  setAttempt((v) => v + 1);
                }}
              >
                Retry connection
              </button>
            </div>
          )}
          {data && filing && (
            <>
              {view !== "project" && (
                <div className={`data-mode-strip ${live ? "" : "offline"}`}>
                  <div>
                    <span className="tiny-dot" />
                    <strong>
                      {live ? "LIVE SEC IMPORT" : "OFFLINE FILING SNAPSHOT"}
                    </strong>
                    <span>
                      Historical annual filing · not real-time financial status
                    </span>
                  </div>
                  <span>
                    Imported {dateLabel(filing.imported_at.slice(0, 10))}
                  </span>
                </div>
              )}
              {view === "project" ? (
                <ProjectOverview
                  companies={companies}
                  onExplore={(destination) => {
                    const nucor = companies.find((c) => c.ticker === "NUE");
                    if (nucor) selectCompany(nucor.id, false, destination);
                  }}
                />
              ) : view === "universe" ? (
                <>
                  <PageHeading
                    eyebrow="RESEARCH COVERAGE"
                    title="Research universe"
                    description="Approved US steel-value-chain companies with complete source-backed data for the required analysis."
                  />
                  <section className="panel universe-panel">
                    <div className="panel-heading">
                      <h2>
                        Covered issuers{" "}
                        <span className="count-badge">{companies.length}</span>
                      </h2>
                      <label className="search-box">
                        <Search size={16} />
                        <input
                          placeholder="Search company or ticker"
                          aria-label="Search company or ticker"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                        />
                      </label>
                    </div>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>Company</th>
                            <th>Sector</th>
                            <th>Fiscal period</th>
                            <th>Filed</th>
                            <th>Acquisition</th>
                            <th>Research</th>
                          </tr>
                        </thead>
                        <tbody>
                          {companies
                            .filter((c) =>
                              `${c.name} ${c.ticker}`
                                .toLowerCase()
                                .includes(search.toLowerCase()),
                            )
                            .map((c) => (
                              <tr key={c.id}>
                                <td>
                                  <strong>{c.name}</strong>
                                  <span className="table-subtext">
                                    {c.ticker} · CIK {c.cik}
                                  </span>
                                </td>
                                <td>
                                  {c.research_profile?.sector || c.industry}
                                </td>
                                <td>FY{c.filing?.fiscal_year}</td>
                                <td>
                                  {c.filing
                                    ? dateLabel(c.filing.filed_at)
                                    : "Not available"}
                                </td>
                                <td>
                                  <span className="status-pill">
                                    {c.filing?.acquisition_mode === "LIVE_SEC"
                                      ? "SEC import"
                                      : "Offline snapshot"}
                                  </span>
                                </td>
                                <td>
                                  <button
                                    className="text-button"
                                    onClick={() => selectCompany(c.id, true)}
                                    aria-label={`Open issuer ${c.ticker}`}
                                  >
                                    Open issuer
                                    <ArrowUpRight size={14} />
                                  </button>
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                    {!companies.some((c) =>
                      `${c.name} ${c.ticker}`
                        .toLowerCase()
                        .includes(search.toLowerCase()),
                    ) && (
                      <p className="empty-state">
                        No covered issuers match “{search}”.
                      </p>
                    )}
                  </section>
                  <div className="information-note">
                    <InfoIcon />
                    Only approved companies with required debt, cash, interest
                    and full maturity evidence are published. All current
                    snapshots use FY2025 in USD. Producers and distributors are
                    identified separately.
                  </div>
                </>
              ) : view === "methodology" ? (
                <Methodology />
              ) : view === "peers" ? (
                <PeerComparison onSelect={(id) => selectCompany(id, true)} />
              ) : (
                <>
                  <div className="company-heading">
                    <div>
                      <div className="eyebrow">
                        COMPANY FILE <span className="eyebrow-line" /> US
                        INDUSTRIALS
                      </div>
                      <div className="company-title-row">
                        <h1>{companyName}</h1>
                        <span className="ticker-badge">
                          {data.company.ticker}
                        </span>
                      </div>
                      <p className="company-subtitle">
                        {data.company.research_profile?.sector ||
                          data.company.industry}{" "}
                        <span>·</span> US listed <span>·</span>{" "}
                        {data.company.research_profile?.exchange ||
                          "SEC registrant"}{" "}
                        <span>·</span> USD reporting
                      </p>
                    </div>
                    <a
                      className="secondary-button source-button"
                      href={filing.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <FileText size={15} />
                      Open source filing
                      <ExternalLink size={13} />
                    </a>
                  </div>
                  <div className="filing-meta">
                    <span>
                      <FileCheck2 size={14} />
                      <strong>FY{filing.fiscal_year} annual report</strong>
                    </span>
                    <span>
                      Period ended{" "}
                      <strong>{dateLabel(filing.period_end)}</strong>
                    </span>
                    <span>
                      Filed <strong>{dateLabel(filing.filed_at)}</strong>
                    </span>
                    <span className="validated-label">
                      <CheckCheck size={14} />
                      {data.quality.cross_checked_core_facts} core facts
                      cross-checked
                    </span>
                  </div>
                  <div className="workspace-location">
                    <span>{sectionLabel[view]}</span>
                    <small>
                      Historical observations · hypothetical simulations
                    </small>
                  </div>
                  {inScenarioTools && (
                    <nav className="scenario-tools" aria-label="Scenario tools">
                      {(
                        [
                          [
                            "stress",
                            "Stress scenarios",
                            "Compare three assumption sets",
                          ],
                          [
                            "liquidity",
                            "Annual cash model",
                            "Edit each year's cash flows",
                          ],
                          [
                            "scenarios",
                            "Single maturity",
                            "Isolate one rate change",
                          ],
                        ] as const
                      ).map(([key, label, description]) => (
                        <button
                          key={key}
                          className={view === key ? "selected" : ""}
                          aria-current={view === key ? "page" : undefined}
                          onClick={() => navigate(key)}
                        >
                          <strong>{label}</strong>
                          <span>{description}</span>
                        </button>
                      ))}
                    </nav>
                  )}

                  {view === "overview" && (
                    <>
                      <section
                        className="overview-focus"
                        aria-label="Refinancing focus"
                      >
                        <div>
                          <span className="eyebrow">
                            START WITH THE REPAYMENTS
                          </span>
                          <h2>What comes due, and how could cash change?</h2>
                          <p>
                            Read the disclosed principal first. Then test the
                            cash flows and financing access needed to meet it.
                          </p>
                        </div>
                        <dl>
                          <div>
                            <dt>
                              Principal due{" "}
                              {data.maturities.near_term_years?.join("–")}
                            </dt>
                            <dd data-testid="near-term-principal">
                              {money(
                                data.maturities.near_term_principal,
                                true,
                                2,
                              )}
                            </dd>
                            <small>
                              {data.maturities.near_term_share === null
                                ? "Share unavailable"
                                : `${(Number(data.maturities.near_term_share) * 100).toFixed(1)}% of disclosed principal`}
                            </small>
                          </div>
                          <div>
                            <dt>Next principal repayment year</dt>
                            <dd>
                              {data.maturities.next_positive_year ??
                                "Unavailable"}
                            </dd>
                            <small>
                              {money(
                                data.maturities.next_positive_principal,
                                true,
                                2,
                              )}{" "}
                              principal
                            </small>
                          </div>
                        </dl>
                        <div className="focus-actions">
                          <button
                            className="primary-button"
                            onClick={() => navigate("stress")}
                          >
                            Compare stress scenarios
                            <ArrowUpRight size={15} />
                          </button>
                          <button
                            className="text-button"
                            onClick={() => navigate("maturities")}
                          >
                            Inspect debt maturities
                          </button>
                        </div>
                        <p className="focus-scope">
                          Source long-term principal; cash availability and
                          other outflows require separate assumptions.
                        </p>
                      </section>
                      <div className="section-intro">
                        <div>
                          <h2>Financial position</h2>
                          <p>
                            What is owed, what is held in cash, and how the two
                            compare.
                          </p>
                        </div>
                        <button
                          className="text-button"
                          onClick={() => navigate("profile")}
                        >
                          View financial details
                          <ArrowUpRight size={14} />
                        </button>
                      </div>
                      <div className="metric-grid">
                        {[
                          "gross_debt",
                          "cash",
                          "net_debt",
                          "interest_expense",
                        ].map((key) => (
                          <MetricCard
                            key={key}
                            metric={metricByKey(key)}
                            onEvidence={(m) => setEvidence({ metric: m })}
                          />
                        ))}
                      </div>
                      <p className="amount-key">
                        USD · B = billions · M = millions. Click a figure to
                        inspect its source and definition.
                      </p>
                      <div className="overview-grid">
                        <section className="panel maturity-panel">
                          <div className="panel-heading">
                            <div>
                              <span className="eyebrow">
                                02 / REPAYMENT SCHEDULE
                              </span>
                              <h2>When does the debt come due?</h2>
                            </div>
                            <button
                              className="text-button small"
                              onClick={() => navigate("maturities")}
                            >
                              Explore debt
                              <ArrowUpRight size={14} />
                            </button>
                          </div>
                          <MaturityChart
                            buckets={data.maturities.buckets}
                            onSelect={(bucket) => setEvidence({ bucket })}
                          />
                          <div className="panel-footnote">
                            <span className="legend-dot" />
                            <p>
                              Exact annual principal · long-term debt only.
                              Thereafter is not a single-year maturity.
                            </p>
                          </div>
                        </section>
                        <ScenarioLab
                          key={data.company.id}
                          data={data}
                          compact
                          onOpenFull={(inputs) => {
                            setScenarioDraft(inputs);
                            navigate("scenarios");
                          }}
                        />
                      </div>
                      <section className="panel overview-ledger">
                        <div className="panel-heading">
                          <div>
                            <span className="eyebrow">SOURCE TRACEABILITY</span>
                            <h2>Filing &amp; evidence</h2>
                          </div>
                          <button
                            className="text-button small"
                            onClick={() => navigate("sources")}
                          >
                            View source ledger <ArrowUpRight size={13} />
                          </button>
                        </div>
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr>
                                <th>Record</th>
                                <th>Value</th>
                                <th>Evidence</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td>Annual filing</td>
                                <td>
                                  {filing.form} · FY{filing.fiscal_year}
                                </td>
                                <td>
                                  <a
                                    className="text-button small"
                                    href={filing.source_url}
                                    target="_blank"
                                    rel="noreferrer"
                                  >
                                    SEC original filing{" "}
                                    <ExternalLink size={12} />
                                  </a>
                                </td>
                              </tr>
                              <tr>
                                <td>Financial period</td>
                                <td>
                                  {dateLabel(filing.period_start)} —{" "}
                                  {dateLabel(filing.period_end)}
                                </td>
                                <td className="mono">{filing.accession}</td>
                              </tr>
                              <tr>
                                <td>Core source checks</td>
                                <td>
                                  {data.quality.cross_checked_core_facts} /{" "}
                                  {data.quality.expected_core_facts} matched
                                </td>
                                <td>Human review pending</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </section>
                      <details className="reading-guide">
                        <summary>
                          New to debt research? Start with these three
                          questions. <span>Reading guide +</span>
                        </summary>
                        <div className="reading-guide-grid">
                          <div>
                            <span>01</span>
                            <h3>How much does it owe?</h3>
                            <p>
                              Debt is the amount recorded on the balance sheet.
                              Net debt subtracts eligible cash. Click a figure
                              to see the calculation and filing evidence.
                            </p>
                          </div>
                          <div>
                            <span>02</span>
                            <h3>When must it be repaid?</h3>
                            <p>
                              The bars show principal scheduled for each
                              disclosed year. Thereafter combines later years;
                              it is not one large payment in a single year.
                            </p>
                          </div>
                          <div>
                            <span>03</span>
                            <h3>What if refinancing costs more?</h3>
                            <p>
                              The Scenario Lab models a rate change on selected
                              debt. It is a hypothetical sensitivity, not a
                              prediction or a quoted borrowing rate.
                            </p>
                          </div>
                        </div>
                      </details>
                      <div className="bottom-insights">
                        <div>
                          <ArrowDownRight size={17} />
                          <span>
                            Free cash flow
                            <strong>
                              {money(metricByKey("free_cash_flow").value)}
                            </strong>
                          </span>
                          <button
                            className="icon-button"
                            aria-label="Inspect free cash flow evidence"
                            onClick={() =>
                              setEvidence({
                                metric: metricByKey("free_cash_flow"),
                              })
                            }
                          >
                            <ArrowUpRight size={16} />
                          </button>
                        </div>
                        <div>
                          <Database size={17} />
                          <span>
                            Data basis
                            <strong>Annual · consolidated · USD</strong>
                          </span>
                        </div>
                        <div>
                          <BookOpen size={17} />
                          <span>
                            Interpretation
                            <strong>Scenario outputs are hypothetical</strong>
                          </span>
                        </div>
                      </div>
                    </>
                  )}

                  {view === "profile" && (
                    <>
                      <div className="section-intro">
                        <div>
                          <h2>Financial profile</h2>
                          <p>
                            Click any metric to inspect its formula, components
                            and source evidence.
                          </p>
                        </div>
                        <span className="unit-note">
                          FY{filing.fiscal_year} · USD
                        </span>
                      </div>
                      <div className="metric-grid profile-grid">
                        {data.financials.metrics.map((m) => (
                          <MetricCard
                            key={m.key}
                            metric={m}
                            onEvidence={(metric) => setEvidence({ metric })}
                          />
                        ))}
                      </div>
                      <div className="information-note">
                        <InfoIcon />
                        {data.company.research_profile?.debt_basis}.{" "}
                        {metricByKey("ebit_proxy").note} Operating leases and
                        short-term investments are excluded. Comparison debt
                        excludes finance leases explicitly. EBITDA is not
                        available.
                      </div>
                      <section className="panel">
                        <div className="panel-heading">
                          <h2>Reported components</h2>
                          <span className="eyebrow">SOURCE EXTRACTED</span>
                        </div>
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr>
                                <th>Financial fact</th>
                                <th>USD · full base units</th>
                                <th>Period</th>
                                <th>Validation</th>
                                <th>Evidence</th>
                              </tr>
                            </thead>
                            <tbody>
                              {data.financials.facts.map((f) => (
                                <tr key={f.id}>
                                  <td>{title(f.concept)}</td>
                                  <td className="mono">
                                    {money(f.amount, false)}
                                  </td>
                                  <td>
                                    {f.start ? "FY " : "As of "}
                                    {dateLabel(f.end)}
                                  </td>
                                  <td>
                                    <span className="validation-text">
                                      <Check size={13} />
                                      {title(f.validation_state)}
                                    </span>
                                  </td>
                                  <td>
                                    <a
                                      className="text-button small"
                                      href={f.source_url}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      Source
                                      <ExternalLink size={12} />
                                    </a>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </section>
                    </>
                  )}

                  {view === "maturities" && (
                    <>
                      <div className="section-intro">
                        <div>
                          <h2>Debt maturity wall</h2>
                          <p>
                            Scheduled long-term principal. Broad disclosures
                            remain broad.
                          </p>
                        </div>
                        <span className="status-pill">Document extracted</span>
                      </div>
                      <section className="panel">
                        <div className="panel-heading">
                          <h2>Disclosed repayment schedule</h2>
                          <span className="unit-note">
                            USD · principal basis ·{" "}
                            {dateLabel(filing.period_end)}
                          </span>
                        </div>
                        <MaturityChart
                          buckets={data.maturities.buckets}
                          onSelect={(bucket) => setEvidence({ bucket })}
                        />
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr>
                                <th>Maturity bucket</th>
                                <th>Principal</th>
                                <th>Disclosure basis</th>
                                <th>Validation</th>
                                <th>Evidence</th>
                              </tr>
                            </thead>
                            <tbody>
                              {data.maturities.buckets.map((b) => (
                                <tr key={b.id}>
                                  <td>
                                    <strong>{b.label}</strong>
                                  </td>
                                  <td className="mono">
                                    {money(b.amount, false)}
                                  </td>
                                  <td>
                                    {b.kind === "EXACT_YEAR"
                                      ? "Exact year"
                                      : "Broad / unallocated"}
                                  </td>
                                  <td>
                                    <span className="validation-text">
                                      <Check size={13} />
                                      Cross-checked
                                    </span>
                                  </td>
                                  <td>
                                    <button
                                      className="text-button small"
                                      onClick={() => setEvidence({ bucket: b })}
                                    >
                                      Inspect
                                      <ArrowUpRight size={13} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </section>
                      <section className="panel reconciliation-panel">
                        <div>
                          <span className="eyebrow">
                            RECONCILIATION & SCOPE
                          </span>
                          <h2>
                            Principal and carrying debt measure different
                            things.
                          </h2>
                          <p>{data.maturities.reconciliation_note}</p>
                        </div>
                        <dl>
                          <div>
                            <dt>Disclosed long-term principal</dt>
                            <dd>
                              {money(data.maturities.total_principal, false)}
                            </dd>
                          </div>
                          <div>
                            <dt>Reported debt carrying amount</dt>
                            <dd>
                              {money(data.maturities.carrying_debt, false)}
                            </dd>
                          </div>
                          <div>
                            <dt>Carrying debt minus principal schedule</dt>
                            <dd>
                              {money(data.maturities.scope_difference, false)}
                            </dd>
                          </div>
                        </dl>
                      </section>
                    </>
                  )}

                  {view === "scenarios" && (
                    <>
                      <div className="section-intro">
                        <div>
                          <h2>Single-maturity sensitivity</h2>
                          <p>
                            Change an assumption. Follow the arithmetic. Keep
                            the evidence separate.
                          </p>
                        </div>
                        <span className="unit-note">
                          Live calculation · historical reference
                        </span>
                      </div>
                      <ScenarioLab
                        key={data.company.id}
                        data={data}
                        initialInputs={scenarioDraft}
                        onInputsChange={setScenarioDraft}
                      />
                    </>
                  )}

                  {view === "liquidity" && (
                    <LiquidityModel
                      key={data.company.id}
                      data={data}
                      initialDraft={liquidityDraft}
                      onDraftChange={setLiquidityDraft}
                    />
                  )}
                  {view === "stress" && (
                    <StressScenarios
                      key={data.company.id}
                      data={data}
                      initialDraft={stressDraft}
                      onDraftChange={setStressDraft}
                      onOpenAnnual={openAnnualCase}
                      onSources={() => navigate("sources")}
                    />
                  )}
                  {view === "sources" && <Sources data={data} />}
                  {view === "case-study" && (
                    <CaseStudyPanel
                      key={`${data.company.id}:${filing.id}`}
                      data={data}
                      onOpenAnnual={openAnnualCase}
                      onSources={() => navigate("sources")}
                      onOpenNucor={() => {
                        const nucor = companies.find((c) => c.ticker === "NUE");
                        if (nucor) selectCompany(nucor.id);
                      }}
                    />
                  )}
                  {view === "brief" && (
                    <>
                      <div className="section-intro">
                        <div>
                          <h2>Research brief</h2>
                          <p>
                            Rule-based narrative from this filing snapshot, with
                            a source appendix.
                          </p>
                        </div>
                        <button
                          className="secondary-button"
                          onClick={() => window.print()}
                        >
                          <Printer size={14} />
                          Print / save PDF
                        </button>
                      </div>
                      <article className="panel research-brief">
                        <div className="brief-heading">
                          <span className="eyebrow">
                            REFILENS RESEARCH NOTE
                          </span>
                          <h2>
                            {companyName} · FY{filing.fiscal_year}
                          </h2>
                          <span className="status-pill">
                            {live
                              ? "SEC-imported evidence"
                              : "Offline filing snapshot"}
                          </span>
                        </div>
                        {data.brief.paragraphs.map((p, i) => (
                          <p key={i}>{p}</p>
                        ))}
                        <h3>Source appendix</h3>
                        <dl>
                          <div>
                            <dt>Form / accession</dt>
                            <dd className="mono">
                              {filing.form} · {filing.accession}
                            </dd>
                          </div>
                          <div>
                            <dt>Fiscal period</dt>
                            <dd>
                              {filing.period_start} to {filing.period_end}
                            </dd>
                          </div>
                          <div>
                            <dt>Methodology</dt>
                            <dd>{data.brief.methodology_version}</dd>
                          </div>
                        </dl>
                        <a
                          className="text-button"
                          href={filing.source_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Original SEC filing
                          <ExternalLink size={14} />
                        </a>
                        <small>
                          Generated from deterministic templates. No AI prose or
                          human-review claim.
                        </small>
                      </article>
                    </>
                  )}
                </>
              )}
              <footer className="page-footer">
                <span>
                  RefiLens <span>·</span> Corporate Debt & Refinancing Risk
                  Intelligence
                </span>
                <span>
                  Research support only <span>·</span> Verify the filing
                </span>
              </footer>
            </>
          )}
        </main>
      </div>

      <dialog
        ref={dialog}
        className="evidence-dialog"
        onClose={() => setEvidence(null)}
        onClick={(e) => {
          if (e.target === dialog.current) closeEvidence();
        }}
      >
        {evidence && data && filing && (
          <div className="evidence-dialog-content">
            <div className="panel-heading">
              <span className="eyebrow">SOURCE EVIDENCE</span>
              <button
                className="icon-button"
                onClick={closeEvidence}
                aria-label="Close evidence"
              >
                <X size={19} />
              </button>
            </div>
            <h2>
              {evidence.metric?.label || `${evidence.bucket?.label} principal`}
            </h2>
            <p className="evidence-amount">
              {evidence.metric
                ? evidence.metric.unit === "x"
                  ? multiple(evidence.metric.value)
                  : money(evidence.metric.value)
                : money(evidence.bucket?.amount)}
            </p>
            <span className="status-pill">
              {live ? "Live SEC import" : "Offline filing snapshot"}
            </span>
            <div className="source-metadata">
              <span>
                Form {filing.form} · FY{filing.fiscal_year}
              </span>
              <span>
                Filed {filing.filed_at} · Period end {filing.period_end}
              </span>
              <code>{filing.accession}</code>
            </div>
            {evidence.metric && (
              <div className="formula-box">
                <span className="eyebrow">FORMULA & BASIS</span>
                <code>{evidence.metric.formula}</code>
                <p>
                  {evidence.metric.basis}. {evidence.metric.note}
                </p>
              </div>
            )}
            {sourceFacts.map((f) => (
              <section className="evidence-fact" key={f.id}>
                <div>
                  <h3>{title(f.concept)}</h3>
                  <strong>{money(f.amount, false)}</strong>
                </div>
                <span className="validation-text">
                  <CheckCheck size={14} />
                  {title(f.validation_state)} · {title(f.source_type)}
                </span>
                <blockquote>{f.excerpt}</blockquote>
                <dl>
                  <div>
                    <dt>Original value / scale</dt>
                    <dd>
                      {f.original_value} × 10^{f.original_scale}{" "}
                      {f.original_unit}
                    </dd>
                  </div>
                  <div>
                    <dt>Accounting period</dt>
                    <dd>
                      {f.start ? `${f.start} → ` : "Instant: "}
                      {f.end}
                    </dd>
                  </div>
                  <div>
                    <dt>Taxonomy</dt>
                    <dd>
                      <code>{f.taxonomy_tag}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>Method</dt>
                    <dd>{f.extraction_method}</dd>
                  </div>
                </dl>
                <p className="field-note">{f.raw_record.normalization}</p>
                <details>
                  <summary>Actual source reference</summary>
                  <code className="source-ref">{f.source_ref}</code>
                </details>
                <a
                  className="text-button small"
                  href={f.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open filing at source element
                  <ExternalLink size={13} />
                </a>
              </section>
            ))}
            {evidence.bucket && (
              <section className="evidence-fact">
                <span className="validation-text">
                  <CheckCheck size={14} />
                  Cross-checked with filing-specific companyfacts
                </span>
                <blockquote>{evidence.bucket.excerpt}</blockquote>
                <p>{evidence.bucket.source_ref}</p>
                <p className="field-note">
                  Principal excludes finance leases.{" "}
                  {evidence.bucket.kind !== "EXACT_YEAR" &&
                    "No individual-year allocation has been inferred."}
                </p>
                <a
                  className="text-button"
                  href={evidence.bucket.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open original SEC filing
                  <ExternalLink size={14} />
                </a>
              </section>
            )}
            {evidence.metric && !sourceFacts.length && (
              <div className="information-note">
                <InfoIcon />
                No supported source reconciliation is available for this metric.
                It remains unavailable.
              </div>
            )}
            <p className="dialog-disclaimer">
              Cross-checked means deterministic agreement between the inline
              filing and the SEC companyfacts record for this accession and
              period. It does not indicate independent human review.
            </p>
          </div>
        )}
      </dialog>
    </div>
  );
}

function InfoIcon() {
  return <CircleHelp size={16} className="info-icon" />;
}
function PageHeading({
  eyebrow,
  title: heading,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="page-heading">
      <span className="eyebrow">{eyebrow}</span>
      <h1>{heading}</h1>
      <p>{description}</p>
    </div>
  );
}

function Sources({ data }: { data: Dataset }) {
  const q = data.quality;
  return (
    <>
      <div className="section-intro">
        <div>
          <h2>Data quality & source ledger</h2>
          <p>
            Review extraction coverage, exceptions and the evidence behind the
            snapshot.
          </p>
        </div>
        <span className="status-pill">Human review pending</span>
      </div>
      <div className="quality-stats">
        <div>
          <FileCheck2 size={19} />
          <strong>
            {q.cross_checked_core_facts} / {q.expected_core_facts}
          </strong>
          <span>Core facts cross-checked</span>
        </div>
        <div>
          <ChartNoAxesColumnIncreasing size={19} />
          <strong>{q.maturity_buckets}</strong>
          <span>Disclosed maturity buckets</span>
        </div>
        <div>
          <ShieldCheck size={19} />
          <strong>{q.manually_verified_facts}</strong>
          <span>Facts manually verified</span>
        </div>
        <div>
          <Database size={19} />
          <strong>{q.missing_fields.length}</strong>
          <span>Unavailable fields / metrics</span>
        </div>
      </div>
      <div className="information-note">
        <InfoIcon />
        Core-fact coverage uses a defined {q.expected_core_facts}-field
        extraction set. It is not an accuracy score or complete coverage of the
        financial statements. Human verification has not been claimed.
      </div>
      <FinancialReviewPanel key={data.company.id} data={data} />
      <section className="panel">
        <div className="panel-heading">
          <h2>Validation & interpretation notes</h2>
          <span className="count-badge">{q.issues.length}</span>
        </div>
        <div className="issues-list">
          {q.issues.map((issue, i) => (
            <div className="issue" key={i}>
              <span className={`issue-dot ${issue.severity}`} />
              <div>
                <span className="eyebrow">
                  {title(issue.field)} · {issue.severity}
                </span>
                <p>{issue.message}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>Raw-source provenance</h2>
          <span className="eyebrow">SHA-256 RECORDED</span>
        </div>
        <div className="source-ledger">
          {Object.entries(q.source_manifest).map(([url, source]) => (
            <div className="source-ledger-item" key={url}>
              <div>
                <Database size={15} />
                <a href={url} target="_blank" rel="noreferrer">
                  {url.split("/").pop()}
                  <ExternalLink size={12} />
                </a>
                <span>{(source.bytes / 1024).toFixed(0)} KB</span>
              </div>
              <code>{source.sha256}</code>
              <small>
                Retrieved {source.retrieved_at} ·{" "}
                {source.cache_hit ? "validated cache" : "direct request"} at
                import
              </small>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>Fact-level source ledger</h2>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Concept / taxonomy</th>
                <th>Normalized USD</th>
                <th>Source type</th>
                <th>Method</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {data.financials.facts.map((f) => (
                <tr key={f.id}>
                  <td>
                    <strong>{title(f.concept)}</strong>
                    <span className="table-subtext code-label">
                      {f.taxonomy_tag}
                    </span>
                  </td>
                  <td className="mono">{money(f.amount, false)}</td>
                  <td>Document extracted</td>
                  <td>
                    {f.extraction_method === "INLINE_XBRL_AND_COMPANYFACTS"
                      ? "Inline XBRL + companyfacts"
                      : "Inline filing only"}
                    <span className="table-subtext">
                      {title(f.validation_state)}
                    </span>
                  </td>
                  <td>
                    <a
                      className="text-button small"
                      href={f.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Filing
                      <ExternalLink size={12} />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function Methodology() {
  return (
    <>
      <PageHeading
        eyebrow="TRANSPARENT BY DESIGN"
        title="Methodology & assumptions"
        description="Understand the accounting basis before interpreting the output."
      />
      <div className="methodology-grid">
        {[
          [
            "01",
            "Debt is not a single number",
            "Company views retain issuer-specific reported debt carrying amounts and their source components. Nucor includes finance leases; peer comparison explicitly excludes them. Operating leases and undrawn facilities are excluded. Contractual principal uses a different basis.",
          ],
          [
            "02",
            "Cash has a defined scope",
            "Net debt subtracts same-date cash and cash equivalents only. Short-term investments and restricted cash are excluded. Consolidated joint venture cash may not be freely available to the parent.",
          ],
          [
            "03",
            "Keep earnings definitions explicit",
            "Nucor uses a labelled analytical EBIT proxy: pretax earnings plus net interest expense. The other approved issuers use reported consolidated operating income. Each company displays its formula. These differing numerators are not ranked as identical peer ratios. Gross interest expense is the denominator.",
          ],
          [
            "04",
            "Missing EBITDA stays missing",
            "No unsupported EBITDA reconciliation is published. Net debt / EBITDA remains unavailable. A scenario can accept a clearly hypothetical EBITDA baseline; EBITDA is not free cash flow.",
          ],
          [
            "05",
            "A maturity bucket is evidence",
            "Only disclosed, cross-checked long-term principal enters the wall. Thereafter and broad buckets are not spread across years. Carrying debt and contractual principal are never summed together.",
          ],
          [
            "06",
            "Scenarios are annualized sensitivities",
            "Incremental annual interest = selected principal × (new annual rate − previous annual rate). Coverage adds that delta once to historical gross interest expense and applies the chosen decline to the issuer-specific earnings measure. Rates and declines are assumptions.",
          ],
          [
            "07",
            "Cash flow is a separate measure",
            "Free cash flow = annual operating cash flow − cash purchases of property, plant and equipment. Acquisitions are excluded. This is not a forward liquidity-gap model.",
          ],
          [
            "08",
            "Evidence has several dimensions",
            "Live SEC import describes acquisition. Document extracted describes the extraction source. Cross-checked describes agreement with filing-specific XBRL; it is not human review. Offline snapshots and hypothetical inputs retain their own labels.",
          ],
          [
            "09",
            "Annual cash follows explicit assumptions",
            "Opening cash plus operating cash flow, less investment, other uses and principal repayments, plus assumed refinancing, less fees and cumulative interest changes, gives an unfunded year-end balance. Historical interest is already reflected in cash flows. A negative balance is a model shortfall before new uncommitted financing.",
          ],
          [
            "10",
            "Stress cases explain changes, not probabilities",
            "Base, Adverse and Severe use illustrative CFO, capex, rate, refinancing and fee assumptions. Each runs through the same cash model. Five signed contributions reconcile ending cash versus Base. A two-variable grid changes only CFO reduction and new borrowing rate while the remaining assumptions stay fixed.",
          ],
        ].map(([n, heading, text]) => (
          <section className="panel methodology-card" key={n}>
            <span className="step-index">{n}</span>
            <h2>{heading}</h2>
            <p>{text}</p>
          </section>
        ))}
      </div>
      <div className="information-note">
        <InfoIcon />
        The model does not estimate bankruptcy probability, credit ratings,
        credit spreads, refinancing availability, covenant compliance or
        investment suitability. All baseline observations are historical.
      </div>
    </>
  );
}
