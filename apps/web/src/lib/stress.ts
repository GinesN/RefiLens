import {
  CaseId,
  millionsToMoney,
  moneyToMillions,
  percentToRate,
  rateToPercent,
  StressInput,
} from "./api";

export interface StressDraft {
  companyId: number;
  filingId: number;
  asOf: string;
  opening: string;
  floor: string;
  previous: string;
  horizon: string;
  selected: CaseId;
  cases: {
    id: CaseId;
    cfo: string;
    capex: string;
    rate: string;
    refinance: string;
    fee: string;
  }[];
  other: { year: number; value: string }[];
}
export function stressDraftFromInput(input: StressInput): StressDraft {
  return {
    companyId: input.company_id,
    filingId: input.filing_id,
    asOf: input.as_of,
    opening: moneyToMillions(input.available_cash_assumption),
    floor: moneyToMillions(input.minimum_cash),
    previous: rateToPercent(input.previous_rate),
    horizon: String(input.horizon_years),
    selected: input.sensitivity_case_id,
    cases: input.cases.map((profile) => ({
      id: profile.id,
      cfo: rateToPercent(profile.cfo_decline_fraction),
      capex: rateToPercent(profile.capex_fraction),
      rate: rateToPercent(profile.new_rate),
      refinance: rateToPercent(profile.refinance_fraction),
      fee: rateToPercent(profile.issuance_fee_rate),
    })),
    other: input.other_cash_uses.map((row) => ({
      year: row.year,
      value: moneyToMillions(row.amount),
    })),
  };
}
export function stressInputFromDraft(draft: StressDraft): StressInput {
  const field = (label: string, convert: () => string): string => {
    try {
      return convert();
    } catch (error) {
      throw new Error(
        `${label}: ${error instanceof Error ? error.message : "Invalid input."}`,
      );
    }
  };
  return {
    company_id: draft.companyId,
    filing_id: draft.filingId,
    as_of: draft.asOf,
    currency: "USD",
    available_cash_assumption: field("Available opening cash", () =>
      millionsToMoney(draft.opening),
    ),
    minimum_cash: field("Minimum cash floor", () =>
      millionsToMoney(draft.floor),
    ),
    previous_rate: field("Original coupon assumption", () =>
      percentToRate(draft.previous),
    ),
    horizon_years: Number(draft.horizon),
    sensitivity_case_id: draft.selected,
    cases: draft.cases.map((profile) => ({
      id: profile.id,
      cfo_decline_fraction: field(
        `${profile.id} operating cash flow reduction`,
        () => percentToRate(profile.cfo),
      ),
      capex_fraction: field(`${profile.id} cash capex`, () =>
        percentToRate(profile.capex, 200),
      ),
      new_rate: field(`${profile.id} new borrowing rate`, () =>
        percentToRate(profile.rate),
      ),
      refinance_fraction: field(`${profile.id} principal refinanced`, () =>
        percentToRate(profile.refinance),
      ),
      issuance_fee_rate: field(`${profile.id} issuance fee`, () =>
        percentToRate(profile.fee),
      ),
    })),
    other_cash_uses: draft.other.map((row) => ({
      year: row.year,
      amount: field(`${row.year} other cash uses`, () =>
        millionsToMoney(row.value),
      ),
    })),
  };
}
