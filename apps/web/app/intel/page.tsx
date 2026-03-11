import { IntelSyncScreen } from "@/components/IntelSyncScreen";
import { getFilings, getMacroEvents, getMacroSeries } from "@/lib/api";

export default async function IntelPage() {
  const [filings, series, events] = await Promise.all([
    getFilings(),
    getMacroSeries(),
    getMacroEvents(30)
  ]);

  return <IntelSyncScreen initialFilings={filings} initialSeries={series} initialEvents={events} />;
}
