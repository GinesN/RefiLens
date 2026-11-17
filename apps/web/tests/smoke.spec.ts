import { expect, test, Page } from "@playwright/test";
import { readFile } from "node:fs/promises";

async function navigateResearch(page: Page, name: string) {
  const button = page
    .getByRole("navigation", { name: "Main navigation", exact: true })
    .getByRole("button", { name, exact: true });
  if (!(await button.isVisible()))
    await page
      .getByRole("button", { name: "Toggle navigation", exact: true })
      .click();
  await button.click();
  if ((page.viewportSize()?.width ?? 1440) <= 820)
    await expect(page.locator(".workbench-sidebar")).toBeHidden();
}

async function scenarioTool(page: Page, name: string) {
  await page
    .getByRole("navigation", { name: "Scenario tools", exact: true })
    .getByRole("button", { name: new RegExp("^" + name) })
    .click();
}

test("stress cases calculate independently, explain changes and transfer exact annual assumptions", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/?company=NUE#stress");
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("$1.09B");
  await page.getByRole("button", { name: "Severe", exact: true }).click();
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("−$6.47B");
  await expect(page.getByTestId("stress-first-shortfall")).toHaveText("2027");
  await expect(page.getByTestId("stress-explanation")).toContainText(
    "operating cash flow",
  );
  await expect(page.getByTestId("sensitivity-selected")).toContainText("$6.5B");
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export stress cases JSON", exact: true })
    .click();
  const file = await download;
  const result = JSON.parse(await readFile((await file.path())!, "utf8"));
  expect(result.hypothetical).toBe(true);
  expect(result.inputs.sensitivity_case_id).toBe("severe");
  expect(result.cases).toHaveLength(3);
  expect(Number(result.cases[2].projection.peak_shortfall)).toBe(6468330000);
  expect(Number(result.cases[2].driver_reconciliation_difference)).toBe(0);
  await page
    .getByRole("button", { name: "Explore Severe year by year", exact: true })
    .click();
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText("−$6.47B");
  await expect(
    page.getByLabel("New borrowing rate (%)", { exact: true }),
  ).toHaveValue("10");
  await expect(
    page.getByLabel("Principal refinanced (%)", { exact: true }),
  ).toHaveValue("50");
  await expect(
    page.getByLabel("2026 operating cash flow (USDm)", { exact: true }),
  ).toHaveValue("1940.4");
  await scenarioTool(page, "Stress scenarios");
  await expect(
    page.getByRole("button", { name: "Severe", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("−$6.47B");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.screenshot({
    path: testInfo.outputPath("stress-scenarios.png"),
    fullPage: testInfo.project.name !== "webkit",
  });
  await page
    .getByText("Shared cash settings and other outflows", { exact: false })
    .click();
  await page
    .getByLabel("Stress projection horizon", { exact: true })
    .selectOption("2");
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("−$1.14B");
  await page
    .getByRole("button", { name: "Explore Severe year by year", exact: true })
    .click();
  await expect(
    page.getByLabel("Projection horizon", { exact: true }),
  ).toHaveValue("2");
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText("−$1.14B");
  await page
    .getByLabel("Projection horizon", { exact: true })
    .selectOption("5");
  await expect(
    page.getByLabel("2028 operating cash flow (USDm)", { exact: true }),
  ).toHaveValue("1940.4");
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText("−$6.47B");
  await scenarioTool(page, "Stress scenarios");
  await page
    .getByText("Shared cash settings and other outflows", { exact: false })
    .click();
  await page
    .getByLabel("Stress projection horizon", { exact: true })
    .selectOption("5");
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("−$6.47B");
  await page.getByText("Edit case assumptions", { exact: true }).click();
  expect(
    await page
      .getByRole("region", { name: "Editable case assumptions", exact: true })
      .locator("tbody th")
      .evaluateAll((cells) =>
        cells.every((cell) => cell.scrollWidth <= cell.clientWidth),
      ),
  ).toBe(true);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .getByLabel("Severe operating cash flow reduction (%)", { exact: true })
    .fill("35");
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("−$5.66B");
  await page
    .getByLabel("Severe new borrowing rate (%)", { exact: true })
    .fill("110");
  await expect(
    page.getByRole("alert").filter({ hasText: "between 0% and 100%" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Export stress cases JSON", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Reset stress assumptions", exact: true })
    .click();
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("$1.09B");
  expect(errors).toEqual([]);
});

test("source-first overview and scenario navigation preserve drafts within the selected issuer", async ({
  page,
}) => {
  await page.goto("/?company=NUE#overview");
  await expect(page.getByTestId("near-term-principal")).toHaveText("$598.00M");
  await page
    .getByRole("button", { name: "Compare stress scenarios", exact: true })
    .click();
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("$1.09B");
  await page.getByText("Edit case assumptions", { exact: true }).click();
  await page
    .getByLabel("Adverse operating cash flow reduction (%)", { exact: true })
    .fill("25");
  await expect(
    page.getByRole("button", { name: "Export stress cases JSON", exact: true }),
  ).toBeVisible();
  await scenarioTool(page, "Annual cash model");
  await page
    .getByLabel("Minimum cash floor (USDm)", { exact: true })
    .fill("500");
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText("$1.09B");
  await scenarioTool(page, "Stress scenarios");
  await expect(
    page.getByLabel("Adverse operating cash flow reduction (%)", {
      exact: true,
    }),
  ).toHaveValue("25");
  await page.getByRole("button", { name: "Adverse", exact: true }).click();
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("−$3.53B");
  await scenarioTool(page, "Annual cash model");
  await expect(
    page.getByLabel("Minimum cash floor (USDm)", { exact: true }),
  ).toHaveValue("500");
  await navigateResearch(page, "Company overview");
  await page
    .getByRole("button", { name: "View financial details", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Financial profile", exact: true }),
  ).toBeVisible();
  const companies = await (await page.request.get("/api/companies")).json();
  const stld = companies.find((c: { ticker: string }) => c.ticker === "STLD");
  await page
    .getByLabel("Selected company", { exact: true })
    .selectOption(String(stld.id));
  await expect(
    page.getByRole("heading", { name: "Steel Dynamics Inc", exact: true }),
  ).toBeVisible();
  await navigateResearch(page, "Scenario analysis");
  await expect(
    page.getByLabel("Adverse operating cash flow reduction (%)", {
      exact: true,
    }),
  ).toHaveValue("20");
  await expect(page.getByTestId("stress-ending-cash")).toHaveText("$3.19B");
  await scenarioTool(page, "Annual cash model");
  await expect(
    page.getByLabel("Minimum cash floor (USDm)", { exact: true }),
  ).toHaveValue("0");
  await expect(
    page.getByLabel("Available opening cash (USDm)", { exact: true }),
  ).toHaveValue("769.878");
});

test("annual liquidity keeps cash deficits unfunded, exports exact inputs and resets", async ({
  page,
}, testInfo) => {
  await page.goto("/?company=NUE#liquidity");
  await expect(
    page.getByRole("heading", { name: "Annual liquidity model", exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText("$1.09B");
  await page.getByLabel("Principal refinanced (%)", { exact: true }).fill("0");
  await expect(page.getByTestId("liquidity-peak-shortfall")).toHaveText(
    "$836.52M",
  );
  await expect(page.getByTestId("liquidity-first-shortfall")).toHaveText(
    "2030",
  );
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export liquidity model JSON", exact: true })
    .click();
  const file = await download;
  const result = JSON.parse(await readFile((await file.path())!, "utf8"));
  expect(result.hypothetical).toBe(true);
  expect(Number(result.peak_shortfall)).toBe(836520000);
  expect(result.inputs.refinance_fraction).toBe("0.00");
  expect(result.inputs.years).toHaveLength(5);
  expect(Number(result.excluded_principal)).toBe(4690000000);
  expect(result.years[4].closing_cash_before_uncommitted_funding).toMatch(/^-/);
  await page
    .getByLabel("2026 operating cash flow (USDm)", { exact: true })
    .fill("");
  await expect(
    page.getByRole("alert").filter({ hasText: "valid amount" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Export liquidity model JSON",
      exact: true,
    }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Reset liquidity assumptions", exact: true })
    .click();
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText("$1.09B");
  await page
    .getByLabel("Projection horizon", { exact: true })
    .selectOption("2");
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText("$1.75B");
  await expect(
    page.getByText("Principal outside this horizon:", { exact: false }),
  ).toContainText("$6,338,000,000");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.screenshot({
    path: testInfo.outputPath("liquidity.png"),
    fullPage: testInfo.project.name !== "webkit",
  });
  const companies = await (await page.request.get("/api/companies")).json();
  const stld = companies.find(
    (company: { ticker: string }) => company.ticker === "STLD",
  );
  await page
    .getByLabel("Selected company", { exact: true })
    .selectOption(String(stld.id));
  await expect(
    page.getByLabel("Available opening cash (USDm)", { exact: true }),
  ).toHaveValue("769.878");
  await expect(
    page.getByLabel("Projection horizon", { exact: true }),
  ).toHaveValue("5");
  await expect(
    page.getByLabel("2026 operating cash flow (USDm)", { exact: true }),
  ).toHaveValue("1449.534");
  await expect(page.getByTestId("liquidity-ending-cash")).toBeVisible();
});

test("financial review shows actual debt bridges, source rounding and a downloadable workbook", async ({
  page,
}, testInfo) => {
  await page.goto("/?company=NUE#sources");
  await expect(
    page.getByRole("region", { name: "Financial review", exact: true }),
  ).toBeVisible();
  // macOS WebKit follows Safari's Option-Tab behavior for links.
  await page.keyboard.press(
    testInfo.project.use.browserName === "webkit" &&
      process.platform === "darwin"
      ? "Alt+Tab"
      : "Tab",
  );
  await expect(page.locator(".skip-link")).toBeFocused();
  await expect(page.locator(".skip-link")).toHaveCSS("clip-path", "none");
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
  await expect(page).toHaveURL(/#sources$/);
  const review = page.getByRole("region", {
    name: "Financial review",
    exact: true,
  });
  await expect(review.getByTestId("debt-bridge-difference")).toContainText(
    "$0",
  );
  await expect(review).toContainText("$159,000,000");
  await expect(review).toContainText("$32,000,000");
  await expect(review).toContainText("$4,000,000");
  await expect(review).toContainText("SOURCE_EXTRACTED");
  const download = page.waitForEvent("download");
  await review
    .getByRole("link", { name: "Download financial review Excel", exact: true })
    .click();
  const file = await download;
  const bytes = await readFile((await file.path())!);
  expect(bytes.subarray(0, 2).toString()).toBe("PK");
  const exported = page.waitForEvent("download");
  await review
    .getByRole("button", { name: "Export financial review JSON", exact: true })
    .click();
  const json = JSON.parse(
    await readFile((await (await exported).path())!, "utf8"),
  );
  expect(json.human_review_completed).toBe(false);
  expect(Number(json.debt_bridge_difference)).toBe(0);
  const companies = await (await page.request.get("/api/companies")).json();
  await page
    .getByLabel("Selected company", { exact: true })
    .selectOption(
      String(companies.find((c: { ticker: string }) => c.ticker === "STLD").id),
    );
  await expect(
    page.getByRole("region", { name: "Financial review", exact: true }),
  ).toContainText("$5,394,000");
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  if (testInfo.project.name === "webkit") {
    await page.screenshot({
      path: testInfo.outputPath("financial-review.png"),
    });
  } else {
    await page
      .getByRole("region", { name: "Financial review", exact: true })
      .screenshot({ path: testInfo.outputPath("financial-review.png") });
  }
});

test("filing evidence, maturity wall and deterministic scenario stay connected", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/?company=NUE#overview");
  await expect(
    page.getByRole("heading", { name: "Nucor Corp", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Inspect Gross financial debt evidence" }),
  ).toContainText("$7.12B");
  await page
    .getByRole("button", { name: "Inspect Gross financial debt evidence" })
    .click();
  await expect(page.getByRole("dialog")).toContainText("0001193125-26-071575");
  await expect(page.getByRole("dialog")).toContainText("Short Term Debt");
  await page.getByRole("button", { name: "Close evidence" }).click();
  await navigateResearch(page, "Debt maturities");
  await expect(
    page.getByRole("cell", { name: "Thereafter", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "$4,690,000,000", exact: true }),
  ).toBeVisible();
  await navigateResearch(page, "Scenario analysis");
  await page
    .getByRole("button", { name: "Single maturity", exact: false })
    .click();
  await expect(page.getByTestId("interest-impact")).toHaveText("$10.64M");
  await page.getByLabel("New annual rate (%)", { exact: true }).fill("8");
  await expect(page.getByTestId("interest-impact")).toHaveText("$21.28M");
  await expect(page.getByTestId("scenario-coverage")).toHaveText("10.99×");
  await page.getByRole("button", { name: "Reset assumptions" }).click();
  await expect(page.getByTestId("interest-impact")).toHaveText("$10.64M");
  await navigateResearch(page, "Data quality & sources");
  await expect(
    page.getByRole("heading", { name: "Data quality & source ledger" }),
  ).toBeVisible();
  await expect(
    page.getByText("Facts manually verified", { exact: true }),
  ).toBeVisible();
  await navigateResearch(page, "Company overview");
  await expect(
    page.getByRole("heading", { name: "Financial position" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await expect(page.getByTestId("interest-impact")).toHaveText("$10.64M");
  await page.screenshot({
    path: testInfo.outputPath("overview.png"),
    fullPage: testInfo.project.name !== "webkit",
  });
  expect(errors).toEqual([]);
});

test("assumptions export honestly, invalid rates fail, and research navigation works", async ({
  page,
}) => {
  await page.goto("/#scenarios");
  await expect(page.getByTestId("interest-impact")).toHaveText("$10.64M");
  await page
    .locator("summary")
    .filter({ hasText: "Optional EBITDA assumption" })
    .click();
  await page
    .getByLabel("Hypothetical baseline EBITDA (USD)", { exact: true })
    .fill("4000000000");
  await page.getByLabel("EBITDA decline (%)", { exact: true }).fill("25");
  await expect(
    page.getByText("EBITDA (user assumption)", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("$3.00B", { exact: true })).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export scenario JSON" }).click();
  const download = await downloadPromise;
  const exported = JSON.parse(await readFile((await download.path())!, "utf8"));
  expect(exported.hypothetical).toBe(true);
  expect(exported.baseline_ebitda).toBe("4000000000");
  expect(Number(exported.ebitda_delta)).toBe(-1000000000);
  const financials = await (
    await page.request.get("/api/companies/1/financials")
  ).json();
  expect(
    financials.metrics.find((m: { key: string }) => m.key === "ebitda").value,
  ).toBe(null);
  await page.getByLabel("New annual rate (%)", { exact: true }).fill("110");
  await expect(
    page.getByRole("alert").filter({ hasText: "between 0% and 100%" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Export scenario JSON" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Reset assumptions" }).click();
  await expect(page.getByTestId("interest-impact")).toHaveText("$10.64M");
  await navigateResearch(page, "Research brief");
  await expect(
    page.getByRole("heading", { name: "Source appendix" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Print / save PDF" }),
  ).toBeVisible();
  await page.emulateMedia({ media: "print" });
  await expect(page.locator(".research-brief")).toBeVisible();
  await expect(page.locator(".sidebar")).not.toBeVisible();
  await page.emulateMedia({ media: "screen" });
  if (
    !(await page
      .getByRole("button", { name: "Research universe", exact: true })
      .isVisible())
  ) {
    await page.getByRole("button", { name: "Toggle navigation" }).click();
  }
  await page
    .getByRole("button", { name: "Research universe", exact: true })
    .click();
  await page.getByLabel("Search company or ticker").fill("uncovered issuer");
  await expect(page.getByText(/No covered issuers match/)).toBeVisible();
  await page.getByLabel("Search company or ticker").fill("NUE");
  await expect(page.getByRole("button", { name: "Open issuer" })).toBeVisible();
});

test("overview worksheet opens the full lab with the same exact assumptions", async ({
  page,
}) => {
  await page.goto("/?company=NUE#overview");
  await expect(page.getByTestId("interest-impact")).toHaveText("$10.64M");
  await page
    .getByLabel("Previous annual rate (%)", { exact: true })
    .fill("4.125");
  await page.getByLabel("New annual rate (%)", { exact: true }).fill("7.375");
  await expect(page.getByTestId("interest-impact")).toHaveText("$17.29M");
  await page
    .getByRole("button", { name: "Open single-maturity model", exact: true })
    .click();
  await expect(
    page.getByLabel("Previous annual rate (%)", { exact: true }),
  ).toHaveValue("4.125");
  await expect(
    page.getByLabel("New annual rate (%)", { exact: true }),
  ).toHaveValue("7.375");
  await expect(
    page.getByLabel("Analytical EBIT proxy decline", { exact: true }),
  ).toHaveValue("0");
  await expect(page.getByTestId("interest-impact")).toHaveText("$17.29M");
});

test("approved companies switch to their own real data and the qualified comparison", async ({
  page,
}, testInfo) => {
  await page.goto("/?company=NUE#overview");
  const companies = await (await page.request.get("/api/companies")).json();
  const stld = companies.find(
    (company: { ticker: string }) => company.ticker === "STLD",
  );
  const rs = companies.find(
    (company: { ticker: string }) => company.ticker === "RS",
  );
  expect(stld).toBeTruthy();
  expect(rs).toBeTruthy();
  await page
    .getByLabel("Selected company", { exact: true })
    .selectOption(String(stld.id));
  await expect(
    page.getByRole("heading", { name: "Steel Dynamics Inc", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Inspect Reported financial debt evidence",
    }),
  ).toContainText("$4.21B");
  await expect(page.getByTestId("interest-impact")).toHaveText("$7.02M");
  await page
    .getByRole("button", { name: "Inspect Reported financial debt evidence" })
    .click();
  await expect(page.getByRole("dialog")).toContainText("0001104659-26-021395");
  await page.getByRole("button", { name: "Close evidence" }).click();
  await page
    .getByLabel("Selected company", { exact: true })
    .selectOption(String(rs.id));
  await expect(
    page.getByRole("heading", { name: "Reliance, Inc.", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Inspect Reported financial debt evidence",
    }),
  ).toContainText("$1.42B");
  await expect(page.getByTestId("interest-impact")).toHaveText("$8.00M");
  await expect(page).toHaveURL(/company=RS/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Reliance, Inc.", exact: true }),
  ).toBeVisible();
  const comparisonNav = page.getByRole("button", {
    name: "Peer comparison",
    exact: true,
  });
  if (!(await comparisonNav.isVisible()))
    await page.getByRole("button", { name: "Toggle navigation" }).click();
  await comparisonNav.click();
  if (testInfo.project.name === "mobile")
    await expect(page.locator(".workbench-sidebar")).toBeHidden();
  await expect(
    page.getByRole("heading", { name: "Peer comparison", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open NUE", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open STLD", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open RS", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "$6.86B", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("comparison.png"),
    fullPage: testInfo.project.name !== "webkit",
  });
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export comparison JSON" }).click();
  const file = await downloaded;
  const result = JSON.parse(await readFile((await file.path())!, "utf8"));
  expect(result.enabled).toBe(true);
  expect(result.rows).toHaveLength(5);
  await page.getByRole("button", { name: "Open STLD", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Steel Dynamics Inc", exact: true }),
  ).toBeVisible();
});

for (const issuer of [
  { ticker: "LECO", name: "Lincoln Electric Holdings Inc", debt: "$1.29B", accession: "0000059527-26-000006", ending: "$2.95B", other: "0", final: 2954405520 },
  { ticker: "ITW", name: "Illinois Tool Works Inc", debt: "$8.97B", accession: "0000049826-26-000008", ending: "$12.82B", other: "1287", final: 12824500000 },
]) {
  test(`${issuer.ticker} real evidence, stress export and annual cash uses remain issuer-specific`, async ({ page }, testInfo) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(`/?company=${issuer.ticker}#overview`);
    await expect(page.getByRole("heading", { name: issuer.name, exact: true })).toBeVisible();
    const debt = page.getByRole("button", { name: "Inspect Reported financial debt evidence", exact: true });
    await expect(debt).toContainText(issuer.debt);
    await debt.click();
    await expect(page.getByRole("dialog")).toContainText(issuer.accession);
    await page.getByRole("button", { name: "Close evidence", exact: true }).click();
    await navigateResearch(page, "Data quality & sources");
    const review = page.getByRole("region", { name: "Financial review", exact: true });
    await expect(review.getByTestId("debt-bridge-difference")).toContainText("$0");
    if (issuer.ticker === "LECO") await expect(review).toContainText("$4,000");
    await navigateResearch(page, "Scenario analysis");
    await expect(page.getByTestId("stress-ending-cash")).toHaveText(issuer.ending);
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export stress cases JSON", exact: true }).click();
    const exported = JSON.parse(await readFile((await (await download).path())!, "utf8"));
    expect(Number(exported.cases[0].projection.closing_cash_before_uncommitted_funding)).toBe(issuer.final);
    await page.getByRole("button", { name: "Explore Base year by year", exact: true }).click();
    await expect(page.getByTestId("liquidity-ending-cash")).toHaveText(issuer.ending);
    await expect(page.getByLabel("2026 other cash uses (USDm)", { exact: true })).toHaveValue(issuer.other);
    await page.reload();
    await expect(page.getByTestId("liquidity-ending-cash")).toHaveText(issuer.ending);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`${issuer.ticker.toLowerCase()}-annual.png`), fullPage: testInfo.project.name !== "webkit" });
    await navigateResearch(page, "Peer comparison");
    await expect(page.getByRole("button", { name: "Open LECO", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open ITW", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Open NUE", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Nucor Corp", exact: true })).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test("dated Nucor case explains a residual reserve gap, exports evidence and transfers its actual cash uses", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/?company=NUE#case-study");
  await expect(
    page.getByRole("heading", {
      name: "Nucor: profitable does not mean cash is free",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByTestId("case-response-cash")).toHaveText("$362.74M");
  await expect(page.getByTestId("case-residual-gap")).toHaveText("$137.27M");
  await expect(page.getByTestId("case-annual-improvement")).toHaveText(
    "$68.63M",
  );
  await page
    .getByText(
      "Source appendix: historical amounts, management estimate and facility capacity",
      { exact: true },
    )
    .click();
  await expect(
    page.getByRole("region", {
      name: "Case-study source appendix",
      exact: true,
    }),
  ).toContainText("Management estimate · source-extracted");
  await expect(
    page.getByRole("region", {
      name: "Case-study source appendix",
      exact: true,
    }),
  ).toContainText("2026-12-31");
  await page
    .getByText(
      "Source appendix: historical amounts, management estimate and facility capacity",
      { exact: true },
    )
    .click();
  const jsonDownload = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export case JSON", exact: true })
    .click();
  const jsonFile = await jsonDownload;
  const study = JSON.parse(await readFile((await jsonFile.path())!, "utf8"));
  expect(study.human_review_completed).toBe(false);
  expect(study.report.cases).toHaveLength(4);
  expect(Number(study.report.remaining_cash_floor_gap)).toBe(137265000);
  expect(study.evidence).toHaveLength(8);
  const memoDownload = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download case memo", exact: true })
    .click();
  const memoFile = await memoDownload;
  expect(await readFile((await memoFile.path())!, "utf8")).toContain(
    "EACH of 2026 and 2027",
  );
  await page
    .getByRole("button", { name: "Review Pause modeled buybacks", exact: true })
    .click();
  await expect(page.getByTestId("case-rationale")).toContainText(
    "Change only share repurchases to zero",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.screenshot({
    path: testInfo.outputPath("case-study.png"),
    fullPage: testInfo.project.name !== "webkit",
  });
  await page
    .getByRole("button", {
      name: "Open selected case in annual model",
      exact: true,
    })
    .click();
  await expect(page.getByTestId("liquidity-ending-cash")).toHaveText(
    "$362.74M",
  );
  await expect(page.getByTestId("liquidity-peak-shortfall")).toHaveText(
    "$137.27M",
  );
  await expect(
    page.getByLabel("Projection horizon", { exact: true }),
  ).toHaveValue("2");
  await expect(
    page.getByLabel("2026 other cash uses (USDm)", { exact: true }),
  ).toHaveValue("915");
  await expect(
    page.getByLabel("2027 other cash uses (USDm)", { exact: true }),
  ).toHaveValue("793");
  const companies = await (await page.request.get("/api/companies")).json();
  const stld = companies.find((c: { ticker: string }) => c.ticker === "STLD");
  await page
    .getByLabel("Selected company", { exact: true })
    .selectOption(String(stld.id));
  await navigateResearch(page, "Case study");
  await expect(
    page.getByRole("heading", { name: "A focused Nucor case", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Open Nucor case study", exact: true })
    .click();
  await expect(page.getByTestId("case-residual-gap")).toHaveText("$137.27M");
  await expect(
    page.getByLabel("Selected company", { exact: true }),
  ).toHaveValue(String(study.report.cases[0].inputs.company_id));
  expect(errors).toEqual([]);
});

test("project introduction explains the case, serves real documents and opens the source-bound workspace", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: /Profit covers interest\.\s*Does cash cover the plan\?/,
    }),
  ).toBeVisible();
  await expect(page.getByTestId("project-case-gap")).toHaveText("$137.27M");
  await expect(
    page.getByRole("combobox", { name: "Selected company", exact: true }),
  ).toHaveCount(0);
  for (const name of [
    /Project brief · PDF/,
    /Nucor case · PDF/,
    /Download presentation pack/,
  ]) {
    const download = page.waitForEvent("download");
    await page.getByRole("link", { name }).click();
    const file = await download;
    const bytes = await readFile((await file.path())!);
    if (file.suggestedFilename().endsWith(".pdf"))
      expect(bytes.subarray(0, 4).toString()).toBe("%PDF");
    else expect(bytes.subarray(0, 2).toString()).toBe("PK");
  }
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.screenshot({
    path: testInfo.outputPath("project.png"),
    fullPage: testInfo.project.name !== "webkit",
  });
  await page
    .getByRole("button", { name: "Explore the Nucor case", exact: true })
    .click();
  await expect(page.getByTestId("case-residual-gap")).toHaveText("$137.27M");
  const pdf = page.waitForEvent("download");
  await page
    .getByRole("link", { name: "Download case PDF", exact: true })
    .click();
  expect(
    (await readFile((await (await pdf).path())!)).subarray(0, 4).toString(),
  ).toBe("%PDF");
  await page.goBack();
  await expect(page.getByTestId("project-case-gap")).toHaveText("$137.27M");
  await page.goForward();
  await expect(page.getByTestId("case-residual-gap")).toHaveText("$137.27M");
  expect(errors).toEqual([]);
});

test("browser history restores the company and research section without mixing issuer drafts", async ({
  page,
}) => {
  await page.goto("/?company=NUE#overview");
  await expect(page.getByTestId("near-term-principal")).toHaveText("$598.00M");
  await navigateResearch(page, "Debt maturities");
  const companies = await (await page.request.get("/api/companies")).json();
  const stld = companies.find((c: { ticker: string }) => c.ticker === "STLD");
  await page
    .getByLabel("Selected company", { exact: true })
    .selectOption(String(stld.id));
  await expect(page).toHaveURL(/company=STLD#maturities$/);
  await expect(
    page.getByRole("heading", { name: "Steel Dynamics Inc", exact: true }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByLabel("Selected company", { exact: true }),
  ).toHaveValue(
    String(companies.find((c: { ticker: string }) => c.ticker === "NUE").id),
  );
  await expect(page).toHaveURL(/company=NUE#maturities$/);
  await page.goBack();
  await expect(page.getByTestId("near-term-principal")).toHaveText("$598.00M");
  await page.goForward();
  await expect(page).toHaveURL(/#maturities$/);
  await page.goForward();
  await expect(
    page.getByLabel("Selected company", { exact: true }),
  ).toHaveValue(String(stld.id));
  await expect(
    page.getByRole("heading", { name: "Steel Dynamics Inc", exact: true }),
  ).toBeVisible();
});
