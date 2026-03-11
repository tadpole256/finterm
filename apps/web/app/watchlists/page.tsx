import { WatchlistsScreen } from "@/components/WatchlistsScreen";
import { getWatchlistLayout, getWatchlists } from "@/lib/api";

const USER_ID = "00000000-0000-0000-0000-000000000001";

export default async function WatchlistsPage() {
  const [watchlists, layout] = await Promise.all([getWatchlists(), getWatchlistLayout(USER_ID)]);

  return <WatchlistsScreen initialWatchlists={watchlists} initialLayout={layout} />;
}
