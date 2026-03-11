import { PortfolioScreen } from "@/components/PortfolioScreen";
import { getPortfolioOverview } from "@/lib/api";

export default async function PortfolioPage() {
  const overview = await getPortfolioOverview();
  return <PortfolioScreen initialOverview={overview} />;
}
