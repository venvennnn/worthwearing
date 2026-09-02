import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white px-6 py-16 md:px-16">
      <p className="text-[11px] uppercase tracking-[0.22em] text-[#5C5C5C]">
        WorthWearing Intelligence
      </p>
      <h1 className="serif mt-4 max-w-3xl text-5xl leading-tight text-[#111111] md:text-6xl">
        Try it on. Know if it’s worth owning.
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-[#5C5C5C]">
        Before you buy it, see if you’ll wear it. WorthWearing combines Perfect Corp’s
        virtual try-on technology with wardrobe intelligence to determine whether a new
        garment complements what you already own—or is likely to become your next return.
      </p>
      <p className="serif mt-8 max-w-2xl text-2xl text-[#111111]">
        Virtual try-on shows whether it looks good. WorthWearing shows whether it deserves
        a place in your wardrobe.
      </p>
      <Link
        href="/demo"
        className="mt-10 inline-flex rounded-full bg-[#111111] px-6 py-3 text-sm text-white"
      >
        Open the product-page demo
      </Link>
      <p className="mt-16 max-w-xl text-sm text-[#5C5C5C]">
        Decision-support prototype for the Perfect Corp sponsor challenge. Scores are
        deterministic wardrobe rules, not a calibrated return predictor. We don’t help
        shoppers buy more. We help them keep what they buy.
      </p>
    </main>
  );
}
