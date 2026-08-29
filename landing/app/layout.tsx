import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sprint Retro — Simple, Private Sprint Retrospectives",
  description:
    "Create a retro, invite your team, collect honest feedback, and get a consolidated report — all on your own infrastructure.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
