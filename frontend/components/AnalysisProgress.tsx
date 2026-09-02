"use client";

const STEPS = [
  "Analyzing garment",
  "Generating try-on",
  "Comparing wardrobe",
  "Calculating recommendation",
];

type Props = {
  active: boolean;
  stepIndex: number;
};

export function AnalysisProgress({ active, stepIndex }: Props) {
  if (!active) return null;
  return (
    <div
      className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-4"
      role="status"
      aria-live="polite"
      data-testid="analysis-progress"
    >
      <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">Working</p>
      <ol className="mt-3 space-y-2">
        {STEPS.map((step, index) => {
          const done = index < stepIndex;
          const current = index === stepIndex;
          return (
            <li key={step} className="flex items-center gap-3 text-sm">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full border text-[10px] ${
                  done
                    ? "border-[#0F7B4B] bg-[#0F7B4B] text-white"
                    : current
                      ? "border-[#111111] text-[#111111]"
                      : "border-[#EAEAEA] text-[#C8C8C8]"
                }`}
              >
                {done ? "✓" : index + 1}
              </span>
              <span className={current ? "text-[#111111]" : "text-[#5C5C5C]"}>{step}</span>
              {current ? (
                <span className="ml-auto h-1.5 w-16 overflow-hidden rounded-full bg-[#EAEAEA]">
                  <span className="block h-full w-1/2 animate-pulse bg-[#111111]" />
                </span>
              ) : null}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
