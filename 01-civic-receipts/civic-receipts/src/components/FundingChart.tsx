"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { IndustryFunding } from "@/lib/types";
import { formatMoney } from "@/lib/format";

interface FundingChartProps {
  industries: IndustryFunding[];
  maxAmount?: number;
  labelWidth?: number;
}

const COLORS = [
  "#2563eb",
  "#7c3aed",
  "#db2777",
  "#ea580c",
  "#ca8a04",
  "#16a34a",
];

export default function FundingChart({
  industries,
  maxAmount,
  labelWidth = 160,
}: FundingChartProps) {
  const data = industries.map((ind, i) => ({
    name: ind.name,
    amount: ind.amount,
    fill: COLORS[i % COLORS.length],
  }));

  const domain = maxAmount ? [0, maxAmount] : undefined;

  return (
    <ResponsiveContainer width="100%" height={industries.length * 44 + 20}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 60 }}>
        <XAxis type="number" hide domain={domain} />
        <YAxis
          type="category"
          dataKey="name"
          width={labelWidth}
          tick={{ fontSize: 11, width: labelWidth - 8 }}
          axisLine={false}
          tickLine={false}
          interval={0}
        />
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        <Bar
          dataKey="amount"
          radius={[0, 4, 4, 0]}
          barSize={20}
          label={(props: any) => {
            const x = Number(props.x ?? 0);
            const y = Number(props.y ?? 0);
            const w = Number(props.width ?? 0);
            const v = Number(props.value ?? 0);
            return (
              <text x={x + w + 6} y={y + 14} fontSize={11} fill="#71717a">
                {formatMoney(v)}
              </text>
            );
          }}
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
