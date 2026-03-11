"use client";

import { useEffect } from "react";

import { StateNotice } from "@/components/StateNotice";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="space-y-4">
      <header>
        <p className="text-xs uppercase tracking-[0.16em] text-textSecondary">Workspace Error</p>
        <h2 className="text-2xl font-semibold text-textPrimary">Unable to render this view</h2>
      </header>

      <StateNotice
        tone="error"
        title="A runtime error occurred."
        detail="You can retry below. If this persists, inspect API availability and recent logs."
      />

      <button
        type="button"
        onClick={reset}
        className="rounded-md border border-border px-3 py-2 text-sm text-textSecondary hover:text-textPrimary"
      >
        Retry
      </button>
    </div>
  );
}
