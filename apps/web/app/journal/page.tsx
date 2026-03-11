import { JournalScreen } from "@/components/JournalScreen";
import { getJournalEntries } from "@/lib/api";

export default async function JournalPage() {
  const entries = await getJournalEntries({ limit: 120 });
  return <JournalScreen initialEntries={entries} />;
}
