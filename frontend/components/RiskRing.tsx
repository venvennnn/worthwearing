"use client";

type Props = {
  value: number;
  label?: string;
};

export function RiskRing({ value, label = "Return Risk" }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;
  const color = clamped >= 70 ? "#B42318" : clamped >= 40 ? "#B45309" : "#0F7B4B";

  return (
    <div className="flex items-center gap-4" data-testid="risk-ring">
      <svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label={`${label} ${clamped}`}>
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#EAEAEA" strokeWidth="10" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
        />
        <text
          x="70"
          y="68"
          textAnchor="middle"
          className="serif"
          fontSize="28"
          fill="#111111"
        >
          {clamped}
        </text>
        <text x="70" y="88" textAnchor="middle" fontSize="10" fill="#5C5C5C">
          of 100
        </text>
      </svg>
      <div>
        <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">{label}</p>
        <p className="mt-1 max-w-[12rem] text-sm text-[#5C5C5C]">
          Deterministic proxy, not a predicted return rate.
        </p>
      </div>
    </div>
  );
}
