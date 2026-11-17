"use client";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Download,
  FlaskConical,
  Info,
  RotateCcw,
} from "lucide-react";
import {
  api,
  Dataset,
  downloadJson,
  money,
  multiple,
  percentToRate,
  rateToPercent,
  Scenario,
  ScenarioInput,
} from "@/lib/api";

export default function ScenarioLab({
  data,
  compact = false,
  onOpenFull,
  initialInputs,
  onInputsChange,
}: {
  data: Dataset;
  compact?: boolean;
  onOpenFull?: (inputs: ScenarioInput) => void;
  initialInputs?: ScenarioInput;
  onInputsChange?: (inputs: ScenarioInput) => void;
}) {
  const buckets = data.maturities.buckets;
  const preferredBucket =
    buckets.slice(1).find((bucket) => Number(bucket.amount) > 0) ||
    buckets.find((bucket) => Number(bucket.amount) > 0) ||
    buckets[0];
  const initialBucket = String(preferredBucket?.id || "custom");
  const earningsLabel =
    data.financials.metrics.find((metric) => metric.key === "ebit_proxy")
      ?.label || "Reference earnings";
  const [bucketId, setBucketId] = useState(
    initialInputs
      ? String(initialInputs.maturity_bucket_id || "custom")
      : initialBucket,
  );
  const [principal, setPrincipal] = useState(
    initialInputs?.principal_assumption || "",
  );
  const [period, setPeriod] = useState(
    initialInputs?.refinancing_period || "User-defined refinancing period",
  );
  const [oldRate, setOldRate] = useState(
    initialInputs ? rateToPercent(initialInputs.previous_rate) : "4",
  );
  const [newRate, setNewRate] = useState(
    initialInputs?.new_rate ? rateToPercent(initialInputs.new_rate) : "6",
  );
  const [rateMode, setRateMode] = useState(
    initialInputs?.spread_basis_points != null ? "bps" : "rate",
  );
  const [bps, setBps] = useState(initialInputs?.spread_basis_points || "200");
  const [ebitDecline, setEbitDecline] = useState(
    initialInputs?.ebit_decline_percent || (compact ? "0" : "20"),
  );
  const [ebitda, setEbitda] = useState(initialInputs?.ebitda_assumption || "");
  const [ebitdaDecline, setEbitdaDecline] = useState(
    initialInputs?.ebitda_decline_percent || "20",
  );
  const [result, setResult] = useState<Scenario | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(true);
  const [calculatedInput, setCalculatedInput] = useState("");
  const selected = buckets.find((b) => String(b.id) === bucketId);
  const filing = data.financials.filing;

  const input = useMemo(() => {
    try {
      const payload: ScenarioInput = {
        company_id: data.company.id,
        filing_id: filing.id,
        as_of: filing.period_end,
        currency: "USD",
        maturity_bucket_id: selected?.id || null,
        principal_assumption: selected ? null : principal || null,
        refinancing_period: selected?.label || period,
        requested_year: null,
        previous_rate: percentToRate(oldRate),
        new_rate: rateMode === "rate" ? percentToRate(newRate) : null,
        spread_basis_points: rateMode === "bps" ? bps : null,
        ebit_decline_percent: ebitDecline,
        ebitda_assumption: ebitda || null,
        ebitda_decline_percent: ebitdaDecline,
        baseline_already_refinanced: false,
      };
      return { payload, error: "" };
    } catch (err) {
      return { payload: null, error: (err as Error).message };
    }
  }, [
    data.company.id,
    filing.id,
    filing.period_end,
    selected,
    principal,
    period,
    oldRate,
    rateMode,
    newRate,
    bps,
    ebitDecline,
    ebitda,
    ebitdaDecline,
  ]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setPending(true);
      setError("");
      if (!input.payload) {
        setError(input.error);
        setResult(null);
        setPending(false);
        return;
      }
      api<Scenario>("scenarios/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input.payload),
        signal: controller.signal,
      })
        .then((value) => {
          if (controller.signal.aborted) return;
          setResult(value);
          onInputsChange?.(value.inputs);
          setCalculatedInput(JSON.stringify(input.payload));
          setPending(false);
        })
        .catch((err) => {
          if (!controller.signal.aborted) {
            setError(err.message);
            setResult(null);
            setPending(false);
          }
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [input, onInputsChange]);
  const stale = calculatedInput !== JSON.stringify(input.payload);

  function reset() {
    setBucketId(initialBucket);
    setPrincipal("");
    setOldRate("4");
    setNewRate("6");
    setRateMode("rate");
    setBps("200");
    setEbitDecline(compact ? "0" : "20");
    setEbitda("");
    setEbitdaDecline("20");
  }

  return (
    <section
      className={`panel scenario-panel ${compact ? "compact-scenario" : ""}`}
      aria-label="Scenario Lab"
    >
      <div className="panel-heading">
        <div>
          <span className="eyebrow accent-text">HYPOTHETICAL SCENARIO</span>
          <h2>
            {!compact && <FlaskConical size={19} />}
            {compact ? "Refinancing scenario" : "Refinancing sensitivity"}
          </h2>
        </div>
        <button
          className="icon-button"
          onClick={reset}
          title="Reset assumptions"
          aria-label="Reset assumptions"
        >
          <RotateCcw size={16} />
        </button>
      </div>
      <div className="scenario-layout">
        <div className="scenario-controls">
          <div className="control-section">
            <span className="step-index">01</span>
            <h3>Choose the refinancing exposure</h3>
          </div>
          <label className="field">
            Principal bucket
            <select
              value={bucketId}
              onChange={(e) => setBucketId(e.target.value)}
              aria-label="Principal bucket"
            >
              {buckets.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.label} · {money(b.amount)}
                  {b.kind !== "EXACT_YEAR" ? " · broad bucket" : ""}
                </option>
              ))}
              <option value="custom">Custom principal assumption</option>
            </select>
          </label>
          {selected ? (
            <p className="field-note">
              <span className="tiny-dot" />
              Source-extracted principal · {selected.label}. Assumes this entire
              bucket is refinanced.
            </p>
          ) : (
            <div className="two-fields">
              <label className="field">
                Hypothetical principal (USD)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={principal}
                  onChange={(e) => setPrincipal(e.target.value)}
                />
              </label>
              <label className="field">
                Refinancing period
                <input
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                />
              </label>
            </div>
          )}
          <div className="control-section">
            <span className="step-index">02</span>
            <h3>Set your rate assumptions</h3>
          </div>
          <div className="two-fields">
            <label className="field">
              Previous annual rate (%)
              <input
                type="number"
                min="0"
                max="100"
                step="0.25"
                value={oldRate}
                onChange={(e) => setOldRate(e.target.value)}
                aria-label="Previous annual rate (%)"
              />
            </label>
            {rateMode === "rate" ? (
              <label className="field">
                New annual rate (%)
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.25"
                  value={newRate}
                  onChange={(e) => setNewRate(e.target.value)}
                  aria-label="New annual rate (%)"
                />
              </label>
            ) : (
              <label className="field">
                Rate change (basis points)
                <input
                  type="number"
                  min="-10000"
                  max="10000"
                  step="25"
                  value={bps}
                  onChange={(e) => setBps(e.target.value)}
                  aria-label="Rate change (basis points)"
                />
              </label>
            )}
          </div>
          <button
            className="text-button small"
            onClick={() => setRateMode(rateMode === "rate" ? "bps" : "rate")}
          >
            {rateMode === "rate"
              ? "Use a basis-point change"
              : "Use a new annual rate"}
            <ArrowRight size={12} />
          </button>
          <p className="field-note">
            Both rates are explicit assumptions; instrument coupons are not
            verified.
          </p>
          {!compact && (
            <>
              <div className="control-section">
                <span className="step-index">03</span>
                <h3>Apply an earnings assumption</h3>
              </div>
              <label className="field range-field">
                {earningsLabel} decline <output>{ebitDecline}%</output>
                <input
                  aria-label={`${earningsLabel} decline`}
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={ebitDecline}
                  onChange={(e) => setEbitDecline(e.target.value)}
                />
              </label>
              <p className="field-note">
                Assumes historical {earningsLabel.toLowerCase()} declines by
                this percentage.
              </p>
              <details className="ebitda-options">
                <summary>
                  Optional EBITDA assumption{" "}
                  <span>Source EBITDA unavailable</span>
                </summary>
                <label className="field">
                  Hypothetical baseline EBITDA (USD)
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={ebitda}
                    onChange={(e) => setEbitda(e.target.value)}
                    placeholder="No assumed value"
                  />
                </label>
                <label className="field">
                  EBITDA decline (%)
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={ebitdaDecline}
                    onChange={(e) => setEbitdaDecline(e.target.value)}
                    aria-label="EBITDA decline (%)"
                  />
                </label>
                <p className="field-note">
                  User input only. This does not become a company observation.
                </p>
              </details>
            </>
          )}
        </div>
        <div
          className="scenario-results"
          aria-live="polite"
          aria-busy={pending || stale}
        >
          <div className="result-topline">
            <span className="eyebrow">Annualized modeled impact</span>
            <span className="status-pill hypothetical">Hypothetical</span>
          </div>
          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}
          {result && !error && !stale && (
            <>
              <div className="impact-value" data-testid="interest-impact">
                {money(result.incremental_annual_interest, true, 2)}
              </div>
              <p className="impact-caption">
                Incremental annual interest after refinancing{" "}
                <span>
                  {Number(result.spread_basis_points).toLocaleString("en-US")}{" "}
                  bps rate change
                </span>
              </p>
              {!compact && (
                <>
                  <div className="comparison-heading">
                    <span>Metric</span>
                    <span>Base case</span>
                    <span>Stress case</span>
                    <span>Delta</span>
                  </div>
                  <div className="comparison-row">
                    <span>Annual interest expense</span>
                    <strong>{money(result.baseline_interest_expense)}</strong>
                    <strong>{money(result.scenario_interest_expense)}</strong>
                    <span className="comparison-delta">
                      {money(result.interest_expense_delta, true, 2)}
                    </span>
                  </div>
                  <div className="comparison-row">
                    <span>{earningsLabel}</span>
                    <strong>{money(result.baseline_ebit_proxy)}</strong>
                    <strong>{money(result.scenario_ebit_proxy)}</strong>
                    <span className="comparison-delta">
                      {money(result.ebit_proxy_delta, true, 2)}
                    </span>
                  </div>
                  <div className="comparison-row coverage-row">
                    <span>Reference earnings / interest</span>
                    <strong>
                      {multiple(result.baseline_interest_coverage)}
                    </strong>
                    <strong data-testid="scenario-coverage">
                      {multiple(result.scenario_interest_coverage)}
                    </strong>
                    <span className="comparison-delta">
                      {multiple(result.interest_coverage_delta)}
                    </span>
                  </div>
                  {result.baseline_ebitda !== null && (
                    <>
                      <div className="comparison-row">
                        <span>EBITDA (user assumption)</span>
                        <strong>{money(result.baseline_ebitda)}</strong>
                        <strong>{money(result.scenario_ebitda)}</strong>
                        <span className="comparison-delta">
                          {money(result.ebitda_delta, true, 2)}
                        </span>
                      </div>
                      <div className="comparison-row">
                        <span>Assumed EBITDA / interest</span>
                        <strong>
                          {multiple(result.baseline_ebitda_coverage)}
                        </strong>
                        <strong>
                          {multiple(result.scenario_ebitda_coverage)}
                        </strong>
                        <span className="comparison-delta">
                          {multiple(result.ebitda_coverage_delta)}
                        </span>
                      </div>
                    </>
                  )}
                </>
              )}
              <div className="formula-box">
                <span className="eyebrow">Deterministic formula</span>
                <code>Selected principal × (new rate − previous rate)</code>
                <p>Formula version: {result.formula_version}</p>
              </div>
              {!compact && (
                <>
                  <button
                    className="secondary-button export-scenario"
                    onClick={() =>
                      downloadJson(
                        result,
                        `refilens-${data.company.ticker.toLowerCase()}-scenario.json`,
                      )
                    }
                    disabled={pending || stale}
                  >
                    <Download size={14} />
                    Export scenario JSON
                  </button>
                </>
              )}
            </>
          )}
          {(pending || stale) && !error && (
            <p className="computing-label">
              Calculating with the research API…
            </p>
          )}
        </div>
      </div>
      {compact && (
        <button
          className="primary-button compact-open-lab"
          onClick={() => {
            if (input.payload) onOpenFull?.(input.payload);
          }}
          disabled={pending || stale || !input.payload || !!error}
        >
          Open single-maturity model <ArrowRight size={14} />
        </button>
      )}
      <div className="panel-footnote">
        <Info size={15} />
        <p>
          {compact
            ? "Assumes the entire selected bucket is refinanced. Both rates are hypothetical. Shows the annualized interest change after refinancing; not an immediate change to all debt."
            : "A full-year sensitivity after the selected refinancing. Fixed-rate debt outside this exposure is unchanged. Historical expenses and the issuer-specific earnings measure are reference points; timing, covenants, taxes and financing access are not modeled. EBITDA is not free cash flow."}
        </p>
      </div>
    </section>
  );
}
