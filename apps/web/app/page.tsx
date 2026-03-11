import { DashboardScreen } from "@/components/DashboardScreen";
import { getDashboard } from "@/lib/api";

export default async function Page() {
  const dashboard = await getDashboard();
  return <DashboardScreen data={dashboard} />;
}
