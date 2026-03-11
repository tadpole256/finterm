import { SecurityWorkspaceScreen } from "@/components/SecurityWorkspaceScreen";
import { getSecurityWorkspace } from "@/lib/api";

interface SecurityPageProps {
  params: {
    symbol: string;
  };
}

export default async function SecurityPage({ params }: SecurityPageProps) {
  const security = await getSecurityWorkspace(params.symbol.toUpperCase());

  return <SecurityWorkspaceScreen data={security} />;
}
