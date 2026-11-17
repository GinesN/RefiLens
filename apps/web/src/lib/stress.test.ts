import { describe, expect, it } from "vitest";
import { StressInput } from "./api";
import { stressDraftFromInput, stressInputFromDraft } from "./stress";

// SYNTHETIC input settings test exact unit conversion, not observed company data.
const fixture: StressInput = {
  company_id: 7,
  filing_id: 12,
  as_of: "2025-12-31",
  currency: "USD",
  available_cash_assumption: "769878000",
  minimum_cash: "0",
  previous_rate: "0.04125",
  horizon_years: 5,
  sensitivity_case_id: "severe",
  cases: ["base", "adverse", "severe"].map((id) => ({
    id: id as "base" | "adverse" | "severe",
    cfo_decline_fraction: "0.33333333",
    capex_fraction: "1.12345678",
    new_rate: "0.07375",
    refinance_fraction: "0.5",
    issuance_fee_rate: "0.01",
  })),
  other_cash_uses: [{ year: 2026, amount: "0" }],
};
describe("stress-case input conversion", () => {
  it("preserves exact rates, money and source binding through the editable draft", () => {
    const draft = stressDraftFromInput(fixture);
    expect(draft.opening).toBe("769.878");
    expect(draft.previous).toBe("4.125");
    expect(draft.cases[0].cfo).toBe("33.333333");
    expect(draft.cases[0].capex).toBe("112.345678");
    const input = stressInputFromDraft(draft);
    expect(input.available_cash_assumption).toBe("769878000.00");
    expect(input.previous_rate).toBe("0.04125");
    expect(input.cases[0].new_rate).toBe("0.07375");
    expect(input.cases[0].capex_fraction).toBe("1.12345678");
    expect(input.company_id).toBe(7);
    expect(input.filing_id).toBe(12);
    expect(input.sensitivity_case_id).toBe("severe");
    expect(input.other_cash_uses[0].amount).toBe("0.00");
  });
  it("accepts explicit zero and 200% capex while refusing missing or out-of-range drivers", () => {
    const draft = stressDraftFromInput(fixture);
    draft.cases[0].capex = "200";
    draft.cases[0].cfo = "0";
    expect(stressInputFromDraft(draft).cases[0].capex_fraction).toBe("2.00");
    expect(stressInputFromDraft(draft).cases[0].cfo_decline_fraction).toBe(
      "0.00",
    );
    draft.cases[0].capex = "200.000001";
    expect(() => stressInputFromDraft(draft)).toThrow("200%");
    draft.cases[0].capex = "100";
    draft.cases[0].cfo = "";
    expect(() => stressInputFromDraft(draft)).toThrow();
  });
});
