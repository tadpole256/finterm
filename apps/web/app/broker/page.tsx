import { BrokerWorkspaceScreen } from "@/components/BrokerWorkspaceScreen";
import { getBrokerAccounts, getBrokerReconciliation } from "@/lib/api";

export default async function BrokerPage() {
  const [accounts, reconciliation] = await Promise.all([
    getBrokerAccounts(),
    getBrokerReconciliation()
  ]);

  return (
    <BrokerWorkspaceScreen
      initialAccounts={accounts}
      initialReconciliation={reconciliation}
    />
  );
}
