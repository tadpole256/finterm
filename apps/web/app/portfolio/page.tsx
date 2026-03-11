import { PortfolioScreen } from "@/components/PortfolioScreen";
import { getPortfolioOverview, getPortfolioRisk } from "@/lib/api";

export default async function PortfolioPage() {
  const [overview, risk] = await Promise.all([getPortfolioOverview(), getPortfolioRisk()]);
  return <PortfolioScreen initialOverview={overview} initialRisk={risk} />;
}
