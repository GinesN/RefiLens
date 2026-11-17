import { describe, expect, it } from "vitest";
import {
  money,
  multiple,
  percentToRate,
  rateToPercent,
  moneyToMillions,
  millionsToMoney,
} from "./api";

describe("presentation and input conversion", () => {
  it("keeps missing financial values visibly unavailable", () => {
    expect(money(null)).toBe("Not available");
    expect(multiple(null)).toBe("Not available");
    expect(money("-188000000")).toBe("−$188M");
    expect(money("7121000000")).toBe("$7.12B");
  });
  it("converts user percentage strings without binary arithmetic", () => {
    expect(percentToRate("6.375")).toBe("0.06375");
    expect(rateToPercent("0.06375")).toBe("6.375");
    expect(rateToPercent("0.04125000")).toBe("4.125");
    expect(rateToPercent("0.00")).toBe("0");
    expect(rateToPercent("1.00")).toBe("100");
    expect(percentToRate("0")).toBe("0.00");
    expect(percentToRate("100")).toBe("1.00");
    expect(() => percentToRate("100.000001")).toThrow("between 0% and 100%");
    expect(() => percentToRate("110")).toThrow("between 0% and 100%");
    expect(() => percentToRate("-1")).toThrow();
  });
  it("rounds displayed compact amounts consistently at decimal half boundaries", () => {
    expect(money("137265000.0000", true, 2)).toBe("$137.27M");
    expect(money("-137265000.0000", true, 2)).toBe("−$137.27M");
    expect(money("362735000.0000", true, 2)).toBe("$362.74M");
  });
  it("preserves exact currency-unit conversions and distinguishes blank from zero", () => {
    expect(moneyToMillions("769878000")).toBe("769.878");
    expect(moneyToMillions("216600000.0")).toBe("216.6");
    expect(moneyToMillions("-188000000")).toBe("-188");
    expect(millionsToMoney("769.878")).toBe("769878000.00");
    expect(millionsToMoney("0.00000001")).toBe("0.01");
    expect(millionsToMoney("-0.00000001", true)).toBe("-0.01");
    expect(millionsToMoney("-188", true)).toBe("-188000000.00");
    expect(millionsToMoney("0")).toBe("0.00");
    expect(() => millionsToMoney("")).toThrow();
    expect(() => millionsToMoney("-1")).toThrow();
    expect(() => millionsToMoney("0.000000001")).toThrow();
  });
});
