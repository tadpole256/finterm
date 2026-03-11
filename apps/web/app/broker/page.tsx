import { BrokerWorkspaceScreen } from "@/components/BrokerWorkspaceScreen";
import {
  getBrokerAccounts,
  getBrokerCapabilities,
  getBrokerOrderEvents,
  getBrokerReconciliation,
  getJournalEntries,
  getReconciliationExceptions
} from "@/lib/api";

export default async function BrokerPage() {
  const [
    capabilities,
    accounts,
    reconciliation,
    exceptions,
    orderEvents,
    journalEntries
  ] = await Promise.all([
    getBrokerCapabilities(),
    getBrokerAccounts(),
    getBrokerReconciliation(),
    getReconciliationExceptions("open"),
    getBrokerOrderEvents({ limit: 20 }),
    getJournalEntries({ limit: 20 })
  ]);

  return (
    <BrokerWorkspaceScreen
      initialCapabilities={capabilities}
      initialAccounts={accounts}
      initialReconciliation={reconciliation}
      initialExceptions={exceptions}
      initialOrderEvents={orderEvents}
      initialJournalEntries={journalEntries}
    />
  );
}
