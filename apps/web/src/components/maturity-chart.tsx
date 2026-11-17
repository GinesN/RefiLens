"use client";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Bucket, money } from "@/lib/api";

export default function MaturityChart({
  buckets,
  onSelect,
}: {
  buckets: Bucket[];
  onSelect: (bucket: Bucket) => void;
}) {
  const exact = buckets.filter((b) => b.kind === "EXACT_YEAR");
  const broad = buckets.filter((b) => b.kind !== "EXACT_YEAR");
  if (!buckets.length)
    return (
      <div className="empty-state">
        No maturity disclosure has passed validation.
      </div>
    );
  return (
    <div className="maturity-visual">
      <div
        className="chart-wrap"
        role="img"
        aria-label={`Disclosed annual principal maturities: ${exact.map((b) => `${b.label}: ${money(b.amount, false)}`).join("; ")}. Broad buckets shown separately.`}
      >
        <span className="axis-caption">USD millions · principal</span>
        <ResponsiveContainer width="100%" height={275} minWidth={0}>
          <BarChart
            data={exact.map((b) => ({
              ...b,
              millions: Number(b.amount) / 1e6,
            }))}
            margin={{ top: 30, right: 10, left: -15, bottom: 0 }}
            barCategoryGap="28%"
          >
            <CartesianGrid
              strokeDasharray="2 3"
              vertical={false}
              stroke="var(--chart-grid)"
            />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "var(--chart-axis)", fontSize: 12 }}
              dy={8}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "var(--chart-axis)", fontSize: 11 }}
              tickFormatter={(v) => Number(v).toLocaleString("en-US")}
            />
            <Tooltip
              cursor={{ fill: "#283341" }}
              formatter={(v) => [
                `$${Number(v).toLocaleString("en-US")}M`,
                "Principal",
              ]}
              contentStyle={{
                borderRadius: 0,
                borderColor: "#506174",
                background: "#222b35",
                color: "#e8eef5",
                fontSize: 12,
              }}
            />
            <Bar
              dataKey="millions"
              maxBarSize={48}
              fill="var(--chart-bar)"
              radius={[0, 0, 0, 0]}
              isAnimationActive={false}
            >
              <LabelList
                dataKey="millions"
                position="top"
                formatter={(v) => Number(v).toLocaleString("en-US")}
                fill="var(--chart-label)"
                fontSize={12}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="broad-buckets">
        <span className="eyebrow">Broad disclosure</span>
        {broad.map((b) => (
          <button
            key={b.id}
            className="broad-bucket"
            onClick={() => onSelect(b)}
          >
            <span className="hatch-mark" />
            <strong>{money(b.amount)}</strong>
            <span>{b.label}</span>
          </button>
        ))}
        <p>
          Unallocated across individual years. Shown separately to preserve the
          source.
        </p>
      </div>
    </div>
  );
}
