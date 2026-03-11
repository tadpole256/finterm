import React, { type ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AlertsWorkspaceScreen } from "@/components/AlertsWorkspaceScreen";
import { DashboardScreen } from "@/components/DashboardScreen";
import { PortfolioScreen } from "@/components/PortfolioScreen";
import { ResearchNotebookScreen } from "@/components/ResearchNotebookScreen";
import { SecurityWorkspaceScreen } from "@/components/SecurityWorkspaceScreen";
import { WatchlistsScreen } from "@/components/WatchlistsScreen";
import {
  mockAlertEvaluationSummary,
  mockAlertEvents,
  mockDailyBriefDetail,
  mockManagedAlerts,
  mockNotifications,
  defaultLayoutState,
  mockDashboard,
  mockNoteSynthesis,
  mockPortfolioOverview,
  mockResearchNotes,
  mockSecurityWorkspace,
  mockTheses
} from "@/lib/mock";

vi.mock("next/link", () => ({
  default: ({ children }: { children: ReactNode }) => <>{children}</>
}));

vi.mock("@/components/SecurityChart", () => ({
  SecurityChart: () => <div data-testid="security-chart" />
}));

vi.mock("@/lib/api", () => ({
  addWatchlistItem: vi.fn(async () => ({ id: "watchlist-1", name: "Core", description: null, items: [] })),
  createManagedAlert: vi.fn(async () => mockManagedAlerts[0]),
  createPortfolioTransaction: vi.fn(async () => mockPortfolioOverview.transactions[0]),
  createWatchlist: vi.fn(async () => ({ id: "watchlist-2", name: "New", description: null, items: [] })),
  createResearchNote: vi.fn(async () => mockResearchNotes[0]),
  createThesis: vi.fn(async () => mockTheses[0]),
  deleteManagedAlert: vi.fn(async () => undefined),
  deletePortfolioTransaction: vi.fn(async () => undefined),
  deleteResearchNote: vi.fn(async () => undefined),
  deleteThesis: vi.fn(async () => undefined),
  evaluateAlerts: vi.fn(async () => mockAlertEvaluationSummary),
  generateBrief: vi.fn(async () => mockDailyBriefDetail),
  getAlertEvents: vi.fn(async () => mockAlertEvents),
  getManagedAlerts: vi.fn(async () => mockManagedAlerts),
  getNoteSynthesis: vi.fn(async () => mockNoteSynthesis),
  getNotifications: vi.fn(async () => mockNotifications),
  getPortfolioOverview: vi.fn(async () => mockPortfolioOverview),
  getResearchNotes: vi.fn(async () => mockResearchNotes),
  getResearchTheses: vi.fn(async () => mockTheses),
  markNotificationRead: vi.fn(async () => undefined),
  removeWatchlistItem: vi.fn(async () => undefined),
  reorderWatchlistItems: vi.fn(async () => ({ id: "watchlist-1", name: "Core", description: null, items: [] })),
  updateResearchNote: vi.fn(async () => mockResearchNotes[0]),
  updateThesis: vi.fn(async () => mockTheses[0]),
  updateWatchlistLayout: vi.fn(async (_, layout) => layout)
}));

describe("screen smoke coverage", () => {
  it("renders dashboard shell", () => {
    render(<DashboardScreen data={mockDashboard} />);

    expect(screen.getByText("Market Dashboard")).toBeInTheDocument();
    expect(screen.getAllByText("Morning Brief").length).toBeGreaterThan(0);
  });

  it("renders watchlists shell", () => {
    render(<WatchlistsScreen initialWatchlists={[]} initialLayout={defaultLayoutState} />);

    expect(screen.getByText("Watchlists")).toBeInTheDocument();
    expect(screen.getByText("Create")).toBeInTheDocument();
  });

  it("renders security workspace shell", () => {
    render(<SecurityWorkspaceScreen data={mockSecurityWorkspace("AAPL")} />);

    expect(screen.getByText(/AAPL/i)).toBeInTheDocument();
    expect(screen.getByTestId("security-chart")).toBeInTheDocument();
  });

  it("renders research notebook shell", () => {
    render(
      <ResearchNotebookScreen
        initialNotes={mockResearchNotes}
        initialTheses={mockTheses}
        initialThemes={["quality"]}
        initialSynthesis={mockNoteSynthesis}
      />
    );

    expect(screen.getByText("Research Notebook")).toBeInTheDocument();
    expect(screen.getByText("AI Note Synthesis")).toBeInTheDocument();
  });

  it("renders portfolio shell", () => {
    render(<PortfolioScreen initialOverview={mockPortfolioOverview} />);

    expect(screen.getByText("Recent Transactions")).toBeInTheDocument();
    expect(screen.getByText("Add Transaction")).toBeInTheDocument();
  });

  it("renders alerts workspace shell", () => {
    render(
      <AlertsWorkspaceScreen
        initialAlerts={mockManagedAlerts}
        initialEvents={mockAlertEvents}
        initialNotifications={mockNotifications}
        initialBrief={mockDailyBriefDetail}
      />
    );

    expect(screen.getByText("Alerts & Briefs")).toBeInTheDocument();
    expect(screen.getByText("Active Alerts")).toBeInTheDocument();
  });
});
