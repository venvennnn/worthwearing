"use client";

import type { AnalysisResult } from "@/lib/types";

type Props = {
  result: AnalysisResult;
  open: boolean;
  onToggle: () => void;
};

export function MethodologyDrawer({ result, open, onToggle }: Props) {
  return (
    <div className="rounded-2xl border border-[#EAEAEA] bg-white">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        data-testid="why-this-result"
      >
        <span className="text-sm text-[#111111]">Why this result?</span>
        <span className="text-xs text-[#5C5C5C]">{open ? "Hide" : "Inspect"}</span>
      </button>
      {open ? (
        <div className="border-t border-[#EAEAEA] px-4 py-4 text-sm text-[#5C5C5C]" data-testid="methodology-panel">
          <p className="text-[#111111]">{result.summary}</p>
          <ol className="mt-3 list-decimal space-y-2 pl-4">
            {result.methodology_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ol>
          <p className="mt-4 text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
            Rejected combinations
          </p>
          <ul className="mt-2 space-y-1.5">
            {result.rejected_combinations.slice(0, 8).map((row, index) => (
              <li key={`${row.rule}-${index}`}>
                <span className="text-[#111111]">{row.rule}</span>: {row.reason}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
