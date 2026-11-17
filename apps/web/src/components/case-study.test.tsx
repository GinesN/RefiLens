import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import CaseStudyPanel from "./case-study";
import { api, Dataset } from "@/lib/api";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  api: vi.fn(),
}));
const data = {
  company: { id: 2, ticker: "STLD" },
  financials: { filing: { id: 2 } },
} as unknown as Dataset;
beforeEach(() => vi.resetAllMocks());

it("does not attach Nucor research to an unsupported issuer", async () => {
  vi.mocked(api).mockResolvedValue({
    available: false,
    filing: { id: 2 },
    report: null,
    reason: "Nucor FY2025 only.",
  });
  const onOpenNucor = vi.fn();
  render(
    <CaseStudyPanel
      data={data}
      onOpenAnnual={vi.fn()}
      onSources={vi.fn()}
      onOpenNucor={onOpenNucor}
    />,
  );
  expect(await screen.findByText("Nucor FY2025 only.")).toBeVisible();
  expect(
    screen.queryByRole("button", { name: "Export case JSON" }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: /Open Nucor case study/ }),
  );
  expect(onOpenNucor).toHaveBeenCalledOnce();
});

it("refuses a different filing instead of rendering stale case results", async () => {
  vi.mocked(api).mockResolvedValue({
    available: true,
    filing: { id: 999 },
    report: {},
  });
  render(
    <CaseStudyPanel
      data={data}
      onOpenAnnual={vi.fn()}
      onSources={vi.fn()}
      onOpenNucor={vi.fn()}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "The case source changed",
  );
  expect(
    screen.queryByRole("button", { name: "Download case memo" }),
  ).not.toBeInTheDocument();
});
