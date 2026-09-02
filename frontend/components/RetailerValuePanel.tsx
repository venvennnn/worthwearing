"use client";

type Props = {
  closeLine: string;
};

export function RetailerValuePanel({ closeLine }: Props) {
  return (
    <aside className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-4" data-testid="retailer-value">
      <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
        WorthWearing Intelligence
      </p>
      <p className="serif mt-2 text-xl text-[#111111]">Retailer value</p>
      <p className="mt-2 text-sm text-[#5C5C5C]">
        A future retailer pilot could measure recommendation acceptance, purchases, keep rate,
        and returns. This prototype does not display invented improvements.
      </p>
      <ul className="mt-3 space-y-1 text-sm text-[#111111]">
        <li>Recommendation acceptance — to be measured in a pilot</li>
        <li>Keep rate / returns — to be calibrated with retailer outcomes</li>
        <li>Usage-priced API or product-page SDK</li>
      </ul>
      <p className="serif mt-4 text-base text-[#111111]">{closeLine}</p>
    </aside>
  );
}
