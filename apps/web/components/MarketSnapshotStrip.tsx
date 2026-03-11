import { formatCurrency, formatPercent } from "@/lib/format";
import type { MarketQuote } from "@/lib/types";

interface MarketSnapshotStripProps {
  quotes: MarketQuote[];
}

export function MarketSnapshotStrip({ quotes }: MarketSnapshotStripProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {quotes.map((quote) => (
        <article key={quote.symbol} className="panel px-4 py-3">
          <p className="text-xs uppercase tracking-wider text-textSecondary">{quote.symbol}</p>
          <p className="mt-1 text-sm text-textSecondary">{quote.name}</p>
          <p className="mt-2 text-lg font-semibold text-textPrimary">{formatCurrency(quote.price)}</p>
          <p className={`text-sm ${quote.change_percent >= 0 ? "text-success" : "text-danger"}`}>
            {formatPercent(quote.change_percent)} ({formatCurrency(quote.change)})
          </p>
        </article>
      ))}
    </div>
  );
}
