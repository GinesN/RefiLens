import type { Metadata } from "next";
import "./globals.css";
import "./workbench.css";
import "./research.css";
import "./presentation.css";

export const metadata: Metadata = {
  title: "RefiLens | Corporate Debt Research",
  description:
    "Evidence-backed corporate debt and refinancing sensitivity research. Historical filing data, transparent assumptions.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
