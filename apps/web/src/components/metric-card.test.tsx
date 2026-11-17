import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import MetricCard from "./metric-card";
import { Metric } from "@/lib/api";

it("opens evidence for an unavailable metric without inventing a value", () => {
  const metric: Metric = {
    key: "ebitda",
    label: "EBITDA",
    value: null,
    unit: "USD",
    basis: "Not available",
    formula: "No reviewed reconciliation",
    fact_ids: [],
    status: "UNAVAILABLE",
    note: "",
  };
  const onEvidence = vi.fn();
  render(<MetricCard metric={metric} onEvidence={onEvidence} />);
  expect(screen.getAllByText("Not available")).toHaveLength(2);
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect EBITDA evidence" }),
  );
  expect(onEvidence).toHaveBeenCalledWith(metric);
});
