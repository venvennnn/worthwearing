"use client";

import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FactorComponent } from "@/lib/types";

type Props = {
  factors: FactorComponent[];
};

export function FactorBreakdown({ factors }: Props) {
  const data = factors.map((factor) => ({
    name: factor.label,
    contribution: Number((factor.contribution * 100).toFixed(2)),
    value: factor.value,
    weight: factor.weight,
    explanation: factor.explanation,
  }));

  return (
    <div data-testid="factor-breakdown">
      <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
        Weighted contributions
      </p>
      <div className="mt-2 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
            <XAxis type="number" hide domain={[0, 30]} />
            <YAxis
              type="category"
              dataKey="name"
              width={118}
              tick={{ fill: "#111111", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={false}
              contentStyle={{
                border: "1px solid #EAEAEA",
                background: "#FFFFFF",
                fontSize: 12,
              }}
              formatter={(value, _name, item) => {
                const payload = item?.payload as (typeof data)[number];
                return [`${value} pts · ${payload.explanation}`, "Contribution"];
              }}
            />
            <Bar dataKey="contribution" fill="#111111" radius={[0, 4, 4, 0]} barSize={10} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-2 space-y-1.5 text-xs text-[#5C5C5C]">
        {factors.map((factor) => (
          <li key={factor.key}>
            <span className="text-[#111111]">{factor.label}</span>
            {" · "}
            {(factor.weight * 100).toFixed(0)}% × {factor.value.toFixed(2)} ={" "}
            {(factor.contribution * 100).toFixed(1)} pts
          </li>
        ))}
      </ul>
    </div>
  );
}
