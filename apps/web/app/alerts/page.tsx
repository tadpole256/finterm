import { AlertsWorkspaceScreen } from "@/components/AlertsWorkspaceScreen";
import { getAlertEvents, getLatestBrief, getManagedAlerts, getNotifications } from "@/lib/api";
import { mockDailyBriefDetail } from "@/lib/mock";

export default async function AlertsPage() {
  const [alerts, events, notifications, brief] = await Promise.all([
    getManagedAlerts("all"),
    getAlertEvents(),
    getNotifications("all"),
    getLatestBrief().catch(() => mockDailyBriefDetail)
  ]);

  return (
    <AlertsWorkspaceScreen
      initialAlerts={alerts}
      initialEvents={events}
      initialNotifications={notifications}
      initialBrief={brief}
    />
  );
}
