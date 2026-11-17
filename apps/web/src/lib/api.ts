export type DecimalString = string;
export interface Filing {
  id: number;
  accession: string;
  form: string;
  filed_at: string;
  period_start: string;
  period_end: string;
  fiscal_year: number;
  source_url: string;
  acquisition_mode: string;
  imported_at: string;
}
export interface Company {
  id: number;
  ticker: string;
  name: string;
  cik: string;
  industry: string;
  sic: string;
  filing: Filing | null;
  research_profile: {
    sector?: string;
    business_model?: string;
    exchange?: string;
    debt_basis?: string;
    includes_finance_leases?: boolean;
    comparability_note?: string;
    maturity_scope?: string;
    short_term_outside_maturities?: boolean;
  };
}
export interface Fact {
  id: number;
  filing_id: number;
  concept: string;
  taxonomy_tag: string;
  currency: string;
  original_unit: string;
  original_value: string;
  original_scale: number;
  amount: DecimalString;
  start: string | null;
  end: string;
  period: string;
  source_type: string;
  source_url: string;
  source_ref: string;
  excerpt: string;
  extraction_method: string;
  validation_state: string;
  raw_record: {
    normalization?: string;
    taxonomy_amount?: string;
    [key: string]: unknown;
  };
}
export interface Metric {
  key: string;
  label: string;
  value: DecimalString | null;
  unit: string;
  basis: string;
  formula: string;
  fact_ids: number[];
  status: string;
  note: string;
}
export interface Financials {
  filing: Filing;
  metrics: Metric[];
  facts: Fact[];
}
export interface Bucket {
  id: number;
  label: string;
  kind: string;
  year_start: number | null;
  year_end: number | null;
  amount: DecimalString;
  currency: string;
  category: string;
  as_of: string;
  source_url: string;
  source_ref: string;
  excerpt: string;
  validation_state: string;
}
export interface Maturities {
  filing: Filing;
  buckets: Bucket[];
  total_principal: DecimalString | null;
  carrying_debt: DecimalString | null;
  scope_difference: DecimalString | null;
  reconciliation_note: string;
  near_term_principal: string | null;
  near_term_share: string | null;
  near_term_years: number[];
  next_positive_bucket_id: number | null;
  next_positive_year: number | null;
  next_positive_principal: string | null;
}
export interface Quality {
  filing: Filing;
  expected_core_facts: number;
  extracted_core_facts: number;
  cross_checked_core_facts: number;
  manually_verified_facts: number;
  missing_fields: string[];
  maturity_buckets: number;
  issues: {
    severity: string;
    field: string;
    message: string;
    resolved: boolean;
  }[];
  source_manifest: Record<
    string,
    { sha256: string; retrieved_at: string; bytes: number; cache_hit: boolean }
  >;
}
export interface Brief {
  company: Company;
  paragraphs: string[];
  methodology_version: string;
  source_urls: string[];
}
export interface FinancialReview {
  filing: Filing;
  review_kind: string;
  human_review_completed: boolean;
  checks: {
    key: string;
    label: string;
    status: "PASS" | "EXPLAINED" | "FAIL" | "UNAVAILABLE";
    detail: string;
    difference: string | null;
    fact_ids: number[];
  }[];
  debt_bridge: { label: string; amount: string | null; fact_ids: number[] }[];
  reconstructed_debt: string | null;
  carrying_debt: string | null;
  debt_bridge_difference: string | null;
  note_principal: string | null;
  scheduled_principal: string | null;
  maturity_difference: string | null;
  maturity_rounding_bound: string | null;
  cash_flow_cash_difference: string | null;
  notes: string[];
}
export interface LiquidityInput {
  company_id: number;
  filing_id: number;
  as_of: string;
  currency: "USD";
  available_cash_assumption: string;
  minimum_cash: string;
  previous_rate: string;
  new_rate: string;
  refinance_fraction: string;
  issuance_fee_rate: string;
  cash_flow_already_adjusted: boolean;
  years: {
    year: number;
    operating_cash_flow: string;
    capital_expenditure: string;
    other_cash_uses: string;
  }[];
}
export interface LiquidityYear {
  year: number;
  opening_cash: string;
  operating_cash_flow_assumption: string;
  capital_expenditure_assumption: string;
  other_cash_uses_assumption: string;
  scheduled_principal: string;
  refinanced_principal: string;
  principal_repaid_from_cash: string;
  interest_change_for_new_maturities: string;
  cumulative_interest_change: string;
  reference_interest_after_changes: string;
  issuance_fees: string;
  closing_cash_before_uncommitted_funding: string;
  shortfall_to_minimum_cash: string;
  cumulative_refinanced_principal: string;
}
export interface LiquidityResult {
  hypothetical: boolean;
  formula_version: string;
  filing: Filing;
  inputs: LiquidityInput;
  source_cash: string;
  source_operating_cash_flow: string;
  source_capital_expenditure: string;
  source_interest_expense: string;
  excluded_principal: string;
  excluded_bucket_labels: string[];
  years: LiquidityYear[];
  closing_cash_before_uncommitted_funding: string;
  peak_shortfall: string;
  first_shortfall_year: number | null;
  total_refinanced_principal: string;
  conclusion: string;
  warnings: string[];
}
export type CaseId = "base" | "adverse" | "severe";
export interface StressCaseInput {
  id: CaseId;
  cfo_decline_fraction: string;
  capex_fraction: string;
  new_rate: string;
  refinance_fraction: string;
  issuance_fee_rate: string;
}
export interface StressInput {
  company_id: number;
  filing_id: number;
  as_of: string;
  currency: "USD";
  available_cash_assumption: string;
  minimum_cash: string;
  previous_rate: string;
  horizon_years: number;
  sensitivity_case_id: CaseId;
  cases: StressCaseInput[];
  other_cash_uses: { year: number; amount: string }[];
}
export interface StressDefaults {
  inputs: StressInput;
  assumption_origin: string;
  rationale: string[];
}
export type CashProjection = Pick<
  LiquidityResult,
  | "formula_version"
  | "years"
  | "closing_cash_before_uncommitted_funding"
  | "peak_shortfall"
  | "first_shortfall_year"
  | "total_refinanced_principal"
