import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { api, Company } from "@/lib/api";
import ProjectOverview from "./project-overview";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  api: vi.fn(),
}));
const companies = [
  { id: 1, ticker: "NUE", filing: { source_url: "https://www.sec.gov/" } },
] as Company[];
beforeEach(() => vi.resetAllMocks());

it("leaves the featured outcome unavailable when the source-backed case request fails", async () => {
  vi.mocked(api).mockRejectedValue(new Error("The source snapshot changed."));
  render(<ProjectOverview companies={companies} onExplore={vi.fn()} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "The source snapshot changed",
  );
  expect(screen.queryByTestId("project-case-gap")).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Project brief/ })).toHaveAttribute(
    "href",
    "/research/RefiLens_Project_Brief.pdf",
  );
});

it("routes the case and evidence choices without inventing financial outputs", async () => {
  vi.mocked(api).mockResolvedValue({
    available: true,
    report: {
      historical_coverage_proxy: "15.452941176471",
      historical_free_cash_flow: "-188000000",
      cash_preserved_by_pausing_buybacks: "1400000000",
      minimum_cash_assumption: "500000000",
      remaining_cash_floor_gap: "137265000",
      cases: [
        {
          id: "pause_buybacks",
          projection: { closing_cash_before_uncommitted_funding: "362735000" },
        },
      ],
    },
  });
  const onExplore = vi.fn();
  render(<ProjectOverview companies={companies} onExplore={onExplore} />);
  expect(await screen.findByTestId("project-case-gap")).toHaveTextContent(
    "$137.27M",
  );
  fireEvent.click(
    screen.getByRole("button", { name: /Explore the Nucor case/ }),
  );
  expect(onExplore).toHaveBeenLastCalledWith("case-study");
  fireEvent.click(
    screen.getByRole("button", { name: /Inspect source definitions/ }),
  );
  expect(onExplore).toHaveBeenLastCalledWith("sources");
});
