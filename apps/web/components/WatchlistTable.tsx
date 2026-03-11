import Link from "next/link";

import { formatCurrency, formatPercent } from "@/lib/format";
import { StateNotice } from "@/components/StateNotice";
import type { Watchlist } from "@/lib/types";

interface WatchlistTableProps {
  watchlists: Watchlist[];
}

export function WatchlistTable({ watchlists }: WatchlistTableProps) {
  if (watchlists.length === 0) {
    return (
      <StateNotice
        title="No watchlists configured yet."
        detail="Create watchlists to track symbols and surface them on the dashboard."
      />
    );
  }

  return (
    <div className="space-y-4">
      {watchlists.map((watchlist) => (
        <div key={watchlist.id}>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-medium text-textPrimary">{watchlist.name}</h3>
            <span className="text-xs text-textSecondary">{watchlist.items.length} symbols</span>
          </div>
          <div className="overflow-auto rounded-lg border border-border">
            <table className="min-w-full text-left">
              <thead className="bg-panelMuted text-xs text-textSecondary">
                <tr>
                  <th className="table-cell">Symbol</th>
                  <th className="table-cell">Price</th>
                  <th className="table-cell">Change</th>
                  <th className="table-cell">Tags</th>
                </tr>
              </thead>
              <tbody>
                {watchlist.items.map((item) => (
                  <tr key={item.id} className="border-t border-border hover:bg-panelMuted/40">
                    <td className="table-cell font-medium text-textPrimary">
                      <Link href={`/security/${item.symbol}`}>{item.symbol}</Link>
                    </td>
                    <td className="table-cell text-textPrimary">{formatCurrency(item.quote.price)}</td>
                    <td
                      className={`table-cell ${
                        item.quote.change_percent >= 0 ? "text-success" : "text-danger"
                      }`}
                    >
                      {formatPercent(item.quote.change_percent)}
                    </td>
                    <td className="table-cell text-textSecondary">{item.tags.join(", ") || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