>;
export interface StressResult {
  hypothetical: boolean;
  formula_version: string;
  assumption_origin: string;
  filing: Filing;
  inputs: StressInput;
  source_cash: string;
  source_operating_cash_flow: string;
  source_capital_expenditure: string;
  source_interest_expense: string;
  excluded_principal: string;
  excluded_bucket_labels: string[];
  cases: {
    id: CaseId;
    label: string;
    profile: StressCaseInput;
    resolved_inputs: LiquidityInput;
    projection: CashProjection;
    ending_cash_change_vs_base: string;
    cash_change_drivers: { key: string; label: string; amount: string }[];
    driver_reconciliation_difference: string;
    largest_cash_reduction_vs_base: string | null;
    explanation: string;
  }[];
  sensitivity_case_id: CaseId;
  rate_axis: string[];
  cfo_axis: string[];
  sensitivity_cells: {
    cfo_decline_fraction: string;
    new_rate: string;
    available: boolean;
    peak_shortfall: string | null;
    first_shortfall_year: number | null;
    reason: string | null;
    is_selected: boolean;
  }[];
  assumptions_ordered_by_severity: boolean;
  notes: string[];
}
export interface Dataset {
  company: Company;
  financials: Financials;
  maturities: Maturities;
  quality: Quality;
  brief: Brief;
}
export interface PeerComparisonData {
  enabled: boolean;
  cohort: string;
  currency: string;
  period_end: string;
  debt_definition: string;
  rows: {
    company: Company;
    metrics: Metric[];
    principal_2026_2027: string;
    total_scheduled_principal: string;
    core_facts_checked: number;
    expected_core_facts: number;
  }[];
  notes: string[];
}
export interface ScenarioInput {
  company_id: number;
  filing_id: number;
  as_of: string;
  currency: "USD";
  maturity_bucket_id: number | null;
  principal_assumption: string | null;
  refinancing_period: string;
  requested_year: number | null;
  previous_rate: string;
  new_rate: string | null;
  spread_basis_points: string | null;
  ebit_decline_percent: string;
  ebitda_assumption: string | null;
  ebitda_decline_percent: string;
  baseline_already_refinanced: boolean;
}
export interface Scenario {
  hypothetical: boolean;
  formula_version: string;
  filing: Filing;
  inputs: ScenarioInput;
  resolved_principal: string;
  principal_basis: string;
  resolved_new_rate: string;
  incremental_annual_interest: string;
  spread_basis_points: string;
  baseline_interest_expense: string | null;
  scenario_interest_expense: string | null;
  baseline_ebit_proxy: string | null;
  scenario_ebit_proxy: string | null;
  baseline_ebitda: string | null;
  scenario_ebitda: string | null;
  baseline_interest_coverage: string | null;
  scenario_interest_coverage: string | null;
  baseline_ebitda_coverage: string | null;
  scenario_ebitda_coverage: string | null;
  interest_expense_delta: string | null;
  ebit_proxy_delta: string | null;
  ebitda_delta: string | null;
  interest_coverage_delta: string | null;
  ebitda_coverage_delta: string | null;
  warnings: string[];
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/${path}`, { ...init, cache: "no-store" });
  const value = await response.json();
  if (!response.ok) {
    const detail = value.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((v: { msg: string }) => v.msg).join("; ")
          : "Request failed.",
    );
  }
  return value as T;
}

// Number conversions below are for presentation only. All financial outputs come from Python Decimal.
export function money(
  value: string | null | undefined,
  compact = true,
  precision?: number,
): string {
  if (value == null) return "Not available";
  const n = Number(value);
  if (!Number.isFinite(n)) return "Not available";
  const sign = n < 0 ? "−" : "";
  const abs = Math.abs(n);
  const abbreviated = (amount: number, digits: number) =>
    new Intl.NumberFormat("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
      useGrouping: false,
    }).format(amount);
  if (compact && abs >= 1e9)
    return `${sign}$${abbreviated(abs / 1e9, precision ?? 2)}B`;
  if (compact && abs >= 1e6)
    return `${sign}$${abbreviated(abs / 1e6, precision ?? (abs < 10e6 ? 2 : 0))}M`;
  return `${sign}$${abs.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}
export function multiple(value: string | null | undefined): string {
  return value == null ? "Not available" : `${Number(value).toFixed(2)}×`;
}
export function dateLabel(value: string): string {
  return new Date(`${value}T12:00:00Z`).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}
export function title(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
export function percentToRate(value: string, maximumPercent = 100): string {
  if (!/^\d+(\.\d{0,6})?$/.test(value))
    throw new Error(
      "Enter a valid nonnegative percentage with at most six decimal places.",
    );
  const [whole, fraction = ""] = value.split(".");
  if (
    BigInt(whole) > BigInt(maximumPercent) ||
    (BigInt(whole) === BigInt(maximumPercent) && /[1-9]/.test(fraction))
  ) {
    throw new Error(
      maximumPercent === 100
        ? "Enter an annual rate between 0% and 100%."
        : `Enter a percentage between 0% and ${maximumPercent}%.`,
    );
  }
  const digits = whole.padStart(3, "0");
  return `${digits.slice(0, -2)}.${digits.slice(-2)}${fraction}`;
}
export function rateToPercent(value: string): string {
  const [whole, fraction = ""] = value.split(".");
  const padded = fraction.padEnd(2, "0");
  const integer = `${whole}${padded.slice(0, 2)}`.replace(/^0+(?=\d)/, "");
  const remainder = padded.slice(2).replace(/0+$/, "");
  return remainder ? `${integer}.${remainder}` : integer;
}
export function downloadJson(value: unknown, filename: string) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// Exact unit conversion only. Financial projections are calculated by Python Decimal.
export function millionsToMoney(value: string, allowNegative = false): string {
  if (
    !/^-?\d+(\.\d{0,8})?$/.test(value) ||
    (!allowNegative && value.startsWith("-"))
  )
    throw new Error(
      "Enter a valid amount in USD millions, with at most eight decimal places. Cash uses cannot be negative.",
    );
  const negative = value.startsWith("-");
  const [whole, fraction = ""] = value.replace(/^-/, "").split(".");
  const cents = BigInt(whole) * 100_000_000n + BigInt(fraction.padEnd(8, "0"));
  return `${negative && cents !== 0n ? "-" : ""}${cents / 100n}.${(cents % 100n).toString().padStart(2, "0")}`;
}
export function moneyToMillions(value: string): string {
  if (!/^-?\d+(\.\d+)?$/.test(value))
    throw new Error("Source amount is not a decimal string.");
  const negative = value.startsWith("-");
  const [whole, fraction = ""] = value.replace(/^-/, "").split(".");
  const padded = whole.padStart(7, "0");
  const integer = padded.slice(0, -6).replace(/^0+(?=\d)/, "");
  const decimals = `${padded.slice(-6)}${fraction}`.replace(/0+$/, "");
  return `${negative ? "-" : ""}${integer}${decimals ? "." + decimals : ""}`;
}

export interface ResearchCase {
  id: "reference" | "cash_pressure" | "funding_pressure" | "pause_buybacks";
  label: string;
  rationale: string;
  annual_buybacks_assumption: string;
  inputs: LiquidityInput;
  projection: CashProjection;
}
export interface CaseStudy {
  available: boolean;
  reason: string | null;
  filing: Filing;
  hypothetical: boolean;
  human_review_completed: boolean;
  excluded_principal: string | null;
  excluded_bucket_labels: string[];
  source_manifest: Record<string, unknown>;
  evidence: {
    key: string;
    label: string;
    amount: string;
    currency: "USD";
    period_start: string | null;
    period_end: string;
    kind: "HISTORICAL_REPORTED" | "MANAGEMENT_ESTIMATE" | "DISCLOSED_CAPACITY";
    validation_state: string;
    source_url: string;
    source_ref: string;
    taxonomy_tag: string | null;
    context_ref: string | null;
    original_value: string | null;
    scale: number | null;
    companyfacts_record: Record<string, unknown> | null;
  }[];
  report: {
    formula_version: string;
    title: string;
    question: string;
    information_cutoff: string;
    as_of: string;
    starting_cash: string;
    historical_cfo: string;
    historical_cash_capex: string;
    historical_free_cash_flow: string;
    historical_coverage_proxy: string | null;
    near_term_principal: string;
    minimum_cash_assumption: string;
    observed_cfo_deterioration: string;
    recurring_other_uses_before_buybacks: string;
    cash_preserved_by_pausing_buybacks: string;
    remaining_cash_floor_gap: string;
    minimum_additional_annual_cash_improvement: string;
    cases: ResearchCase[];
    assumptions: string[];
    limitations: string[];
    memo_markdown: string;
  } | null;
}
