import { ScreenerScreen } from "@/components/ScreenerScreen";
import { getSavedScreens, getWatchlists, runScreener } from "@/lib/api";

export default async function ScreenerPage() {
  const [watchlists, initialResults, savedScreens] = await Promise.all([
    getWatchlists(),
    runScreener({ limit: 150 }),
    getSavedScreens()
  ]);

  return (
    <ScreenerScreen
      initialResults={initialResults}
      initialSavedScreens={savedScreens}
      watchlists={watchlists}
    />
  );
}
