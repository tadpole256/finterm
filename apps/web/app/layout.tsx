import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Finterm",
  description: "Personal market intelligence terminal"
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/screener", label: "Screener" },
  { href: "/intel", label: "Intel" },
  { href: "/watchlists", label: "Watchlists" },
  { href: "/alerts", label: "Alerts" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/broker", label: "Broker" },
  { href: "/journal", label: "Journal" },
  { href: "/research", label: "Research" },
  { href: "/security/AAPL", label: "Security" }
] as const;

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-[radial-gradient(circle_at_top,#1a2438_0,#070b14_50%)]">
          <header className="border-b border-border bg-base/80 backdrop-blur">
            <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-textSecondary">
                  Personal Terminal
                </p>
                <h1 className="text-xl font-semibold text-textPrimary">Finterm</h1>
              </div>
              <nav className="flex gap-4">
                {navItems.map((item) => (
                  <a
                    key={item.href}
                    href={item.href}
                    className="rounded-md px-3 py-2 text-sm text-textSecondary transition hover:bg-panelMuted hover:text-textPrimary"
                  >
                    {item.label}
                  </a>
                ))}
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-[1600px] px-6 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
