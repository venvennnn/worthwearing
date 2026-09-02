"use client";

import { useEffect, useState } from "react";
import { DemoExperience } from "@/components/DemoExperience";
import { getDemo } from "@/lib/api";
import type { DemoPayload } from "@/lib/types";

export default function DemoPage() {
  const [demo, setDemo] = useState<DemoPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDemo()
      .then(setDemo)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Could not load demo data.")
      );
  }, []);

  if (error) {
    return (
      <main className="min-h-screen bg-white px-6 py-16">
        <h1 className="serif text-3xl">WorthWearing</h1>
        <p className="mt-4 text-sm text-[#B42318]" role="alert">
          {error} Start the FastAPI backend on port 8000 and reload.
        </p>
      </main>
    );
  }

  if (!demo) {
    return (
      <main className="min-h-screen bg-white px-6 py-16">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[3fr_2fr]">
          <div className="h-[640px] animate-pulse rounded-3xl bg-[#FAFAFA]" />
          <div className="h-[640px] animate-pulse rounded-3xl bg-[#FAFAFA]" />
        </div>
      </main>
    );
  }

  return <DemoExperience demo={demo} />;
}
