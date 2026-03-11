import { formatCurrency, formatPercent } from "@/lib/format";
import { StateNotice } from "@/components/StateNotice";
import type { MarketQuote } from "@/lib/types";

interface MoversPanelProps {
  gainers: MarketQuote[];
  losers: MarketQuote[];
}

export function MoversPanel({ gainers, losers }: MoversPanelProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div>
        <p className="mb-2 text-xs uppercase tracking-wider text-textSecondary">Top Gainers</p>
        {gainers.length === 0 ? (
          <StateNotice title="No gainers in current data window." />
        ) : (
          <ul className="space-y-2">
            {gainers.map((item) => (
              <li key={item.symbol} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-textPrimary">{item.symbol}</p>
                  <p className="text-xs text-textSecondary">{formatCurrency(item.price)}</p>
                </div>
                <span className="text-sm text-success">{formatPercent(item.change_percent)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wider text-textSecondary">Top Losers</p>
        {losers.length === 0 ? (
          <StateNotice title="No losers in current data window." />
        ) : (
          <ul className="space-y-2">
            {losers.map((item) => (
              <li key={item.symbol} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-textPrimary">{item.symbol}</p>
                  <p className="text-xs text-textSecondary">{formatCurrency(item.price)}</p>
                </div>
                <span className="text-sm text-danger">{formatPercent(item.change_percent)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
